"""Focused tests for concurrent outbox worker claims and lease recovery."""

from pathlib import Path
import sys
import threading
import unittest
from tempfile import TemporaryDirectory

LAB_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(LAB_DIR))

import ledger


class OutboxWorkerLeaseTests(unittest.TestCase):
    def test_competing_workers_deliver_each_message_once(self) -> None:
        with TemporaryDirectory() as directory:
            subject = ledger.OutboxLedger(Path(directory) / "ledger.db")
            for index in range(6):
                subject.apply(f"req-demo-{index:03d}", index + 1)

            delivered = []
            errors = []
            lock = threading.Lock()

            def deliver(message: ledger.OutboxMessage) -> None:
                with lock:
                    delivered.append(message.request_id)

            def run(worker_id: str) -> None:
                try:
                    subject.dispatch(deliver, worker_id=worker_id)
                except BaseException as error:
                    errors.append(error)

            workers = [threading.Thread(target=run, args=(f"worker-{index}",)) for index in range(3)]
            for worker in workers:
                worker.start()
            for worker in workers:
                worker.join(timeout=3)

            self.assertEqual([], errors)
            self.assertEqual(6, len(delivered))
            self.assertEqual(6, len(set(delivered)))
            self.assertEqual([], subject.pending())

    def test_unexpired_lease_hides_message_from_other_worker(self) -> None:
        with TemporaryDirectory() as directory:
            subject = ledger.OutboxLedger(Path(directory) / "ledger.db")
            subject.apply("req-demo-001", 25)

            claimed = subject.claim("worker-a", lease_seconds=30, now=100.0)

            self.assertEqual(ledger.OutboxMessage("req-demo-001", 25), claimed)
            self.assertIsNone(subject.claim("worker-b", lease_seconds=30, now=129.9))

    def test_expired_lease_recovers_abandoned_message(self) -> None:
        with TemporaryDirectory() as directory:
            subject = ledger.OutboxLedger(Path(directory) / "ledger.db")
            subject.apply("req-demo-001", 25)

            first_claim = subject.claim("worker-a", lease_seconds=30, now=100.0)
            recovered = subject.claim("worker-b", lease_seconds=30, now=130.0)

            self.assertEqual(first_claim, recovered)
            self.assertTrue(subject.acknowledge("worker-b", "req-demo-001"))
            self.assertFalse(subject.acknowledge("worker-a", "req-demo-001"))
            self.assertEqual([], subject.pending())

    def test_failed_delivery_releases_lease_but_respects_retry_backoff(self) -> None:
        with TemporaryDirectory() as directory:
            subject = ledger.OutboxLedger(Path(directory) / "ledger.db")
            subject.apply("req-demo-001", 25)

            def fail_delivery(_message) -> None:
                raise RuntimeError("synthetic downstream failure")

            with self.assertRaisesRegex(RuntimeError, "synthetic downstream"):
                subject.dispatch(fail_delivery, worker_id="worker-a", base_backoff_seconds=60.0)

            self.assertIsNone(subject.claim("worker-b"))
            recovered = subject.claim("worker-b", now=10**12)
            self.assertEqual(ledger.OutboxMessage("req-demo-001", 25), recovered)

    def test_non_positive_lease_is_rejected(self) -> None:
        with TemporaryDirectory() as directory:
            subject = ledger.OutboxLedger(Path(directory) / "ledger.db")
            with self.assertRaisesRegex(ValueError, "lease_seconds"):
                subject.claim("worker-a", lease_seconds=0)


if __name__ == "__main__":
    unittest.main()
