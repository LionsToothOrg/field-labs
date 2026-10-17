import unittest

from circuit_breaker import CircuitBreaker, CircuitState


class CircuitBreakerTests(unittest.TestCase):
    def test_opens_after_consecutive_failure_threshold(self):
        breaker = CircuitBreaker(failure_threshold=2, recovery_timeout_seconds=30)

        self.assertTrue(breaker.before_call(now=0).allowed)
        breaker.record_failure(now=1)
        self.assertEqual(breaker.state, CircuitState.CLOSED)

        self.assertTrue(breaker.before_call(now=2).allowed)
        breaker.record_failure(now=3)

        self.assertEqual(breaker.state, CircuitState.OPEN)
        decision = breaker.before_call(now=10)
        self.assertFalse(decision.allowed)
        self.assertEqual(decision.reason, "recovery_timeout_pending")

    def test_success_resets_consecutive_failures(self):
        breaker = CircuitBreaker(failure_threshold=2, recovery_timeout_seconds=30)

        breaker.record_failure(now=1)
        breaker.record_success()
        breaker.record_failure(now=2)

        self.assertEqual(breaker.state, CircuitState.CLOSED)
        self.assertEqual(breaker.consecutive_failures, 1)

    def test_allows_one_probe_after_recovery_timeout(self):
        breaker = CircuitBreaker(failure_threshold=1, recovery_timeout_seconds=10)
        breaker.record_failure(now=5)

        probe = breaker.before_call(now=15)
        second = breaker.before_call(now=15)

        self.assertTrue(probe.allowed)
        self.assertEqual(probe.reason, "probe_allowed")
        self.assertFalse(second.allowed)
        self.assertEqual(second.reason, "probe_in_flight")

    def test_successful_probe_closes_circuit(self):
        breaker = CircuitBreaker(failure_threshold=1, recovery_timeout_seconds=10)
        breaker.record_failure(now=5)
        breaker.before_call(now=15)

        breaker.record_success()

        self.assertEqual(breaker.state, CircuitState.CLOSED)
        self.assertTrue(breaker.before_call(now=16).allowed)

    def test_failed_probe_reopens_and_restarts_timeout(self):
        breaker = CircuitBreaker(failure_threshold=1, recovery_timeout_seconds=10)
        breaker.record_failure(now=5)
        breaker.before_call(now=15)

        breaker.record_failure(now=16)

        self.assertEqual(breaker.state, CircuitState.OPEN)
        self.assertFalse(breaker.before_call(now=25).allowed)
        self.assertTrue(breaker.before_call(now=26).allowed)

    def test_rejects_invalid_configuration(self):
        with self.assertRaises(ValueError):
            CircuitBreaker(failure_threshold=0, recovery_timeout_seconds=1)
        with self.assertRaises(ValueError):
            CircuitBreaker(failure_threshold=1, recovery_timeout_seconds=-1)


if __name__ == "__main__":
    unittest.main()
