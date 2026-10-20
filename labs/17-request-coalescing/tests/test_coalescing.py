import unittest

from coalescing import Request, coalesce_requests, fan_out_failures, fan_out_successes


class RequestCoalescingTests(unittest.TestCase):
    def test_same_key_requests_share_one_origin_load(self) -> None:
        result = coalesce_requests(
            [
                Request("req-001", "synthetic-item-a"),
                Request("req-002", "synthetic-item-a"),
                Request("req-003", "synthetic-item-a"),
            ]
        )

        self.assertEqual(3, result.request_count)
        self.assertEqual(1, result.origin_loads)
        self.assertEqual(2, result.avoided_origin_loads)
        self.assertEqual("req-001", result.groups[0].leader.request_id)
        self.assertEqual(("req-002", "req-003"), tuple(r.request_id for r in result.groups[0].followers))

    def test_different_keys_do_not_coalesce(self) -> None:
        result = coalesce_requests(
            [
                Request("req-001", "synthetic-item-a"),
                Request("req-002", "synthetic-item-b"),
            ]
        )

        self.assertEqual(2, result.origin_loads)
        self.assertEqual(0, result.avoided_origin_loads)

    def test_interleaved_keys_preserve_first_leader_and_follower_order(self) -> None:
        result = coalesce_requests(
            [
                Request("req-001", "synthetic-item-a"),
                Request("req-002", "synthetic-item-b"),
                Request("req-003", "synthetic-item-a"),
                Request("req-004", "synthetic-item-b"),
            ]
        )

        self.assertEqual(("synthetic-item-a", "synthetic-item-b"), tuple(g.key for g in result.groups))
        self.assertEqual(("req-003",), tuple(r.request_id for r in result.groups[0].followers))
        self.assertEqual(("req-004",), tuple(r.request_id for r in result.groups[1].followers))

    def test_empty_batch_has_no_origin_loads(self) -> None:
        result = coalesce_requests([])
        self.assertEqual(0, result.request_count)
        self.assertEqual(0, result.origin_loads)
        self.assertEqual(0, result.avoided_origin_loads)

    def test_duplicate_request_ids_are_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "duplicate request_id"):
            coalesce_requests(
                [
                    Request("req-001", "synthetic-item-a"),
                    Request("req-001", "synthetic-item-a"),
                ]
            )

    def test_empty_identifiers_are_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "request_id"):
            coalesce_requests([Request("", "synthetic-item-a")])
        with self.assertRaisesRegex(ValueError, "key"):
            coalesce_requests([Request("req-001", "")])

    def test_successful_leader_value_is_fanned_out_to_followers(self) -> None:
        coalesced = coalesce_requests(
            [
                Request("req-001", "synthetic-item-a"),
                Request("req-002", "synthetic-item-a"),
                Request("req-003", "synthetic-item-a"),
            ]
        )

        result = fan_out_successes(coalesced, {"req-001": "synthetic-value-a"})

        self.assertEqual(1, result.origin_loads)
        self.assertEqual(("req-001", "req-002", "req-003"), tuple(d.request_id for d in result.deliveries))
        self.assertEqual({"synthetic-value-a"}, {d.value for d in result.deliveries})
        self.assertEqual({"req-001"}, {d.source_request_id for d in result.deliveries})

    def test_each_key_fans_out_only_its_own_leader_value(self) -> None:
        coalesced = coalesce_requests(
            [
                Request("req-001", "synthetic-item-a"),
                Request("req-002", "synthetic-item-b"),
                Request("req-003", "synthetic-item-a"),
                Request("req-004", "synthetic-item-b"),
            ]
        )

        result = fan_out_successes(
            coalesced,
            {"req-001": "synthetic-value-a", "req-002": "synthetic-value-b"},
        )

        delivered = {delivery.request_id: delivery for delivery in result.deliveries}
        self.assertEqual("synthetic-value-a", delivered["req-003"].value)
        self.assertEqual("req-001", delivered["req-003"].source_request_id)
        self.assertEqual("synthetic-value-b", delivered["req-004"].value)
        self.assertEqual("req-002", delivered["req-004"].source_request_id)
        self.assertEqual(2, result.origin_loads)

    def test_missing_leader_value_is_rejected_before_fanout(self) -> None:
        coalesced = coalesce_requests(
            [
                Request("req-001", "synthetic-item-a"),
                Request("req-002", "synthetic-item-a"),
            ]
        )

        with self.assertRaisesRegex(ValueError, "missing leader value: req-001"):
            fan_out_successes(coalesced, {})

    def test_follower_cannot_supply_an_independent_origin_value(self) -> None:
        coalesced = coalesce_requests(
            [
                Request("req-001", "synthetic-item-a"),
                Request("req-002", "synthetic-item-a"),
            ]
        )

        with self.assertRaisesRegex(ValueError, "unexpected leader value: req-002"):
            fan_out_successes(
                coalesced,
                {"req-001": "synthetic-value-a", "req-002": "independent-value"},
            )

    def test_empty_batch_fans_out_no_results(self) -> None:
        result = fan_out_successes(coalesce_requests([]), {})
        self.assertEqual((), result.deliveries)
        self.assertEqual(0, result.origin_loads)

    def test_leader_failure_is_fanned_out_to_followers(self) -> None:
        coalesced = coalesce_requests(
            [
                Request("req-001", "synthetic-item-a"),
                Request("req-002", "synthetic-item-a"),
                Request("req-003", "synthetic-item-a"),
            ]
        )

        result = fan_out_failures(coalesced, {"req-001": "synthetic-origin-unavailable"})

        self.assertEqual(1, result.origin_loads)
        self.assertEqual(("req-001", "req-002", "req-003"), tuple(d.request_id for d in result.deliveries))
        self.assertEqual({"synthetic-origin-unavailable"}, {d.error for d in result.deliveries})
        self.assertEqual({"req-001"}, {d.source_request_id for d in result.deliveries})

    def test_each_key_receives_only_its_own_leader_failure(self) -> None:
        coalesced = coalesce_requests(
            [
                Request("req-001", "synthetic-item-a"),
                Request("req-002", "synthetic-item-b"),
                Request("req-003", "synthetic-item-a"),
                Request("req-004", "synthetic-item-b"),
            ]
        )

        result = fan_out_failures(
            coalesced,
            {"req-001": "synthetic-error-a", "req-002": "synthetic-error-b"},
        )

        delivered = {delivery.request_id: delivery for delivery in result.deliveries}
        self.assertEqual("synthetic-error-a", delivered["req-003"].error)
        self.assertEqual("req-001", delivered["req-003"].source_request_id)
        self.assertEqual("synthetic-error-b", delivered["req-004"].error)
        self.assertEqual("req-002", delivered["req-004"].source_request_id)
        self.assertEqual(2, result.origin_loads)

    def test_missing_leader_failure_is_rejected_before_fanout(self) -> None:
        coalesced = coalesce_requests(
            [
                Request("req-001", "synthetic-item-a"),
                Request("req-002", "synthetic-item-a"),
            ]
        )

        with self.assertRaisesRegex(ValueError, "missing leader failure: req-001"):
            fan_out_failures(coalesced, {})

    def test_follower_cannot_supply_an_independent_failure(self) -> None:
        coalesced = coalesce_requests(
            [
                Request("req-001", "synthetic-item-a"),
                Request("req-002", "synthetic-item-a"),
            ]
        )

        with self.assertRaisesRegex(ValueError, "unexpected leader failure: req-002"):
            fan_out_failures(
                coalesced,
                {"req-001": "synthetic-error", "req-002": "independent-error"},
            )

    def test_empty_leader_failure_is_rejected(self) -> None:
        coalesced = coalesce_requests([Request("req-001", "synthetic-item-a")])

        with self.assertRaisesRegex(ValueError, "empty leader failure: req-001"):
            fan_out_failures(coalesced, {"req-001": ""})

    def test_empty_batch_fans_out_no_failures(self) -> None:
        result = fan_out_failures(coalesce_requests([]), {})
        self.assertEqual((), result.deliveries)
        self.assertEqual(0, result.origin_loads)


if __name__ == "__main__":
    unittest.main()
