import unittest

from coalescing import Request, coalesce_requests, fan_out_terminal_timeouts


class RequestCoalescingTimeoutTests(unittest.TestCase):
    def test_terminal_timeout_is_shared_by_leader_and_followers(self) -> None:
        coalesced = coalesce_requests(
            [
                Request("req-001", "synthetic-item-a"),
                Request("req-002", "synthetic-item-a"),
                Request("req-003", "synthetic-item-a"),
            ]
        )

        result = fan_out_terminal_timeouts(coalesced, {"req-001": 250})

        self.assertEqual(1, result.origin_loads)
        self.assertEqual(("req-001", "req-002", "req-003"), tuple(d.request_id for d in result.deliveries))
        self.assertEqual({250}, {d.timeout_ms for d in result.deliveries})
        self.assertEqual({"req-001"}, {d.source_request_id for d in result.deliveries})

    def test_timeout_policy_remains_isolated_by_key(self) -> None:
        coalesced = coalesce_requests(
            [
                Request("req-001", "synthetic-item-a"),
                Request("req-002", "synthetic-item-b"),
                Request("req-003", "synthetic-item-a"),
                Request("req-004", "synthetic-item-b"),
            ]
        )

        result = fan_out_terminal_timeouts(coalesced, {"req-001": 250, "req-002": 500})
        delivered = {delivery.request_id: delivery for delivery in result.deliveries}

        self.assertEqual(250, delivered["req-003"].timeout_ms)
        self.assertEqual("req-001", delivered["req-003"].source_request_id)
        self.assertEqual(500, delivered["req-004"].timeout_ms)
        self.assertEqual("req-002", delivered["req-004"].source_request_id)
        self.assertEqual(2, result.origin_loads)

    def test_missing_leader_timeout_is_rejected_before_fanout(self) -> None:
        coalesced = coalesce_requests([Request("req-001", "synthetic-item-a")])
        with self.assertRaisesRegex(ValueError, "missing leader timeout: req-001"):
            fan_out_terminal_timeouts(coalesced, {})

    def test_follower_cannot_supply_an_independent_timeout(self) -> None:
        coalesced = coalesce_requests(
            [Request("req-001", "synthetic-item-a"), Request("req-002", "synthetic-item-a")]
        )
        with self.assertRaisesRegex(ValueError, "unexpected leader timeout: req-002"):
            fan_out_terminal_timeouts(coalesced, {"req-001": 250, "req-002": 250})

    def test_non_positive_or_non_integer_timeout_is_rejected(self) -> None:
        coalesced = coalesce_requests([Request("req-001", "synthetic-item-a")])
        for invalid in (0, -1, 1.5, True):
            with self.subTest(invalid=invalid):
                with self.assertRaisesRegex(ValueError, "invalid leader timeout: req-001"):
                    fan_out_terminal_timeouts(coalesced, {"req-001": invalid})

    def test_empty_batch_has_no_timeout_deliveries(self) -> None:
        result = fan_out_terminal_timeouts(coalesce_requests([]), {})
        self.assertEqual((), result.deliveries)
        self.assertEqual(0, result.origin_loads)


if __name__ == "__main__":
    unittest.main()
