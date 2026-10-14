import importlib.util
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import Barrier, Lock, Thread
import unittest


MODULE_PATH = Path(__file__).parents[1] / "ledger.py"
SPEC = importlib.util.spec_from_file_location("transaction_ledger_worker_leases", MODULE_PATH)
ledger = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(ledger)


class OutboxWorkerLeaseTests(unittest.TestCase):
    def test_competing_workers_deliver_each_message_once(self) -> None:
        with TemporaryDirectory() as directory:
            subject = ledger.OutboxLedger(Path(directory) / "ledger.db")
            expected = {f"req-demo-{index:03d}" for index in range(1, 9)}
            for request_id in sorted(expected):
                subject.apply(request_id, 1)

            start = Barrier(3)
            delivered: list[str] = []
            delivered_lock = Lock()

            def deliver(message) -> None:
                with delivered_lock:
                    delivered.append(message.request_id)

            def run(worker_id: str) -> None:
                start.wait()
                subject.dispatch(deliver, worker_id=worker_id)

            workers = [Thread(target=run, args=("worker-a",)), Thread(target=run, args=("worker-b",))]
            for worker in workers:
                worker.start()
            start.wait()
            for worker in workers:
                worker.join(timeout=5)

            self.assertTrue(all(not worker.is_alive() for worker in workers))
            self.assertEqual(expected, set(delivered))
            self.assertEqual(len(expected), len(delivered))
            self.assertEqual([], subject.pending())

    def test_unexpired_lease_hides_message_from_other_worker(self) -> None:
        with TemporaryDirectory() as directory:
            subject = ledger.OutboxLedger(Path(directory) / "ledger.db")
            subject.apply("req-demo-001", 25)

            claimed = subject.claim("worker-a", lease_seconds=10, now=100.0)
            blocked = subject.claim("worker-b", lease_seconds=10, now=109.0)

            self.assertEqual(ledger.OutboxMessage("req-demo-001", 25), claimed)
            self.assertIsNone(blocked)

    def test_expired_lease_recovers_abandoned_message(self) -> None:
        with TemporaryDirectory() as directory:
            subject = ledger.OutboxLedger(Path(directory) / "ledger.db")
            subject.apply("req-demo-001", 25)

            first_claim = subject.claim("worker-a", lease_seconds=10, now=100.0)
            recovered = subject.claim("worker-b", lease_seconds=10, now=111.0)

            self.assertEqual(first_claim, recovered)
            self.assertTrue(subject.acknowledge("worker-b", "req-demo-001"))
            self.assertFalse(subject.acknowledge("worker-a", "req-demo-001"))
            self.assertEqual([], subject.pending())

    def test_failed_delivery_releases_claim_for_immediate_retry(self) -> None:
        with TemporaryDirectory() as directory:
            subject = ledger.OutboxLedger(Path(directory) / "ledger.db")
            subject.apply("req-demo-001", 25)

            def fail_delivery(_message) -> None:
                raise RuntimeError("synthetic downstream failure")

            with self.assertRaisesRegex(RuntimeError, "synthetic downstream"):
                subject.dispatch(fail_delivery, worker_id="worker-a")

            recovered = subject.claim("worker-b", now=100.0)
            self.assertEqual(ledger.OutboxMessage("req-demo-001", 25), recovered)

    def test_non_positive_lease_is_rejected(self) -> None:
        with TemporaryDirectory() as directory:
            subject = ledger.OutboxLedger(Path(directory) / "ledger.db")
            with self.assertRaisesRegex(ValueError, "lease_seconds"):
                subject.claim("worker-a", lease_seconds=0)


if __name__ == "__main__":
    unittest.main()
