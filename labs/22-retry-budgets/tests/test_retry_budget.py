import unittest

from retry_budget import (
    RetryBudget,
    RetryClassification,
    RetryDecisionOutcome,
)


class SyntheticClock:
    def __init__(self, now: float = 0.0) -> None:
        self.now = now

    def __call__(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += seconds


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
        self.assertEqual(snapshot.retries_skipped, 0)
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

    def test_non_retryable_outcome_skips_budget_without_consuming_capacity(self) -> None:
        budget = RetryBudget(ratio=0.5)
        for _ in range(4):
            budget.record_original()

        self.assertFalse(
            budget.try_acquire_for(RetryClassification.NON_RETRYABLE)
        )
        snapshot = budget.snapshot()

        self.assertEqual(snapshot.retries_skipped, 1)
        self.assertEqual(snapshot.retries_admitted, 0)
        self.assertEqual(snapshot.retries_rejected, 0)
        self.assertEqual(snapshot.retries_remaining, 2)

    def test_retryable_outcome_uses_the_same_bounded_capacity(self) -> None:
        budget = RetryBudget(ratio=0.5)
        for _ in range(2):
            budget.record_original()

        self.assertTrue(budget.try_acquire_for(RetryClassification.RETRYABLE))
        self.assertFalse(budget.try_acquire_for(RetryClassification.RETRYABLE))

        snapshot = budget.snapshot()
        self.assertEqual(snapshot.retries_admitted, 1)
        self.assertEqual(snapshot.retries_rejected, 1)
        self.assertEqual(snapshot.retries_skipped, 0)

    def test_structured_decision_reports_admission(self) -> None:
        budget = RetryBudget(ratio=0.5)
        for _ in range(4):
            budget.record_original()

        decision = budget.decide_for(RetryClassification.RETRYABLE)

        self.assertTrue(decision.admitted)
        self.assertEqual(decision.outcome, RetryDecisionOutcome.ADMITTED)
        self.assertEqual(decision.classification, RetryClassification.RETRYABLE)
        self.assertEqual(decision.retry_limit, 2)
        self.assertEqual(decision.retries_remaining, 1)
        self.assertIsNone(decision.window_started_at)

    def test_structured_decisions_distinguish_skip_from_budget_rejection(self) -> None:
        budget = RetryBudget(ratio=0.5)
        for _ in range(2):
            budget.record_original()

        skipped = budget.decide_for(RetryClassification.NON_RETRYABLE)
        admitted = budget.decide_for(RetryClassification.RETRYABLE)
        rejected = budget.decide_for(RetryClassification.RETRYABLE)

        self.assertEqual(skipped.outcome, RetryDecisionOutcome.POLICY_SKIPPED)
        self.assertFalse(skipped.admitted)
        self.assertEqual(skipped.retries_remaining, 1)
        self.assertEqual(admitted.outcome, RetryDecisionOutcome.ADMITTED)
        self.assertEqual(admitted.retries_remaining, 0)
        self.assertEqual(rejected.outcome, RetryDecisionOutcome.BUDGET_REJECTED)
        self.assertFalse(rejected.admitted)
        self.assertEqual(rejected.retries_remaining, 0)

    def test_structured_decision_includes_active_synthetic_window(self) -> None:
        clock = SyntheticClock(20.0)
        budget = RetryBudget(ratio=1, window_seconds=10, clock=clock)
        budget.record_original()

        decision = budget.decide_for(RetryClassification.RETRYABLE)

        self.assertEqual(decision.window_started_at, 20.0)
        self.assertEqual(decision.retry_limit, 1)
        self.assertEqual(decision.retries_remaining, 0)

    def test_invalid_retry_classification_is_rejected(self) -> None:
        budget = RetryBudget(ratio=0.5)

        with self.assertRaises(TypeError):
            budget.try_acquire_for("retryable")  # type: ignore[arg-type]

    def test_window_rollover_expires_old_demand_and_retry_usage(self) -> None:
        clock = SyntheticClock(100.0)
        budget = RetryBudget(ratio=0.5, window_seconds=10, clock=clock)
        for _ in range(4):
            budget.record_original()
        self.assertTrue(budget.try_acquire_retry())
        self.assertFalse(
            budget.try_acquire_for(RetryClassification.NON_RETRYABLE)
        )
        self.assertEqual(budget.snapshot().retry_limit, 2)

        clock.advance(10)
        snapshot = budget.snapshot()

        self.assertEqual(snapshot.window_started_at, 110.0)
        self.assertEqual(snapshot.originals, 0)
        self.assertEqual(snapshot.retries_admitted, 0)
        self.assertEqual(snapshot.retries_rejected, 0)
        self.assertEqual(snapshot.retries_skipped, 0)
        self.assertEqual(snapshot.retry_limit, 0)
        self.assertFalse(budget.try_acquire_retry())

    def test_window_does_not_roll_before_boundary(self) -> None:
        clock = SyntheticClock()
        budget = RetryBudget(ratio=0.5, window_seconds=10, clock=clock)
        for _ in range(4):
            budget.record_original()

        clock.advance(9.999)

        self.assertEqual(budget.snapshot().originals, 4)
        self.assertEqual(budget.snapshot().window_started_at, 0.0)

    def test_rollover_advances_across_multiple_idle_windows(self) -> None:
        clock = SyntheticClock(5.0)
        budget = RetryBudget(ratio=0.5, window_seconds=10, clock=clock)
        budget.record_original()

        clock.advance(35)
        snapshot = budget.snapshot()

        self.assertEqual(snapshot.window_started_at, 35.0)
        self.assertEqual(snapshot.originals, 0)

    def test_windowed_budget_rejects_backward_clock(self) -> None:
        clock = SyntheticClock(10.0)
        budget = RetryBudget(ratio=0.5, window_seconds=5, clock=clock)
        clock.now = 9.0

        with self.assertRaises(ValueError):
            budget.snapshot()

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
        with self.assertRaises(TypeError):
            RetryBudget(ratio=0.2, window_seconds=10)
        with self.assertRaises(ValueError):
            RetryBudget(ratio=0.2, window_seconds=0, clock=SyntheticClock())
        with self.assertRaises(ValueError):
            RetryBudget(ratio=0.2, clock=SyntheticClock())


if __name__ == "__main__":
    unittest.main()
