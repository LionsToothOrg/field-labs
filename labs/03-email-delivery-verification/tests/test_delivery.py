import unittest

from delivery import (
    DeliveryEvent,
    DeliveryState,
    ProviderEvent,
    ReconciliationOutcome,
    generated,
    reconcile_provider_events,
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
        sensitive_like_but_synthetic_detail = "synthetic payload body that should not be audited"
        event = ProviderEvent(
            "evt-synthetic-030",
            30,
            DeliveryState.ACCEPTED,
            sensitive_like_but_synthetic_detail,
        )

        result = reconcile_provider_events(generated(), (event,))

        self.assertEqual(result.decisions[0].outcome, ReconciliationOutcome.APPLIED)
        self.assertFalse(hasattr(result.decisions[0], "detail"))
        self.assertNotIn(sensitive_like_but_synthetic_detail, repr(result.decisions))


if __name__ == "__main__":
    unittest.main()
