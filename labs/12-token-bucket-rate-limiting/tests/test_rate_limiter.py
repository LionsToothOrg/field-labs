import unittest

from rate_limiter import TokenBucket


class TokenBucketTests(unittest.TestCase):
    def test_starts_full_and_allows_within_capacity(self):
        bucket = TokenBucket(capacity=3, refill_rate=1)
        decision = bucket.allow(now=0, tokens=2)
        self.assertTrue(decision.allowed)
        self.assertEqual(decision.reason, "allowed")
        self.assertEqual(decision.retry_after, 0.0)
        self.assertEqual(bucket.snapshot(), (1.0, 3.0, 0.0))

    def test_can_start_with_partial_capacity(self):
        bucket = TokenBucket(capacity=5, refill_rate=2, start_time=10, initial_tokens=1.5)
        self.assertEqual(bucket.snapshot(), (1.5, 5.0, 10.0))
        decision = bucket.allow(now=10.5, tokens=2.5)
        self.assertTrue(decision.allowed)
        self.assertEqual(bucket.snapshot(), (0.0, 5.0, 10.5))

    def test_can_start_empty_and_refill_from_start_time(self):
        bucket = TokenBucket(capacity=3, refill_rate=2, start_time=4, initial_tokens=0)
        rejected = bucket.allow(now=4, tokens=1)
        self.assertFalse(rejected.allowed)
        self.assertEqual(rejected.retry_after, 0.5)
        admitted = bucket.allow(now=4.5, tokens=1)
        self.assertTrue(admitted.allowed)

    def test_inspect_projects_refill_without_mutating_state(self):
        bucket = TokenBucket(capacity=5, refill_rate=2, initial_tokens=1)
        before = bucket.snapshot()
        state = bucket.inspect(now=1.5)
        self.assertEqual((state.tokens, state.capacity, state.as_of), (4.0, 5.0, 1.5))
        self.assertEqual(bucket.snapshot(), before)

        decision = bucket.allow(now=1.5, tokens=4)
        self.assertTrue(decision.allowed)
        self.assertEqual(bucket.snapshot(), (0.0, 5.0, 1.5))

    def test_inspect_caps_projection_at_capacity(self):
        bucket = TokenBucket(capacity=3, refill_rate=2, initial_tokens=1)
        state = bucket.inspect(now=10)
        self.assertEqual(state.tokens, 3.0)
        self.assertEqual(bucket.snapshot(), (1.0, 3.0, 0.0))

    def test_inspect_rejects_clock_regression_without_mutating_state(self):
        bucket = TokenBucket(capacity=3, refill_rate=1, start_time=5)
        before = bucket.snapshot()
        with self.assertRaisesRegex(ValueError, "backward"):
            bucket.inspect(now=4.5)
        self.assertEqual(bucket.snapshot(), before)

    def test_rejects_request_when_tokens_are_exhausted(self):
        bucket = TokenBucket(capacity=2, refill_rate=1)
        bucket.allow(now=0, tokens=2)
        decision = bucket.allow(now=0, tokens=1)
        self.assertFalse(decision.allowed)
        self.assertEqual(decision.reason, "insufficient_tokens")
        self.assertEqual(decision.retry_after, 1.0)
        self.assertEqual(bucket.snapshot(), (0.0, 2.0, 0.0))

    def test_retry_after_reflects_weighted_token_deficit(self):
        bucket = TokenBucket(capacity=5, refill_rate=2)
        bucket.allow(now=0, tokens=4)
        decision = bucket.allow(now=0, tokens=3)
        self.assertFalse(decision.allowed)
        self.assertEqual(decision.retry_after, 1.0)
        self.assertEqual(bucket.snapshot(), (1.0, 5.0, 0.0))

    def test_retry_after_request_succeeds_when_deficit_has_refilled(self):
        bucket = TokenBucket(capacity=3, refill_rate=2)
        bucket.allow(now=0, tokens=3)
        rejected = bucket.allow(now=0, tokens=1)
        admitted = bucket.allow(now=rejected.retry_after, tokens=1)
        self.assertTrue(admitted.allowed)
        self.assertEqual(admitted.retry_after, 0.0)

    def test_request_larger_than_capacity_is_not_retryable(self):
        bucket = TokenBucket(capacity=3, refill_rate=2)
        before = bucket.snapshot()
        decision = bucket.allow(now=0, tokens=4)
        self.assertFalse(decision.allowed)
        self.assertEqual(decision.reason, "request_exceeds_capacity")
        self.assertIsNone(decision.retry_after)
        self.assertEqual(bucket.snapshot(), before)

    def test_refills_from_elapsed_time(self):
        bucket = TokenBucket(capacity=4, refill_rate=2)
        bucket.allow(now=0, tokens=4)
        decision = bucket.allow(now=1.5, tokens=3)
        self.assertTrue(decision.allowed)
        self.assertEqual(bucket.snapshot(), (0.0, 4.0, 1.5))

    def test_refill_is_capped_at_capacity(self):
        bucket = TokenBucket(capacity=3, refill_rate=2)
        bucket.allow(now=0, tokens=2)
        bucket.allow(now=10, tokens=1)
        self.assertEqual(bucket.snapshot(), (2.0, 3.0, 10.0))

    def test_rejected_request_does_not_consume_available_tokens(self):
        bucket = TokenBucket(capacity=3, refill_rate=1)
        bucket.allow(now=0, tokens=2)
        decision = bucket.allow(now=0, tokens=2)
        self.assertFalse(decision.allowed)
        self.assertEqual(bucket.snapshot(), (1.0, 3.0, 0.0))

    def test_rejects_clock_regression_without_mutating_state(self):
        bucket = TokenBucket(capacity=3, refill_rate=1, start_time=5)
        bucket.allow(now=6, tokens=2)
        before = bucket.snapshot()
        with self.assertRaisesRegex(ValueError, "backward"):
            bucket.allow(now=5.5)
        self.assertEqual(bucket.snapshot(), before)

    def test_rejects_invalid_configuration(self):
        for capacity, refill_rate in (
            (0, 1),
            (-1, 1),
            (True, 1),
            (1, 0),
            (1, float("inf")),
        ):
            with self.subTest(capacity=capacity, refill_rate=refill_rate), self.assertRaises(ValueError):
                TokenBucket(capacity=capacity, refill_rate=refill_rate)

    def test_rejects_invalid_initial_tokens(self):
        for initial_tokens in (-1, True, float("inf"), float("nan"), 4):
            with self.subTest(initial_tokens=initial_tokens), self.assertRaises(ValueError):
                TokenBucket(capacity=3, refill_rate=1, initial_tokens=initial_tokens)

    def test_rejects_invalid_requests_without_mutating_state(self):
        bucket = TokenBucket(capacity=3, refill_rate=1)
        for now, tokens in (
            (float("nan"), 1),
            (0, 0),
            (0, -1),
            (0, True),
            (0, float("inf")),
        ):
            before = bucket.snapshot()
            with self.subTest(now=now, tokens=tokens), self.assertRaises(ValueError):
                bucket.allow(now=now, tokens=tokens)
            self.assertEqual(bucket.snapshot(), before)


if __name__ == "__main__":
    unittest.main()
