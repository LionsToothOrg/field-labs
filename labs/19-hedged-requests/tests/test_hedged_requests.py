import unittest

from hedged_requests import (
    Completion,
    HedgeDecision,
    Request,
    plan_hedge,
    resolve_acceptable_race,
    resolve_race,
)


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


class HedgeRaceTests(unittest.TestCase):
    def test_primary_wins_admitted_race(self):
        decision = plan_hedge(Request("req-primary-win", "GET", 90, 50))
        outcome = resolve_race(decision, primary_completed_at_ms=90, hedge_completed_at_ms=110)
        self.assertEqual("primary", outcome.winner)
        self.assertEqual("hedge", outcome.loser)
        self.assertEqual(90, outcome.completed_at_ms)
        self.assertTrue(outcome.cancellation_requested)
        self.assertTrue(outcome.loser_work_may_have_started)

    def test_hedge_wins_admitted_race(self):
        decision = plan_hedge(Request("req-hedge-win", "GET", 140, 50))
        outcome = resolve_race(decision, primary_completed_at_ms=140, hedge_completed_at_ms=85)
        self.assertEqual("hedge", outcome.winner)
        self.assertEqual("primary", outcome.loser)
        self.assertEqual(85, outcome.completed_at_ms)
        self.assertTrue(outcome.cancellation_requested)
        self.assertTrue(outcome.loser_work_may_have_started)

    def test_equal_completion_times_choose_primary_deterministically(self):
        decision = plan_hedge(Request("req-tie", "GET", 100, 50))
        outcome = resolve_race(decision, primary_completed_at_ms=100, hedge_completed_at_ms=100)
        self.assertEqual("primary", outcome.winner)
        self.assertEqual("hedge", outcome.loser)

    def test_non_hedged_request_has_no_loser_or_cancellation(self):
        decision = plan_hedge(Request("req-single", "GET", 40, 50))
        outcome = resolve_race(decision, primary_completed_at_ms=40)
        self.assertEqual("primary", outcome.winner)
        self.assertIsNone(outcome.loser)
        self.assertFalse(outcome.cancellation_requested)
        self.assertFalse(outcome.loser_work_may_have_started)

    def test_non_hedged_request_rejects_hedge_completion(self):
        decision = plan_hedge(Request("req-extra", "POST", 100, 50))
        with self.assertRaisesRegex(ValueError, "admitted hedge"):
            resolve_race(decision, primary_completed_at_ms=100, hedge_completed_at_ms=80)

    def test_admitted_hedge_requires_hedge_completion(self):
        decision = plan_hedge(Request("req-missing", "GET", 100, 50))
        with self.assertRaisesRegex(ValueError, "required"):
            resolve_race(decision, primary_completed_at_ms=100)

    def test_negative_completion_time_is_rejected(self):
        decision = plan_hedge(Request("req-negative", "GET", 100, 50))
        with self.assertRaisesRegex(ValueError, "primary_completed_at_ms"):
            resolve_race(decision, primary_completed_at_ms=-1, hedge_completed_at_ms=80)

    def test_inconsistent_attempt_count_is_rejected(self):
        decision = HedgeDecision("req-invalid", True, 1, "hedge_started")
        with self.assertRaisesRegex(ValueError, "two attempts"):
            resolve_race(decision, primary_completed_at_ms=100, hedge_completed_at_ms=80)


class AcceptableCompletionTests(unittest.TestCase):
    def test_first_acceptable_completion_is_selected_and_later_attempt_cancelled(self):
        decision = plan_hedge(Request("req-accepted-first", "GET", 120, 50))
        outcome = resolve_acceptable_race(
            decision, Completion(80, True), Completion(100, True)
        )
        self.assertEqual("primary", outcome.selected)
        self.assertTrue(outcome.acceptable)
        self.assertTrue(outcome.cancellation_requested)

    def test_early_rejected_primary_does_not_cancel_later_acceptable_hedge(self):
        decision = plan_hedge(Request("req-reject-primary", "GET", 120, 50))
        outcome = resolve_acceptable_race(
            decision, Completion(70, False), Completion(90, True)
        )
        self.assertEqual("hedge", outcome.selected)
        self.assertEqual(90, outcome.completed_at_ms)
        self.assertTrue(outcome.acceptable)
        self.assertFalse(outcome.cancellation_requested)

    def test_early_rejected_hedge_does_not_cancel_later_acceptable_primary(self):
        decision = plan_hedge(Request("req-reject-hedge", "GET", 120, 50))
        outcome = resolve_acceptable_race(
            decision, Completion(100, True), Completion(75, False)
        )
        self.assertEqual("primary", outcome.selected)
        self.assertTrue(outcome.acceptable)
        self.assertFalse(outcome.cancellation_requested)

    def test_two_rejected_completions_wait_for_terminal_result(self):
        decision = plan_hedge(Request("req-both-rejected", "GET", 120, 50))
        outcome = resolve_acceptable_race(
            decision, Completion(70, False), Completion(90, False)
        )
        self.assertEqual("hedge", outcome.selected)
        self.assertFalse(outcome.acceptable)
        self.assertFalse(outcome.cancellation_requested)

    def test_equal_time_prefers_acceptable_result_over_primary_tie_break(self):
        decision = plan_hedge(Request("req-equal-quality", "GET", 120, 50))
        outcome = resolve_acceptable_race(
            decision, Completion(90, False), Completion(90, True)
        )
        self.assertEqual("hedge", outcome.selected)
        self.assertTrue(outcome.acceptable)
        self.assertFalse(outcome.cancellation_requested)

    def test_non_hedged_result_preserves_acceptability(self):
        decision = plan_hedge(Request("req-single-quality", "GET", 40, 50))
        outcome = resolve_acceptable_race(decision, Completion(40, False))
        self.assertEqual("primary", outcome.selected)
        self.assertFalse(outcome.acceptable)
        self.assertIsNone(outcome.other_attempt)

    def test_acceptable_race_rejects_missing_hedge_completion(self):
        decision = plan_hedge(Request("req-quality-missing", "GET", 120, 50))
        with self.assertRaisesRegex(ValueError, "required"):
            resolve_acceptable_race(decision, Completion(100, True))

    def test_acceptable_race_rejects_negative_completion_time(self):
        decision = plan_hedge(Request("req-quality-negative", "GET", 120, 50))
        with self.assertRaisesRegex(ValueError, "hedge completion time"):
            resolve_acceptable_race(
                decision, Completion(100, True), Completion(-1, True)
            )


if __name__ == "__main__":
    unittest.main()
