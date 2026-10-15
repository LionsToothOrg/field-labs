import unittest

from delivery import (
    DeliveryEvent,
    DeliveryState,
    ProviderEvent,
    ReconciliationOutcome,
    generated,
    reconcile_provider_events,
    restore_trace,
)


class DeliveryTraceTests(unittest.TestCase):
    def test_generation_is_not_delivery(self):
        trace = generated()
        self.assertEqual(trace.current_state, DeliveryState.GENERATED)
        self.assertNotEqual(trace.current_state, DeliveryState.DELIVERED)

    def test_acceptance_is_not_delivery(self):
        trace = generated().record(
            DeliveryEvent(DeliveryState.ACCEPTED, "synthetic provider accepted message")
        )
        self.assertEqual(trace.current_state, DeliveryState.ACCEPTED)
        self.assertNotEqual(trace.current_state, DeliveryState.DELIVERED)

    def test_deferred_message_can_later_be_delivered(self):
        trace = generated()
        trace = trace.record(
            DeliveryEvent(DeliveryState.ACCEPTED, "synthetic provider accepted message")
        )
        trace = trace.record(
            DeliveryEvent(DeliveryState.DEFERRED, "synthetic mailbox temporarily unavailable")
        )
        trace = trace.record(
            DeliveryEvent(DeliveryState.DELIVERED, "synthetic delivery evidence recorded")
        )
        self.assertEqual(trace.current_state, DeliveryState.DELIVERED)

    def test_bounce_is_terminal(self):
        trace = generated()
        trace = trace.record(
            DeliveryEvent(DeliveryState.ACCEPTED, "synthetic provider accepted message")
        )
        trace = trace.record(
            DeliveryEvent(DeliveryState.BOUNCED, "synthetic mailbox rejected message")
        )
        with self.assertRaises(ValueError):
            trace.record(
                DeliveryEvent(DeliveryState.DELIVERED, "impossible later delivery")
            )

    def test_delivery_requires_provider_acceptance(self):
        with self.assertRaises(ValueError):
            generated().record(
                DeliveryEvent(DeliveryState.DELIVERED, "unsupported delivery claim")
            )


class ProviderEventReconciliationTests(unittest.TestCase):
    def test_duplicate_provider_event_is_applied_once(self):
        duplicate = ProviderEvent(
            "evt-synthetic-001", 10, DeliveryState.ACCEPTED, "synthetic acceptance"
        )
        result = reconcile_provider_events(generated(), (duplicate, duplicate))

        self.assertEqual(result.trace.current_state, DeliveryState.ACCEPTED)
        self.assertEqual(result.applied_event_ids, ("evt-synthetic-001",))
        self.assertEqual(result.ignored_event_ids, ("evt-synthetic-001",))
        self.assertEqual(
            tuple(decision.outcome for decision in result.decisions),
            (ReconciliationOutcome.APPLIED, ReconciliationOutcome.DUPLICATE),
        )

    def test_stale_event_cannot_rewrite_newer_evidence(self):
        events = (
            ProviderEvent(
                "evt-synthetic-010", 10, DeliveryState.ACCEPTED, "synthetic acceptance"
            ),
            ProviderEvent(
                "evt-synthetic-012", 12, DeliveryState.DELIVERED, "synthetic delivery"
            ),
            ProviderEvent(
                "evt-synthetic-011", 11, DeliveryState.DEFERRED, "late synthetic deferral"
            ),
        )
        result = reconcile_provider_events(generated(), events)

        self.assertEqual(result.trace.current_state, DeliveryState.DELIVERED)
        self.assertEqual(
            result.applied_event_ids, ("evt-synthetic-010", "evt-synthetic-012")
        )
        self.assertEqual(result.ignored_event_ids, ("evt-synthetic-011",))
        self.assertEqual(result.decisions[-1].outcome, ReconciliationOutcome.STALE)

    def test_contradictory_event_cannot_reverse_terminal_delivery(self):
        events = (
            ProviderEvent(
                "evt-synthetic-020", 20, DeliveryState.ACCEPTED, "synthetic acceptance"
            ),
            ProviderEvent(
                "evt-synthetic-021", 21, DeliveryState.DELIVERED, "synthetic delivery"
            ),
            ProviderEvent(
                "evt-synthetic-022", 22, DeliveryState.BOUNCED, "contradictory synthetic bounce"
            ),
        )
        result = reconcile_provider_events(generated(), events)

        self.assertEqual(result.trace.current_state, DeliveryState.DELIVERED)
        self.assertEqual(result.ignored_event_ids, ("evt-synthetic-022",))
        self.assertEqual(
            result.decisions[-1].outcome, ReconciliationOutcome.CONTRADICTORY
        )

    def test_decisions_do_not_copy_provider_detail(self):
        synthetic_detail = "synthetic payload body that should not be audited"
        event = ProviderEvent(
            "evt-synthetic-030", 30, DeliveryState.ACCEPTED, synthetic_detail
        )

        result = reconcile_provider_events(generated(), (event,))

        self.assertEqual(result.decisions[0].outcome, ReconciliationOutcome.APPLIED)
        self.assertFalse(hasattr(result.decisions[0], "detail"))
        self.assertNotIn(synthetic_detail, repr(result.decisions))

    def test_duplicate_is_rejected_after_restart(self):
        accepted = ProviderEvent(
            "evt-synthetic-040", 40, DeliveryState.ACCEPTED, "synthetic acceptance"
        )
        first = reconcile_provider_events(generated(), (accepted,))

        restored = restore_trace(first.state)
        after_restart = reconcile_provider_events(restored, (accepted,), first.state)

        self.assertEqual(after_restart.trace.current_state, DeliveryState.ACCEPTED)
        self.assertEqual(after_restart.applied_event_ids, ())
        self.assertEqual(after_restart.decisions[0].outcome, ReconciliationOutcome.DUPLICATE)

    def test_stale_event_is_rejected_after_restart(self):
        first = reconcile_provider_events(
            generated(),
            (
                ProviderEvent(
                    "evt-synthetic-050", 50, DeliveryState.ACCEPTED, "synthetic acceptance"
                ),
                ProviderEvent(
                    "evt-synthetic-052", 52, DeliveryState.DEFERRED, "synthetic deferral"
                ),
            ),
        )
        restored = restore_trace(first.state)
        stale = ProviderEvent(
            "evt-synthetic-051", 51, DeliveryState.DEFERRED, "late synthetic deferral"
        )

        after_restart = reconcile_provider_events(restored, (stale,), first.state)

        self.assertEqual(after_restart.trace.current_state, DeliveryState.DEFERRED)
        self.assertEqual(after_restart.decisions[0].outcome, ReconciliationOutcome.STALE)

    def test_durable_state_does_not_copy_provider_detail(self):
        synthetic_detail = "synthetic payload detail excluded from durable state"
        result = reconcile_provider_events(
            generated(),
            (
                ProviderEvent(
                    "evt-synthetic-060",
                    60,
                    DeliveryState.ACCEPTED,
                    synthetic_detail,
                ),
            ),
        )

        self.assertNotIn(synthetic_detail, repr(result.state))
        self.assertEqual(result.state.current_state, DeliveryState.ACCEPTED)
        self.assertEqual(result.state.latest_sequence, 60)
        self.assertEqual(result.state.seen_event_ids, frozenset({"evt-synthetic-060"}))

    def test_trace_and_restored_state_must_agree(self):
        first = reconcile_provider_events(
            generated(),
            (
                ProviderEvent(
                    "evt-synthetic-070", 70, DeliveryState.ACCEPTED, "synthetic acceptance"
                ),
            ),
        )

        with self.assertRaises(ValueError):
            reconcile_provider_events(generated(), (), first.state)


if __name__ == "__main__":
    unittest.main()
