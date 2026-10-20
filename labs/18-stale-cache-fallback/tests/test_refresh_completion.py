import unittest

from stale_cache import (
    CacheDecision,
    CacheEntry,
    RefreshCompletion,
    RefreshRequest,
    RevalidationOutcome,
    complete_stale_refreshes,
    plan_stale_refreshes,
)


class SharedRefreshCompletionTests(unittest.TestCase):
    def setUp(self):
        self.entry = CacheEntry("synthetic-reading", stored_at_ms=1_000, ttl_ms=500)

    def _plan(self):
        return plan_stale_refreshes(
            [RefreshRequest("request-a", "sensor-a"), RefreshRequest("request-b", "sensor-a")],
            entries_by_key={"sensor-a": self.entry},
            now_ms=1_700,
            max_stale_ms=300,
        )

    def test_success_is_shared_by_leader_and_followers(self):
        deliveries = complete_stale_refreshes(
            self._plan(),
            entries_by_key={"sensor-a": self.entry},
            completions_by_leader={"request-a": RefreshCompletion(RevalidationOutcome.SUCCESS, "synthetic-reading-v2")},
            now_ms=1_700,
            max_stale_ms=300,
        )
        self.assertEqual(("request-a", "request-b"), tuple(item.request_id for item in deliveries))
        self.assertTrue(all(item.leader_request_id == "request-a" for item in deliveries))
        self.assertTrue(all(item.result.decision is CacheDecision.FRESH for item in deliveries))
        self.assertTrue(all(item.result.value == "synthetic-reading-v2" for item in deliveries))

    def test_failure_is_shared_only_inside_original_stale_budget(self):
        deliveries = complete_stale_refreshes(
            self._plan(),
            entries_by_key={"sensor-a": self.entry},
            completions_by_leader={"request-a": RefreshCompletion(RevalidationOutcome.FAILURE)},
            now_ms=1_750,
            max_stale_ms=300,
        )
        self.assertTrue(all(item.result.decision is CacheDecision.STALE for item in deliveries))
        self.assertTrue(all(item.result.value == "synthetic-reading" for item in deliveries))

    def test_failure_after_budget_withholds_value_from_every_reader(self):
        deliveries = complete_stale_refreshes(
            self._plan(),
            entries_by_key={"sensor-a": self.entry},
            completions_by_leader={"request-a": RefreshCompletion(RevalidationOutcome.FAILURE)},
            now_ms=1_801,
            max_stale_ms=300,
        )
        self.assertTrue(all(item.result.decision is CacheDecision.MISS for item in deliveries))
        self.assertTrue(all(item.result.value is None for item in deliveries))

    def test_independent_keys_receive_independent_leader_results(self):
        plan = plan_stale_refreshes(
            [RefreshRequest("request-a", "sensor-a"), RefreshRequest("request-b", "sensor-b")],
            entries_by_key={"sensor-a": self.entry, "sensor-b": self.entry},
            now_ms=1_700,
            max_stale_ms=300,
        )
        deliveries = complete_stale_refreshes(
            plan,
            entries_by_key={"sensor-a": self.entry, "sensor-b": self.entry},
            completions_by_leader={
                "request-a": RefreshCompletion(RevalidationOutcome.SUCCESS, "synthetic-a-v2"),
                "request-b": RefreshCompletion(RevalidationOutcome.FAILURE),
            },
            now_ms=1_700,
            max_stale_ms=300,
        )
        self.assertEqual(CacheDecision.FRESH, deliveries[0].result.decision)
        self.assertEqual(CacheDecision.STALE, deliveries[1].result.decision)

    def test_completion_map_must_match_leaders_exactly(self):
        for completions in ({}, {"request-b": RefreshCompletion(RevalidationOutcome.FAILURE)}):
            with self.subTest(completions=completions):
                with self.assertRaises(ValueError):
                    complete_stale_refreshes(
                        self._plan(), entries_by_key={"sensor-a": self.entry},
                        completions_by_leader=completions, now_ms=1_700, max_stale_ms=300,
                    )

    def test_missing_entry_and_malformed_completion_fail_closed(self):
        with self.assertRaises(ValueError):
            complete_stale_refreshes(
                self._plan(), entries_by_key={},
                completions_by_leader={"request-a": RefreshCompletion(RevalidationOutcome.FAILURE)},
                now_ms=1_700, max_stale_ms=300,
            )
        with self.assertRaises(ValueError):
            complete_stale_refreshes(
                self._plan(), entries_by_key={"sensor-a": self.entry},
                completions_by_leader={"request-a": "failure"},
                now_ms=1_700, max_stale_ms=300,
            )

    def test_empty_plan_completes_without_deliveries(self):
        plan = plan_stale_refreshes([], entries_by_key={}, now_ms=1_700, max_stale_ms=300)
        self.assertEqual((), complete_stale_refreshes(plan, entries_by_key={}, completions_by_leader={}, now_ms=1_700, max_stale_ms=300))


if __name__ == "__main__":
    unittest.main()
