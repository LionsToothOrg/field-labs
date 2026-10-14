import importlib.util
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest


MODULE_PATH = Path(__file__).parents[1] / "retry_policy.py"
SPEC = importlib.util.spec_from_file_location("transaction_retry_policy", MODULE_PATH)
retry_policy = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(retry_policy)


class QuarantineReplayTests(unittest.TestCase):
    def test_replay_restores_eligibility_and_preserves_attempt_history(self) -> None:
        with TemporaryDirectory() as directory:
            subject = retry_policy.RetryPolicyStore(Path(directory) / "retry.db")
            subject.record_failure("req-demo-replay", now=100.0, max_attempts=2)
            quarantined = subject.record_failure("req-demo-replay", now=101.0, max_attempts=2)

            replayed = subject.replay_quarantined("req-demo-replay", now=200.0)

            self.assertTrue(quarantined.quarantined)
            self.assertEqual(2, replayed.attempt_count)
            self.assertFalse(replayed.quarantined)
            self.assertTrue(subject.is_deliverable("req-demo-replay", now=200.0))
            self.assertEqual([], subject.quarantined())

    def test_replay_is_audited_with_attempt_count(self) -> None:
        with TemporaryDirectory() as directory:
            subject = retry_policy.RetryPolicyStore(Path(directory) / "retry.db")
            subject.record_failure("req-demo-audit", now=100.0, max_attempts=1)

            subject.replay_quarantined("req-demo-audit", now=250.0)

            self.assertEqual(
                [retry_policy.QuarantineEvent("req-demo-audit", "replay", 250.0, 1)],
                subject.quarantine_events("req-demo-audit"),
            )

    def test_replay_rejects_unknown_or_non_quarantined_requests(self) -> None:
        with TemporaryDirectory() as directory:
            subject = retry_policy.RetryPolicyStore(Path(directory) / "retry.db")
            subject.record_failure("req-demo-deferred", now=100.0, max_attempts=3)

            with self.assertRaisesRegex(ValueError, "not quarantined"):
                subject.replay_quarantined("req-demo-deferred", now=200.0)
            with self.assertRaisesRegex(ValueError, "not quarantined"):
                subject.replay_quarantined("req-demo-missing", now=200.0)

            self.assertEqual([], subject.quarantine_events())

    def test_replayed_message_requarantines_on_next_failure_at_limit(self) -> None:
        with TemporaryDirectory() as directory:
            subject = retry_policy.RetryPolicyStore(Path(directory) / "retry.db")
            subject.record_failure("req-demo-repeat", now=100.0, max_attempts=2)
            subject.record_failure("req-demo-repeat", now=101.0, max_attempts=2)
            subject.replay_quarantined("req-demo-repeat", now=200.0)

            decision = subject.record_failure("req-demo-repeat", now=201.0, max_attempts=2)

            self.assertEqual(3, decision.attempt_count)
            self.assertTrue(decision.quarantined)
            self.assertFalse(subject.is_deliverable("req-demo-repeat", now=10_000.0))


if __name__ == "__main__":
    unittest.main()
