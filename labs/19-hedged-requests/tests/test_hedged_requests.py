import unittest

from hedged_requests import Request, plan_hedge


class HedgeAdmissionTests(unittest.TestCase):
    def test_primary_completion_before_threshold_avoids_hedge(self):
        decision = plan_hedge(Request("req-early", "GET", 40, 50))
        self.assertFalse(decision.hedge_started)
        self.assertEqual(1, decision.attempt_count)
        self.assertEqual("primary_completed", decision.reason)

    def test_primary_completion_at_threshold_avoids_hedge(self):
        decision = plan_hedge(Request("req-boundary", "GET", 50, 50))
        self.assertFalse(decision.hedge_started)
        self.assertEqual("primary_completed", decision.reason)

    def test_slow_safe_read_starts_exactly_one_hedge(self):
        decision = plan_hedge(Request("req-slow", "GET", 51, 50))
        self.assertTrue(decision.hedge_started)
        self.assertEqual(2, decision.attempt_count)
        self.assertEqual("hedge_started", decision.reason)

    def test_replay_safe_method_is_case_normalized(self):
        decision = plan_hedge(Request("req-head", " head ", 80, 50))
        self.assertTrue(decision.hedge_started)
        self.assertEqual(2, decision.attempt_count)

    def test_slow_mutation_is_not_hedged(self):
        decision = plan_hedge(Request("req-write", "POST", 100, 50))
        self.assertFalse(decision.hedge_started)
        self.assertEqual(1, decision.attempt_count)
        self.assertEqual("unsafe_method", decision.reason)

    def test_empty_request_id_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "request_id"):
            plan_hedge(Request("  ", "GET", 100, 50))

    def test_empty_method_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "method"):
            plan_hedge(Request("req-method", "  ", 100, 50))

    def test_negative_latency_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "primary_latency_ms"):
            plan_hedge(Request("req-latency", "GET", -1, 50))

    def test_non_positive_threshold_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "hedge_after_ms"):
            plan_hedge(Request("req-threshold", "GET", 10, 0))


if __name__ == "__main__":
    unittest.main()
