import unittest

from coalescing import Request, coalesce_requests


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


if __name__ == "__main__":
    unittest.main()
