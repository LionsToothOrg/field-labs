import unittest

from rate_limiter import TokenBucket


class TokenBucketPreviewTests(unittest.TestCase):
    def test_preview_projects_admission_without_mutating_state(self):
        bucket = TokenBucket(capacity=5, refill_rate=2, initial_tokens=1)
        before = bucket.snapshot()

        decision = bucket.preview(now=1.5, tokens=3)

        self.assertTrue(decision.allowed)
        self.assertEqual(decision.remaining, 1.0)
        self.assertEqual(decision.retry_after, 0.0)
        self.assertEqual(bucket.snapshot(), before)

    def test_preview_reports_retry_delay_without_mutating_state(self):
        bucket = TokenBucket(capacity=5, refill_rate=2, initial_tokens=1)
        before = bucket.snapshot()

        decision = bucket.preview(now=0.5, tokens=4)

        self.assertFalse(decision.allowed)
        self.assertEqual(decision.reason, "insufficient_tokens")
        self.assertEqual(decision.retry_after, 1.0)
        self.assertEqual(bucket.snapshot(), before)

    def test_preview_marks_oversized_request_as_non_retryable(self):
        bucket = TokenBucket(capacity=3, refill_rate=1)
        before = bucket.snapshot()

        decision = bucket.preview(now=2, tokens=4)

        self.assertFalse(decision.allowed)
        self.assertEqual(decision.reason, "request_exceeds_capacity")
        self.assertIsNone(decision.retry_after)
        self.assertEqual(bucket.snapshot(), before)

    def test_preview_rejects_invalid_input_without_mutating_state(self):
        bucket = TokenBucket(capacity=3, refill_rate=1, start_time=5)
        before = bucket.snapshot()

        for now, tokens in ((4, 1), (5, 0), (5, True), (float("nan"), 1)):
            with self.subTest(now=now, tokens=tokens), self.assertRaises(ValueError):
                bucket.preview(now=now, tokens=tokens)
            self.assertEqual(bucket.snapshot(), before)


if __name__ == "__main__":
    unittest.main()
