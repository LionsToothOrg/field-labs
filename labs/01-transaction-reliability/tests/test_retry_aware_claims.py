import importlib.util
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest


LAB_PATH = Path(__file__).parents[1]


def load_module(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, LAB_PATH / filename)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


ledger = load_module("transaction_ledger_retry_claims", "ledger.py")
retry_policy = load_module("transaction_retry_claims", "retry_policy.py")


class RetryAwareClaimTests(unittest.TestCase):
    def test_claim_skips_deferred_message_and_selects_healthy_work(self) -> None:
        with TemporaryDirectory() as directory:
            database = Path(directory) / "ledger.db"
            subject = ledger.OutboxLedger(database)
            retries = retry_policy.RetryPolicyStore(database)
            subject.apply("req-demo-a-deferred", 10)
            subject.apply("req-demo-b-healthy", 20)
            retries.record_failure("req-demo-a-deferred", now=100.0, base_backoff_seconds=30.0)

            claimed = subject.claim("worker-demo", now=110.0)

            self.assertIsNotNone(claimed)
            self.assertEqual("req-demo-b-healthy", claimed.request_id)

    def test_claim_allows_deferred_message_when_backoff_expires(self) -> None:
        with TemporaryDirectory() as directory:
            database = Path(directory) / "ledger.db"
            subject = ledger.OutboxLedger(database)
            retries = retry_policy.RetryPolicyStore(database)
            subject.apply("req-demo-deferred", 10)
            retries.record_failure("req-demo-deferred", now=100.0, base_backoff_seconds=30.0)

            self.assertIsNone(subject.claim("worker-demo", now=129.9))
            claimed = subject.claim("worker-demo", now=130.0)

            self.assertIsNotNone(claimed)
            self.assertEqual("req-demo-deferred", claimed.request_id)

    def test_claim_never_returns_quarantined_message(self) -> None:
        with TemporaryDirectory() as directory:
            database = Path(directory) / "ledger.db"
            subject = ledger.OutboxLedger(database)
            retries = retry_policy.RetryPolicyStore(database)
            subject.apply("req-demo-quarantined", 10)
            retries.record_failure("req-demo-quarantined", now=100.0, max_attempts=1)

            self.assertIsNone(subject.claim("worker-demo", now=10_000.0))


if __name__ == "__main__":
    unittest.main()
