import unittest

from retry_budget import RetryBudget


class RetryBudgetTests(unittest.TestCase):
    def test_retries_are_bounded_by_original_attempts(self) -> None:
        budget = RetryBudget(ratio=0.25)
        for _ in range(8):
            budget.record_original()

        self.assertTrue(budget.try_acquire_retry())
        self.assertTrue(budget.try_acquire_retry())
        self.assertFalse(budget.try_acquire_retry())

        snapshot = budget.snapshot()
        self.assertEqual(snapshot.retry_limit, 2)
        self.assertEqual(snapshot.retries_admitted, 2)
        self.assertEqual(snapshot.retries_rejected, 1)
        self.assertEqual(snapshot.retries_remaining, 0)

    def test_budget_grows_as_original_attempts_accumulate(self) -> None:
        budget = RetryBudget(ratio=0.5)
        for _ in range(2):
            budget.record_original()

        self.assertTrue(budget.try_acquire_retry())
        self.assertFalse(budget.try_acquire_retry())

        for _ in range(2):
            budget.record_original()

        self.assertTrue(budget.try_acquire_retry())
        self.assertEqual(budget.snapshot().retry_limit, 2)

    def test_minimum_retry_allowance_is_explicit(self) -> None:
        budget = RetryBudget(ratio=0.1, minimum_retries=1)

        self.assertTrue(budget.try_acquire_retry())
        self.assertFalse(budget.try_acquire_retry())
        self.assertEqual(budget.snapshot().retry_limit, 1)

    def test_zero_ratio_rejects_retries_without_minimum(self) -> None:
        budget = RetryBudget(ratio=0)
        budget.record_original()

        self.assertFalse(budget.try_acquire_retry())
        self.assertEqual(budget.snapshot().retries_rejected, 1)

    def test_fractional_limit_rounds_down(self) -> None:
        budget = RetryBudget(ratio=0.25)
        for _ in range(7):
            budget.record_original()

        self.assertEqual(budget.snapshot().retry_limit, 1)

    def test_invalid_configuration_is_rejected(self) -> None:
        for ratio in (-0.1, 1.1, float("inf"), float("nan")):
            with self.subTest(ratio=ratio):
                with self.assertRaises(ValueError):
                    RetryBudget(ratio=ratio)

        with self.assertRaises(ValueError):
            RetryBudget(ratio=0.2, minimum_retries=-1)
        with self.assertRaises(TypeError):
            RetryBudget(ratio=True)
        with self.assertRaises(TypeError):
            RetryBudget(ratio=0.2, minimum_retries=True)


if __name__ == "__main__":
    unittest.main()
