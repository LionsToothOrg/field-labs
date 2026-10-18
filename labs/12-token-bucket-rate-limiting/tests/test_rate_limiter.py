import unittest

from rate_limiter import TokenBucket


class TokenBucketTests(unittest.TestCase):
    def test_starts_full_and_allows_within_capacity(self):
        bucket = TokenBucket(capacity=3, refill_rate=1)
        decision = bucket.allow(now=0, tokens=2)
        self.assertTrue(decision.allowed)
        self.assertEqual(decision.reason, "allowed")
        self.assertEqual(bucket.snapshot(), (1.0, 3.0, 0.0))

    def test_rejects_request_when_tokens_are_exhausted(self):
        bucket = TokenBucket(capacity=2, refill_rate=1)
        bucket.allow(now=0, tokens=2)
        decision = bucket.allow(now=0, tokens=1)
        self.assertFalse(decision.allowed)
        self.assertEqual(decision.reason, "insufficient_tokens")
        self.assertEqual(bucket.snapshot(), (0.0, 2.0, 0.0))

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
