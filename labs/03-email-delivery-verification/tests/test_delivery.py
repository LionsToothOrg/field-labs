import unittest

from delivery import DeliveryEvent, DeliveryState, generated


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


if __name__ == "__main__":
    unittest.main()
