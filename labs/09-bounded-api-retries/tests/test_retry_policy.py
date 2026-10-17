import unittest

from retry_policy import AttemptResult, RetryDecision, plan_retries


class RetryPolicyTests(unittest.TestCase):
    def test_retryable_failures_back_off_until_success(self):
        result = plan_retries(
            [AttemptResult(503), AttemptResult(502), AttemptResult(200)],
            base_delay_seconds=2,
        )

        self.assertEqual(
            [
                RetryDecision(1, 503, "retry", 2),
                RetryDecision(2, 502, "retry", 4),
                RetryDecision(3, 200, "succeed", None),
            ],
            result,
        )

    def test_non_retryable_failure_stops_immediately(self):
        result = plan_retries([AttemptResult(400), AttemptResult(200)])

        self.assertEqual([RetryDecision(1, 400, "stop", None)], result)

    def test_attempt_budget_exhausts_without_extra_retry(self):
        result = plan_retries(
            [AttemptResult(503), AttemptResult(503), AttemptResult(503), AttemptResult(200)],
            max_attempts=3,
        )

        self.assertEqual(
            [
                RetryDecision(1, 503, "retry", 1),
                RetryDecision(2, 503, "retry", 2),
                RetryDecision(3, 503, "exhaust", None),
            ],
            result,
        )

    def test_retry_after_extends_shorter_local_backoff(self):
        result = plan_retries(
            [AttemptResult(429, retry_after_seconds=12), AttemptResult(200)],
            base_delay_seconds=2,
        )

        self.assertEqual(RetryDecision(1, 429, "retry", 12), result[0])

    def test_retry_after_does_not_shorten_local_backoff(self):
        result = plan_retries(
            [AttemptResult(503), AttemptResult(429, retry_after_seconds=1), AttemptResult(200)],
            base_delay_seconds=3,
        )

        self.assertEqual(RetryDecision(2, 429, "retry", 6), result[1])

    def test_backoff_is_capped(self):
        result = plan_retries(
            [AttemptResult(503), AttemptResult(503), AttemptResult(503), AttemptResult(200)],
            base_delay_seconds=10,
            max_delay_seconds=15,
        )

        self.assertEqual([10, 15, 15], [item.delay_seconds for item in result[:3]])

    def test_invalid_retry_after_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "retry_after_seconds"):
            plan_retries([AttemptResult(429, retry_after_seconds=-1)])


if __name__ == "__main__":
    unittest.main()
