import importlib.util
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest


MODULE_PATH = Path(__file__).parents[1] / "retry_policy.py"
SPEC = importlib.util.spec_from_file_location("transaction_retry_policy", MODULE_PATH)
retry_policy = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(retry_policy)


class RetryPolicyTests(unittest.TestCase):
    def test_failures_use_deterministic_exponential_backoff(self) -> None:
        with TemporaryDirectory() as directory:
            subject = retry_policy.RetryPolicyStore(Path(directory) / "retry.db")

            first = subject.record_failure("req-demo-001", now=100.0, base_backoff_seconds=2.0)
            self.assertEqual(1, first.attempt_count)
            self.assertEqual(102.0, first.next_attempt_at)
            self.assertFalse(first.quarantined)
            self.assertFalse(subject.is_deliverable("req-demo-001", now=101.9))
            self.assertTrue(subject.is_deliverable("req-demo-001", now=102.0))

            second = subject.record_failure("req-demo-001", now=102.0, base_backoff_seconds=2.0)
            self.assertEqual(2, second.attempt_count)
            self.assertEqual(106.0, second.next_attempt_at)
            self.assertFalse(second.quarantined)

    def test_message_is_quarantined_at_attempt_limit(self) -> None:
        with TemporaryDirectory() as directory:
            subject = retry_policy.RetryPolicyStore(Path(directory) / "retry.db")

            subject.record_failure("req-demo-001", now=100.0, max_attempts=2)
            decision = subject.record_failure("req-demo-001", now=101.0, max_attempts=2)

            self.assertTrue(decision.quarantined)
            self.assertIsNone(decision.next_attempt_at)
            self.assertFalse(subject.is_deliverable("req-demo-001", now=10_000.0))
            self.assertEqual([decision], subject.quarantined())

    def test_deferred_poison_message_does_not_block_healthy_message(self) -> None:
        with TemporaryDirectory() as directory:
            subject = retry_policy.RetryPolicyStore(Path(directory) / "retry.db")
            subject.record_failure("req-demo-poison", now=100.0, base_backoff_seconds=30.0)

            self.assertFalse(subject.is_deliverable("req-demo-poison", now=110.0))
            self.assertTrue(subject.is_deliverable("req-demo-healthy", now=110.0))

    def test_retry_state_survives_restart(self) -> None:
        with TemporaryDirectory() as directory:
            database = Path(directory) / "retry.db"
            retry_policy.RetryPolicyStore(database).record_failure(
                "req-demo-001", now=100.0, base_backoff_seconds=5.0
            )

            restarted = retry_policy.RetryPolicyStore(database)
            self.assertFalse(restarted.is_deliverable("req-demo-001", now=104.9))
            self.assertTrue(restarted.is_deliverable("req-demo-001", now=105.0))

    def test_invalid_policy_values_are_rejected(self) -> None:
        with TemporaryDirectory() as directory:
            subject = retry_policy.RetryPolicyStore(Path(directory) / "retry.db")
            with self.assertRaisesRegex(ValueError, "max_attempts"):
                subject.record_failure("req-demo-001", max_attempts=0)
            with self.assertRaisesRegex(ValueError, "base_backoff_seconds"):
                subject.record_failure("req-demo-001", base_backoff_seconds=0)


if __name__ == "__main__":
    unittest.main()
