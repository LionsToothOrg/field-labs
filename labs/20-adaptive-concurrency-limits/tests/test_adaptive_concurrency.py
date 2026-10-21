import unittest

from adaptive_concurrency import LimitPolicy, Sample, admit, update_limit


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


if __name__ == "__main__":
    unittest.main()
