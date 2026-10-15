import unittest

from concurrency import SyntheticStateStore, VersionConflict
from delivery import (
    DeliveryEvent,
    DeliveryState,
    ProviderEvent,
    ReconciliationState,
    generated,
    reconcile_provider_events,
    restore_trace,
)


class ConcurrentReconciliationTests(unittest.TestCase):
    def setUp(self):
        accepted_trace = generated().record(
            DeliveryEvent(DeliveryState.ACCEPTED, "synthetic provider acceptance")
        )
        self.initial_state = ReconciliationState(
            DeliveryState.ACCEPTED, frozenset({"evt-synthetic-100"}), 100
        )
        self.accepted_trace = accepted_trace
        self.delivered = ProviderEvent(
            "evt-synthetic-101", 101, DeliveryState.DELIVERED, "synthetic delivery"
        )
        self.deferred = ProviderEvent(
            "evt-synthetic-102", 102, DeliveryState.DEFERRED, "synthetic deferral"
        )

    def test_unchecked_writes_can_lose_stronger_delivery_evidence(self):
        store = SyntheticStateStore(self.initial_state)
        worker_a = store.read()
        worker_b = store.read()

        delivered_result = reconcile_provider_events(
            restore_trace(worker_a.state), (self.delivered,), worker_a.state
        )
        deferred_result = reconcile_provider_events(
            restore_trace(worker_b.state), (self.deferred,), worker_b.state
        )

        store.write_unchecked(delivered_result.state)
        store.write_unchecked(deferred_result.state)

        self.assertEqual(store.read().state.current_state, DeliveryState.DEFERRED)
        self.assertNotIn("evt-synthetic-101", store.read().state.seen_event_ids)

    def test_conditional_write_rejects_obsolete_worker_snapshot(self):
        store = SyntheticStateStore(self.initial_state)
        worker_a = store.read()
        worker_b = store.read()
        delivered_result = reconcile_provider_events(
            restore_trace(worker_a.state), (self.delivered,), worker_a.state
        )
        deferred_result = reconcile_provider_events(
            restore_trace(worker_b.state), (self.deferred,), worker_b.state
        )

        store.compare_and_swap(worker_a.version, delivered_result.state)

        with self.assertRaises(VersionConflict):
            store.compare_and_swap(worker_b.version, deferred_result.state)

    def test_retry_from_fresh_state_preserves_terminal_delivery(self):
        store = SyntheticStateStore(self.initial_state)
        worker_a = store.read()
        worker_b = store.read()
        delivered_result = reconcile_provider_events(
            restore_trace(worker_a.state), (self.delivered,), worker_a.state
        )
        stale_deferred_result = reconcile_provider_events(
            restore_trace(worker_b.state), (self.deferred,), worker_b.state
        )

        store.compare_and_swap(worker_a.version, delivered_result.state)
        with self.assertRaises(VersionConflict):
            store.compare_and_swap(worker_b.version, stale_deferred_result.state)

        fresh = store.read()
        retried = reconcile_provider_events(
            restore_trace(fresh.state), (self.deferred,), fresh.state
        )
        store.compare_and_swap(fresh.version, retried.state)

        final = store.read().state
        self.assertEqual(final.current_state, DeliveryState.DELIVERED)
        self.assertEqual(final.latest_sequence, 101)
        self.assertEqual(
            final.seen_event_ids,
            frozenset(
                {"evt-synthetic-100", "evt-synthetic-101", "evt-synthetic-102"}
            ),
        )


if __name__ == "__main__":
    unittest.main()
