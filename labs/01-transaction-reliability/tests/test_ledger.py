import importlib.util
from pathlib import Path
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


if __name__ == "__main__":
    unittest.main()
