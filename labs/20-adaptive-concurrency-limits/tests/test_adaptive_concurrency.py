import unittest

from adaptive_concurrency import (
    LimitPolicy,
    Sample,
    admit,
    run_feedback_trace,
    update_limit,
    update_limit_from_window,
)


class AdaptiveConcurrencyTests(unittest.TestCase):
    def setUp(self):
        self.policy = LimitPolicy(minimum=2, maximum=10)

    def test_healthy_sample_increases_limit(self):
        decision = update_limit(4, Sample(40, 50), self.policy)
        self.assertEqual((decision.next_limit, decision.reason), (5, "healthy"))

    def test_target_boundary_is_healthy(self):
        self.assertEqual(update_limit(4, Sample(50, 50), self.policy).next_limit, 5)

    def test_increase_is_capped_at_maximum(self):
        self.assertEqual(update_limit(10, Sample(20, 50), self.policy).next_limit, 10)

    def test_high_latency_reduces_limit(self):
        decision = update_limit(8, Sample(51, 50), self.policy)
        self.assertEqual((decision.next_limit, decision.reason), (4, "latency_above_target"))

    def test_explicit_overload_reduces_even_with_low_latency(self):
        decision = update_limit(8, Sample(10, 50, overloaded=True), self.policy)
        self.assertEqual((decision.next_limit, decision.reason), (4, "overload"))

    def test_decrease_is_floored_at_minimum(self):
        self.assertEqual(update_limit(2, Sample(90, 50), self.policy).next_limit, 2)

    def test_admission_stops_at_limit(self):
        self.assertTrue(admit(3, 4))
        self.assertFalse(admit(4, 4))

    def test_invalid_current_limit_fails(self):
        with self.assertRaises(ValueError):
            update_limit(11, Sample(10, 50), self.policy)

    def test_invalid_sample_fails(self):
        with self.assertRaises(ValueError):
            Sample(-1, 50)
        with self.assertRaises(ValueError):
            Sample(1, 0)

    def test_invalid_policy_fails(self):
        with self.assertRaises(ValueError):
            LimitPolicy(0, 10)
        with self.assertRaises(ValueError):
            LimitPolicy(2, 1)
        with self.assertRaises(ValueError):
            LimitPolicy(2, 10, decrease_ratio=1.0)

    def test_healthy_window_increases_once(self):
        decision = update_limit_from_window(
            4, [Sample(40, 50), Sample(45, 50), Sample(50, 50)], self.policy
        )
        self.assertEqual((decision.next_limit, decision.reason), (5, "window_healthy"))

    def test_isolated_slow_sample_does_not_force_decrease_when_mean_is_healthy(self):
        decision = update_limit_from_window(
            6, [Sample(20, 50), Sample(80, 50), Sample(20, 50)], self.policy
        )
        self.assertEqual((decision.next_limit, decision.reason), (7, "window_healthy"))

    def test_slow_window_reduces_once(self):
        decision = update_limit_from_window(
            8, [Sample(60, 50), Sample(55, 50), Sample(50, 50)], self.policy
        )
        self.assertEqual(
            (decision.next_limit, decision.reason), (4, "window_latency_above_target")
        )

    def test_window_mean_at_target_is_healthy(self):
        decision = update_limit_from_window(
            4, [Sample(40, 50), Sample(60, 50)], self.policy
        )
        self.assertEqual((decision.next_limit, decision.reason), (5, "window_healthy"))

    def test_any_overload_signal_reduces_window(self):
        decision = update_limit_from_window(
            8,
            [Sample(10, 50), Sample(10, 50, overloaded=True), Sample(10, 50)],
            self.policy,
        )
        self.assertEqual((decision.next_limit, decision.reason), (4, "window_overload"))

    def test_empty_window_fails(self):
        with self.assertRaises(ValueError):
            update_limit_from_window(4, [], self.policy)

    def test_mixed_targets_fail(self):
        with self.assertRaises(ValueError):
            update_limit_from_window(4, [Sample(20, 50), Sample(20, 60)], self.policy)

    def test_feedback_trace_carries_limit_between_windows(self):
        trace = run_feedback_trace(
            4,
            [
                [Sample(30, 50), Sample(40, 50)],
                [Sample(70, 50), Sample(60, 50)],
                [Sample(20, 50), Sample(30, 50)],
            ],
            self.policy,
        )
        self.assertEqual(trace.initial_limit, 4)
        self.assertEqual(trace.final_limit, 3)
        self.assertEqual(
            [(d.previous_limit, d.next_limit, d.reason) for d in trace.decisions],
            [
                (4, 5, "window_healthy"),
                (5, 2, "window_latency_above_target"),
                (2, 3, "window_healthy"),
            ],
        )

    def test_feedback_trace_preserves_bounds_across_repeated_windows(self):
        trace = run_feedback_trace(
            9,
            [
                [Sample(10, 50)],
                [Sample(10, 50)],
                [Sample(10, 50)],
            ],
            self.policy,
        )
        self.assertEqual([d.next_limit for d in trace.decisions], [10, 10, 10])
        self.assertEqual(trace.final_limit, 10)

    def test_feedback_trace_stops_on_invalid_window(self):
        with self.assertRaises(ValueError):
            run_feedback_trace(
                4,
                [[Sample(20, 50)], [], [Sample(20, 50)]],
                self.policy,
            )

    def test_empty_feedback_trace_fails(self):
        with self.assertRaises(ValueError):
            run_feedback_trace(4, [], self.policy)


if __name__ == "__main__":
    unittest.main()
