import unittest

from deadline_budget import budget_downstream_call, budget_sequential_calls


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

    def test_sequential_calls_recompute_from_shared_deadline(self):
        calls = budget_sequential_calls(
            start=0,
            deadline=10,
            durations=(4, 4, 4),
            max_timeout=6,
            reserve=1,
        )

        self.assertEqual([call.started_at for call in calls], [0, 4, 8])
        self.assertEqual([call.budget.timeout for call in calls], [6, 5, 1])
        self.assertEqual([call.budget.remaining for call in calls], [10, 6, 2])

    def test_sequential_calls_stop_after_budget_is_exhausted(self):
        calls = budget_sequential_calls(
            start=0,
            deadline=5,
            durations=(3, 2, 1),
            max_timeout=4,
            reserve=2,
        )

        self.assertEqual(len(calls), 2)
        self.assertTrue(calls[0].budget.allowed)
        self.assertFalse(calls[1].budget.allowed)
        self.assertEqual(calls[1].budget.reason, "deadline_exhausted")

    def test_sequential_call_duration_is_capped_by_granted_timeout(self):
        calls = budget_sequential_calls(
            start=0,
            deadline=6,
            durations=(10, 1),
            max_timeout=4,
            reserve=1,
        )

        self.assertEqual(calls[1].started_at, 4)
        self.assertEqual(calls[1].budget.timeout, 1)

    def test_sequential_calls_reject_invalid_duration(self):
        for duration in (-1, float("inf"), True):
            with self.subTest(duration=duration):
                with self.assertRaises((TypeError, ValueError)):
                    budget_sequential_calls(
                        start=0,
                        deadline=10,
                        durations=(duration,),
                        max_timeout=2,
                    )


if __name__ == "__main__":
    unittest.main()
