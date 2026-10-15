import unittest

from concurrency import (
    RetryExhausted,
    SyntheticStateStore,
    VersionConflict,
    reconcile_with_retry,
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


if __name__ == "__main__":
    unittest.main()
