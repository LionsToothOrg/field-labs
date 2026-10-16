import unittest

from session import InvalidRefreshToken, StaleRefreshAttempt, SyntheticSessionStore


class ConcurrentRefreshBaselineTests(unittest.TestCase):
    def setUp(self):
        self.store = SyntheticSessionStore()
        self.initial_token = self.store.current_refresh_token

    def test_single_refresh_rotates_token(self):
        attempt = self.store.begin_refresh(self.initial_token)
        result = self.store.finish_refresh_unchecked(attempt)

        self.assertEqual(result.refresh_token, "refresh-synthetic-1")
        self.assertEqual(self.store.current_refresh_token, result.refresh_token)
        self.assertEqual(self.store.generation, 1)

    def test_two_requests_can_both_pass_validation_before_either_rotates(self):
        first = self.store.begin_refresh(self.initial_token)
        second = self.store.begin_refresh(self.initial_token)

        self.assertEqual(first.observed_generation, 0)
        self.assertEqual(second.observed_generation, 0)

    def test_unchecked_concurrent_refresh_invalidates_first_response(self):
        first = self.store.begin_refresh(self.initial_token)
        second = self.store.begin_refresh(self.initial_token)

        first_result = self.store.finish_refresh_unchecked(first)
        second_result = self.store.finish_refresh_unchecked(second)

        self.assertEqual(first_result.refresh_token, "refresh-synthetic-1")
        self.assertEqual(second_result.refresh_token, "refresh-synthetic-2")
        self.assertEqual(self.store.current_refresh_token, second_result.refresh_token)

        with self.assertRaises(InvalidRefreshToken):
            self.store.begin_refresh(first_result.refresh_token)


class SerializedRefreshTests(unittest.TestCase):
    def setUp(self):
        self.store = SyntheticSessionStore()
        self.initial_token = self.store.current_refresh_token

    def test_single_owned_refresh_rotates_token(self):
        attempt = self.store.begin_refresh(self.initial_token)

        result = self.store.finish_refresh(attempt)

        self.assertEqual(result.refresh_token, "refresh-synthetic-1")
        self.assertEqual(self.store.current_refresh_token, result.refresh_token)
        self.assertEqual(self.store.generation, 1)

    def test_second_completion_from_same_generation_is_rejected(self):
        first = self.store.begin_refresh(self.initial_token)
        second = self.store.begin_refresh(self.initial_token)

        first_result = self.store.finish_refresh(first)

        with self.assertRaises(StaleRefreshAttempt):
            self.store.finish_refresh(second)

        self.assertEqual(self.store.current_refresh_token, first_result.refresh_token)
        self.assertEqual(self.store.generation, 1)

    def test_rejected_stale_completion_does_not_mutate_session(self):
        first = self.store.begin_refresh(self.initial_token)
        second = self.store.begin_refresh(self.initial_token)
        self.store.finish_refresh(first)

        token_before_rejection = self.store.current_refresh_token
        generation_before_rejection = self.store.generation

        with self.assertRaises(StaleRefreshAttempt):
            self.store.finish_refresh(second)

        self.assertEqual(self.store.current_refresh_token, token_before_rejection)
        self.assertEqual(self.store.generation, generation_before_rejection)


if __name__ == "__main__":
    unittest.main()
