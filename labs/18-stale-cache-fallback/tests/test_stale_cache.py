import unittest

from stale_cache import (
    CacheDecision,
    CacheEntry,
    RevalidationOutcome,
    apply_revalidation_outcome,
    evaluate_cache_entry,
)


class StaleCacheFallbackTests(unittest.TestCase):
    def setUp(self):
        self.entry = CacheEntry(value="synthetic-reading", stored_at_ms=1_000, ttl_ms=500)

    def test_fresh_entry_is_served_without_revalidation(self):
        result = evaluate_cache_entry(self.entry, now_ms=1_400, max_stale_ms=300)
        self.assertEqual(CacheDecision.FRESH, result.decision)
        self.assertEqual("synthetic-reading", result.value)
        self.assertEqual(400, result.age_ms)
        self.assertFalse(result.revalidate)

    def test_ttl_boundary_is_still_fresh(self):
        result = evaluate_cache_entry(self.entry, now_ms=1_500, max_stale_ms=300)
        self.assertEqual(CacheDecision.FRESH, result.decision)

    def test_stale_entry_within_budget_is_served_and_revalidated(self):
        result = evaluate_cache_entry(self.entry, now_ms=1_700, max_stale_ms=300)
        self.assertEqual(CacheDecision.STALE, result.decision)
        self.assertEqual("synthetic-reading", result.value)
        self.assertEqual(700, result.age_ms)
        self.assertTrue(result.revalidate)

    def test_max_stale_boundary_is_allowed(self):
        result = evaluate_cache_entry(self.entry, now_ms=1_800, max_stale_ms=300)
        self.assertEqual(CacheDecision.STALE, result.decision)

    def test_entry_beyond_stale_budget_becomes_miss(self):
        result = evaluate_cache_entry(self.entry, now_ms=1_801, max_stale_ms=300)
        self.assertEqual(CacheDecision.MISS, result.decision)
        self.assertIsNone(result.value)
        self.assertEqual(801, result.age_ms)
        self.assertFalse(result.revalidate)

    def test_missing_entry_is_miss(self):
        result = evaluate_cache_entry(None, now_ms=2_000, max_stale_ms=300)
        self.assertEqual(CacheDecision.MISS, result.decision)
        self.assertIsNone(result.age_ms)

    def test_zero_stale_budget_does_not_extend_expired_entry(self):
        result = evaluate_cache_entry(self.entry, now_ms=1_501, max_stale_ms=0)
        self.assertEqual(CacheDecision.MISS, result.decision)

    def test_invalid_policy_and_entry_values_fail_closed(self):
        invalid_entries = [
            CacheEntry(value="", stored_at_ms=1_000, ttl_ms=500),
            CacheEntry(value="x", stored_at_ms=-1, ttl_ms=500),
            CacheEntry(value="x", stored_at_ms=1_000, ttl_ms=0),
        ]
        for entry in invalid_entries:
            with self.subTest(entry=entry):
                with self.assertRaises(ValueError):
                    evaluate_cache_entry(entry, now_ms=2_000, max_stale_ms=300)

        for now_ms, max_stale_ms in [(-1, 300), (2_000, -1), (True, 300), (2_000, False)]:
            with self.subTest(now_ms=now_ms, max_stale_ms=max_stale_ms):
                with self.assertRaises(ValueError):
                    evaluate_cache_entry(self.entry, now_ms=now_ms, max_stale_ms=max_stale_ms)

    def test_clock_before_storage_time_is_rejected(self):
        with self.assertRaises(ValueError):
            evaluate_cache_entry(self.entry, now_ms=999, max_stale_ms=300)

    def test_successful_revalidation_replaces_stale_value_as_fresh(self):
        result = apply_revalidation_outcome(
            self.entry,
            outcome=RevalidationOutcome.SUCCESS,
            now_ms=1_700,
            max_stale_ms=300,
            refreshed_value="synthetic-reading-v2",
        )
        self.assertEqual(CacheDecision.FRESH, result.decision)
        self.assertEqual("synthetic-reading-v2", result.value)
        self.assertEqual(0, result.age_ms)
        self.assertFalse(result.revalidate)

    def test_failed_revalidation_preserves_stale_value_only_inside_budget(self):
        result = apply_revalidation_outcome(
            self.entry,
            outcome=RevalidationOutcome.FAILURE,
            now_ms=1_700,
            max_stale_ms=300,
        )
        self.assertEqual(CacheDecision.STALE, result.decision)
        self.assertEqual("synthetic-reading", result.value)
        self.assertTrue(result.revalidate)

    def test_failed_revalidation_cannot_extend_value_beyond_stale_budget(self):
        result = apply_revalidation_outcome(
            self.entry,
            outcome=RevalidationOutcome.FAILURE,
            now_ms=1_801,
            max_stale_ms=300,
        )
        self.assertEqual(CacheDecision.MISS, result.decision)
        self.assertIsNone(result.value)
        self.assertFalse(result.revalidate)

    def test_successful_revalidation_requires_a_new_value(self):
        for refreshed_value in (None, ""):
            with self.subTest(refreshed_value=refreshed_value):
                with self.assertRaises(ValueError):
                    apply_revalidation_outcome(
                        self.entry,
                        outcome=RevalidationOutcome.SUCCESS,
                        now_ms=1_700,
                        max_stale_ms=300,
                        refreshed_value=refreshed_value,
                    )

    def test_failed_revalidation_rejects_a_refreshed_value(self):
        with self.assertRaises(ValueError):
            apply_revalidation_outcome(
                self.entry,
                outcome=RevalidationOutcome.FAILURE,
                now_ms=1_700,
                max_stale_ms=300,
                refreshed_value="unexpected-value",
            )

    def test_revalidation_rejects_fresh_entries_and_invalid_outcomes(self):
        with self.assertRaises(ValueError):
            apply_revalidation_outcome(
                self.entry,
                outcome=RevalidationOutcome.SUCCESS,
                now_ms=1_400,
                max_stale_ms=300,
                refreshed_value="synthetic-reading-v2",
            )
        with self.assertRaises(ValueError):
            apply_revalidation_outcome(
                self.entry,
                outcome="success",
                now_ms=1_700,
                max_stale_ms=300,
                refreshed_value="synthetic-reading-v2",
            )


if __name__ == "__main__":
    unittest.main()
