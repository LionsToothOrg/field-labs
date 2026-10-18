import unittest

from deadline_budget import budget_downstream_call


class DeadlineBudgetTests(unittest.TestCase):
    def test_caps_call_at_configured_maximum(self):
        budget = budget_downstream_call(
            now=10, deadline=30, max_timeout=5, reserve=2
        )
        self.assertTrue(budget.allowed)
        self.assertEqual(budget.timeout, 5)
        self.assertEqual(budget.remaining, 20)

    def test_shrinks_timeout_to_preserve_reserve(self):
        budget = budget_downstream_call(
            now=10, deadline=14, max_timeout=10, reserve=1.5
        )
        self.assertTrue(budget.allowed)
        self.assertEqual(budget.timeout, 2.5)

    def test_rejects_when_only_reserved_time_remains(self):
        budget = budget_downstream_call(
            now=10, deadline=12, max_timeout=5, reserve=2
        )
        self.assertFalse(budget.allowed)
        self.assertIsNone(budget.timeout)
        self.assertEqual(budget.reason, "deadline_exhausted")

    def test_rejects_expired_deadline(self):
        budget = budget_downstream_call(
            now=10, deadline=9, max_timeout=5, reserve=0
        )
        self.assertFalse(budget.allowed)
        self.assertEqual(budget.remaining, 0)

    def test_rejects_invalid_configuration(self):
        invalid = (
            {"now": 0, "deadline": 10, "max_timeout": 0, "reserve": 0},
            {"now": 0, "deadline": 10, "max_timeout": 1, "reserve": -1},
            {"now": float("inf"), "deadline": 10, "max_timeout": 1, "reserve": 0},
            {"now": True, "deadline": 10, "max_timeout": 1, "reserve": 0},
        )
        for scenario in invalid:
            with self.subTest(scenario=scenario):
                with self.assertRaises((TypeError, ValueError)):
                    budget_downstream_call(**scenario)


if __name__ == "__main__":
    unittest.main()
