import unittest

from concurrency import (
    RetryCancellation,
    RetryCancelled,
    RetryDeadlineExceeded,
    RetryExhausted,
    RetryPolicy,
    SyntheticStateStore,
    VersionConflict,
    reconcile_with_retry,
    reconcile_with_timed_retry,
)
from delivery import DeliveryState, ProviderEvent, ReconciliationState


class ConflictOnceStore(SyntheticStateStore):
    def __init__(self, initial_state):
        super().__init__(initial_state)
        self.write_attempts = 0

    def compare_and_swap(self, expected_version, state):
        self.write_attempts += 1
        if self.write_attempts == 1:
            current = self.read()
            self.write_unchecked(current.state)
            raise VersionConflict("synthetic competing write")
        return super().compare_and_swap(expected_version, state)


class AlwaysConflictStore(SyntheticStateStore):
    def __init__(self, initial_state):
        super().__init__(initial_state)
        self.write_attempts = 0

    def compare_and_swap(self, expected_version, state):
        self.write_attempts += 1
        current = self.read()
        self.write_unchecked(current.state)
        raise VersionConflict("synthetic competing write")


class BoundedRetryTests(unittest.TestCase):
    def setUp(self):
        self.initial_state = ReconciliationState(
            DeliveryState.ACCEPTED, frozenset({"evt-synthetic-200"}), 200
        )
        self.delivered = ProviderEvent(
            "evt-synthetic-201", 201, DeliveryState.DELIVERED, "synthetic delivery"
        )

    def test_retry_re_reads_after_conflict_and_succeeds_within_budget(self):
        store = ConflictOnceStore(self.initial_state)

        result = reconcile_with_retry(store, self.delivered, max_attempts=2)

        self.assertEqual(store.write_attempts, 2)
        self.assertEqual(result.state.current_state, DeliveryState.DELIVERED)
        self.assertIn("evt-synthetic-201", result.state.seen_event_ids)

    def test_retry_exhaustion_is_explicit_and_leaves_event_uncommitted(self):
        store = AlwaysConflictStore(self.initial_state)

        with self.assertRaisesRegex(RetryExhausted, "after 2 attempts"):
            reconcile_with_retry(store, self.delivered, max_attempts=2)

        self.assertEqual(store.write_attempts, 2)
        self.assertEqual(store.read().state.current_state, DeliveryState.ACCEPTED)
        self.assertNotIn("evt-synthetic-201", store.read().state.seen_event_ids)

    def test_retry_budget_must_allow_at_least_one_attempt(self):
        store = SyntheticStateStore(self.initial_state)

        with self.assertRaisesRegex(ValueError, "at least 1"):
            reconcile_with_retry(store, self.delivered, max_attempts=0)

    def test_timed_retry_records_deterministic_delay_before_success(self):
        store = ConflictOnceStore(self.initial_state)
        policy = RetryPolicy(delays_ms=(25, 50), deadline_ms=100)

        result = reconcile_with_timed_retry(store, self.delivered, policy)

        self.assertEqual(result.attempts, 2)
        self.assertEqual(result.elapsed_ms, 25)
        self.assertEqual(result.scheduled_delays_ms, (25,))
        self.assertEqual(result.snapshot.state.current_state, DeliveryState.DELIVERED)

    def test_timed_retry_refuses_attempt_that_would_cross_deadline(self):
        store = AlwaysConflictStore(self.initial_state)
        policy = RetryPolicy(delays_ms=(40, 40), deadline_ms=60)

        with self.assertRaisesRegex(RetryDeadlineExceeded, "60ms"):
            reconcile_with_timed_retry(store, self.delivered, policy)

        self.assertEqual(store.write_attempts, 2)
        self.assertNotIn("evt-synthetic-201", store.read().state.seen_event_ids)

    def test_cancellation_before_first_attempt_does_not_touch_store(self):
        store = AlwaysConflictStore(self.initial_state)
        policy = RetryPolicy(delays_ms=(25,), deadline_ms=100)
        cancellation = RetryCancellation(cancel_before_attempt=1)

        with self.assertRaisesRegex(RetryCancelled, "before attempt 1"):
            reconcile_with_timed_retry(store, self.delivered, policy, cancellation)

        self.assertEqual(store.write_attempts, 0)
        self.assertEqual(store.read().version, 0)
        self.assertNotIn("evt-synthetic-201", store.read().state.seen_event_ids)

    def test_cancellation_stops_retry_after_conflict_without_committing_event(self):
        store = AlwaysConflictStore(self.initial_state)
        policy = RetryPolicy(delays_ms=(25, 50), deadline_ms=100)
        cancellation = RetryCancellation(cancel_before_attempt=2)

        with self.assertRaisesRegex(RetryCancelled, "before attempt 2"):
            reconcile_with_timed_retry(store, self.delivered, policy, cancellation)

        self.assertEqual(store.write_attempts, 1)
        self.assertEqual(store.read().state.current_state, DeliveryState.ACCEPTED)
        self.assertNotIn("evt-synthetic-201", store.read().state.seen_event_ids)

    def test_cancellation_is_distinct_from_deadline_exhaustion(self):
        store = AlwaysConflictStore(self.initial_state)
        policy = RetryPolicy(delays_ms=(40,), deadline_ms=20)
        cancellation = RetryCancellation(cancel_before_attempt=2)

        with self.assertRaises(RetryDeadlineExceeded) as raised:
            reconcile_with_timed_retry(store, self.delivered, policy, cancellation)

        self.assertNotIsInstance(raised.exception, RetryCancelled)
        self.assertEqual(store.write_attempts, 1)

    def test_retry_policy_rejects_negative_timing_values(self):
        with self.assertRaisesRegex(ValueError, "non-negative"):
            RetryPolicy(delays_ms=(-1,), deadline_ms=10)

        with self.assertRaisesRegex(ValueError, "non-negative"):
            RetryPolicy(delays_ms=(1,), deadline_ms=-1)

    def test_cancellation_requires_a_valid_attempt_number(self):
        with self.assertRaisesRegex(ValueError, "at least 1"):
            RetryCancellation(cancel_before_attempt=0)


if __name__ == "__main__":
    unittest.main()
