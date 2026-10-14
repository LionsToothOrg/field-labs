import importlib.util
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import Barrier, Thread
import unittest


MODULE_PATH = Path(__file__).parents[1] / "ledger.py"
SPEC = importlib.util.spec_from_file_location("transaction_ledger", MODULE_PATH)
ledger = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(ledger)


class TransactionReliabilityTests(unittest.TestCase):
    def test_controlled_race_applies_duplicate_twice(self) -> None:
        subject = ledger.UnsafeLedger()
        after_check = Barrier(2)
        results = []

        def submit() -> None:
            results.append(subject.apply("req-demo-001", 25, after_check.wait))

        workers = [Thread(target=submit), Thread(target=submit)]
        for worker in workers:
            worker.start()
        for worker in workers:
            worker.join(timeout=2)

        self.assertTrue(all(not worker.is_alive() for worker in workers))
        self.assertEqual(50, subject.balance)
        self.assertEqual(2, sum(result.applied for result in results))

    def test_idempotent_ledger_applies_concurrent_duplicate_once(self) -> None:
        subject = ledger.IdempotentLedger()
        start = Barrier(3)
        results = []

        def submit() -> None:
            start.wait()
            results.append(subject.apply("req-demo-001", 25))

        workers = [Thread(target=submit), Thread(target=submit)]
        for worker in workers:
            worker.start()
        start.wait()
        for worker in workers:
            worker.join(timeout=2)

        self.assertTrue(all(not worker.is_alive() for worker in workers))
        self.assertEqual(25, subject.balance)
        self.assertEqual(1, sum(result.applied for result in results))

    def test_distinct_requests_apply_independently(self) -> None:
        subject = ledger.IdempotentLedger(10)
        first = subject.apply("req-demo-001", 25)
        second = subject.apply("req-demo-002", -5)
        self.assertTrue(first.applied)
        self.assertTrue(second.applied)
        self.assertEqual(30, subject.balance)

    def test_later_retry_is_ignored(self) -> None:
        subject = ledger.IdempotentLedger()
        first = subject.apply("req-demo-001", 25)
        retry = subject.apply("req-demo-001", 25)
        self.assertTrue(first.applied)
        self.assertFalse(retry.applied)
        self.assertEqual(25, subject.balance)


class DurableTransactionReliabilityTests(unittest.TestCase):
    def test_duplicate_is_ignored_after_restart(self) -> None:
        with TemporaryDirectory() as directory:
            database = Path(directory) / "ledger.db"
            first_process = ledger.DurableLedger(database)
            applied = first_process.apply("req-demo-001", 25)
            restarted_process = ledger.DurableLedger(database)
            retry = restarted_process.apply("req-demo-001", 25)
            self.assertTrue(applied.applied)
            self.assertFalse(retry.applied)
            self.assertEqual(25, restarted_process.balance())

    def test_concurrent_duplicate_is_committed_once(self) -> None:
        with TemporaryDirectory() as directory:
            subject = ledger.DurableLedger(Path(directory) / "ledger.db")
            start = Barrier(3)
            results = []

            def submit() -> None:
                start.wait()
                results.append(subject.apply("req-demo-001", 25))

            workers = [Thread(target=submit), Thread(target=submit)]
            for worker in workers:
                worker.start()
            start.wait()
            for worker in workers:
                worker.join(timeout=5)
            self.assertTrue(all(not worker.is_alive() for worker in workers))
            self.assertEqual(25, subject.balance())
            self.assertEqual(1, sum(result.applied for result in results))

    def test_failed_transaction_does_not_consume_request_key(self) -> None:
        with TemporaryDirectory() as directory:
            subject = ledger.DurableLedger(Path(directory) / "ledger.db")

            def fail_before_mutation() -> None:
                raise RuntimeError("synthetic failure before mutation")

            with self.assertRaisesRegex(RuntimeError, "synthetic failure"):
                subject.apply("req-demo-001", 25, fail_before_mutation)
            retry = subject.apply("req-demo-001", 25)
            self.assertTrue(retry.applied)
            self.assertEqual(25, subject.balance())


class TransactionalOutboxTests(unittest.TestCase):
    def test_state_change_and_outbox_intent_survive_restart(self) -> None:
        with TemporaryDirectory() as directory:
            database = Path(directory) / "ledger.db"
            subject = ledger.OutboxLedger(database)
            result = subject.apply("req-demo-001", 25)

            restarted = ledger.OutboxLedger(database)
            self.assertTrue(result.applied)
            self.assertEqual(25, restarted.balance())
            self.assertEqual([ledger.OutboxMessage("req-demo-001", 25)], restarted.pending())

    def test_successful_dispatch_acknowledges_message(self) -> None:
        with TemporaryDirectory() as directory:
            subject = ledger.OutboxLedger(Path(directory) / "ledger.db")
            subject.apply("req-demo-001", 25)
            delivered = []

            count = subject.dispatch(delivered.append)

            self.assertEqual(1, count)
            self.assertEqual([ledger.OutboxMessage("req-demo-001", 25)], delivered)
            self.assertEqual([], subject.pending())

    def test_failed_delivery_leaves_message_for_retry(self) -> None:
        with TemporaryDirectory() as directory:
            subject = ledger.OutboxLedger(Path(directory) / "ledger.db")
            subject.apply("req-demo-001", 25)

            def fail_delivery(_message) -> None:
                raise RuntimeError("synthetic downstream failure")

            with self.assertRaisesRegex(RuntimeError, "synthetic downstream"):
                subject.dispatch(fail_delivery)

            delivered = []
            count = subject.dispatch(delivered.append)
            self.assertEqual(1, count)
            self.assertEqual([ledger.OutboxMessage("req-demo-001", 25)], delivered)
            self.assertEqual([], subject.pending())

    def test_duplicate_request_creates_one_outbox_intent(self) -> None:
        with TemporaryDirectory() as directory:
            subject = ledger.OutboxLedger(Path(directory) / "ledger.db")
            first = subject.apply("req-demo-001", 25)
            retry = subject.apply("req-demo-001", 25)
            self.assertTrue(first.applied)
            self.assertFalse(retry.applied)
            self.assertEqual(25, subject.balance())
            self.assertEqual([ledger.OutboxMessage("req-demo-001", 25)], subject.pending())


if __name__ == "__main__":
    unittest.main()
