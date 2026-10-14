"""Integration tests for dispatch failure, retry scheduling, and quarantine."""

from pathlib import Path
import sys

LAB_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(LAB_DIR))

from ledger import OutboxLedger
from retry_policy import RetryPolicyStore


def test_failed_dispatch_records_backoff_before_releasing_lease(tmp_path):
    database = tmp_path / "ledger.db"
    ledger = OutboxLedger(database)
    ledger.apply("req-demo-backoff", 7)

    def fail(_message):
        raise RuntimeError("synthetic delivery failure")

    try:
        ledger.dispatch(fail, base_backoff_seconds=60.0)
    except RuntimeError as error:
        assert str(error) == "synthetic delivery failure"
    else:
        raise AssertionError("synthetic delivery should fail")

    retry = RetryPolicyStore(database)
    assert retry.is_deliverable("req-demo-backoff") is False
    assert ledger.claim("worker-2") is None


def test_attempt_limit_quarantines_failed_dispatch(tmp_path):
    database = tmp_path / "ledger.db"
    ledger = OutboxLedger(database)
    ledger.apply("req-demo-quarantine", 11)

    def fail(_message):
        raise RuntimeError("synthetic delivery failure")

    try:
        ledger.dispatch(fail, max_attempts=1)
    except RuntimeError:
        pass
    else:
        raise AssertionError("synthetic delivery should fail")

    quarantined = RetryPolicyStore(database).quarantined()
    assert [(item.request_id, item.attempt_count) for item in quarantined] == [
        ("req-demo-quarantine", 1)
    ]
    assert ledger.claim("worker-2") is None


def test_successful_dispatch_does_not_create_retry_state(tmp_path):
    database = tmp_path / "ledger.db"
    ledger = OutboxLedger(database)
    ledger.apply("req-demo-success", 5)
    delivered = []

    count = ledger.dispatch(delivered.append)

    assert count == 1
    assert [message.request_id for message in delivered] == ["req-demo-success"]
    assert RetryPolicyStore(database).quarantined() == []
    assert ledger.pending() == []
