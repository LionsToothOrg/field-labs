import unittest

from stale_cache import (
    CacheEntry,
    FollowerExit,
    RefreshCompletion,
    RefreshRequest,
    RevalidationOutcome,
    apply_follower_exits,
    complete_stale_refreshes,
    plan_stale_refreshes,
)


class FollowerExitTests(unittest.TestCase):
    def setUp(self):
        self.entry = CacheEntry("synthetic-reading", stored_at_ms=1_000, ttl_ms=500)
        self.plan = plan_stale_refreshes(
            [
                RefreshRequest("request-a", "sensor-a"),
                RefreshRequest("request-b", "sensor-a"),
                RefreshRequest("request-c", "sensor-a"),
            ],
            entries_by_key={"sensor-a": self.entry},
            now_ms=1_700,
            max_stale_ms=300,
        )

    def test_timeout_removes_only_follower_from_completion_delivery(self):
        wait = apply_follower_exits(
            self.plan,
            exits_by_request={"request-b": FollowerExit.TIMEOUT},
        )
        self.assertEqual(1, wait.active_plan.origin_refresh_count)
        self.assertEqual(("request-c",), wait.active_plan.groups[0].follower_request_ids)
        self.assertEqual(FollowerExit.TIMEOUT, wait.departures[0].reason)

        deliveries = complete_stale_refreshes(
            wait.active_plan,
            entries_by_key={"sensor-a": self.entry},
            completions_by_leader={
                "request-a": RefreshCompletion(RevalidationOutcome.SUCCESS, "synthetic-reading-v2")
            },
            now_ms=1_750,
            max_stale_ms=300,
        )
        self.assertEqual(("request-a", "request-c"), tuple(item.request_id for item in deliveries))

    def test_cancellation_does_not_cancel_leader_or_elect_replacement(self):
        wait = apply_follower_exits(
            self.plan,
            exits_by_request={"request-b": FollowerExit.CANCELLED, "request-c": FollowerExit.CANCELLED},
        )
        group = wait.active_plan.groups[0]
        self.assertEqual("request-a", group.leader_request_id)
        self.assertEqual((), group.follower_request_ids)
        self.assertEqual(1, wait.active_plan.origin_refresh_count)

    def test_separate_keys_keep_independent_leaders_when_follower_exits(self):
        plan = plan_stale_refreshes(
            [
                RefreshRequest("request-a", "sensor-a"),
                RefreshRequest("request-b", "sensor-a"),
                RefreshRequest("request-c", "sensor-b"),
                RefreshRequest("request-d", "sensor-b"),
            ],
            entries_by_key={"sensor-a": self.entry, "sensor-b": self.entry},
            now_ms=1_700,
            max_stale_ms=300,
        )
        wait = apply_follower_exits(plan, exits_by_request={"request-d": FollowerExit.TIMEOUT})
        self.assertEqual(2, wait.active_plan.origin_refresh_count)
        self.assertEqual(("request-a", "request-c"), tuple(group.leader_request_id for group in wait.active_plan.groups))
        self.assertEqual(("request-b",), wait.active_plan.groups[0].follower_request_ids)
        self.assertEqual((), wait.active_plan.groups[1].follower_request_ids)

    def test_leader_and_unknown_request_cannot_exit_as_followers(self):
        for request_id in ("request-a", "request-unknown"):
            with self.subTest(request_id=request_id):
                with self.assertRaises(ValueError):
                    apply_follower_exits(self.plan, exits_by_request={request_id: FollowerExit.TIMEOUT})

    def test_exit_reason_must_be_explicit_enum(self):
        with self.assertRaises(ValueError):
            apply_follower_exits(self.plan, exits_by_request={"request-b": "timeout"})

    def test_no_exits_preserve_plan_and_origin_count(self):
        wait = apply_follower_exits(self.plan, exits_by_request={})
        self.assertEqual(self.plan, wait.active_plan)
        self.assertEqual((), wait.departures)


if __name__ == "__main__":
    unittest.main()
