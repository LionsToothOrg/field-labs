import unittest

from session import (
    InMemorySessionStore,
    InvalidRefreshToken,
    StaleRefreshAttempt,
    SyntheticSessionStore,
)


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


class RefreshRecoveryTests(unittest.TestCase):
    def setUp(self):
        self.store = SyntheticSessionStore()
        self.initial_token = self.store.current_refresh_token

    def test_owned_attempt_reports_that_it_rotated_state(self):
        attempt = self.store.begin_refresh(self.initial_token)

        resolution = self.store.finish_refresh_or_recover(attempt)

        self.assertTrue(resolution.rotated)
        self.assertEqual(resolution.result.refresh_token, "refresh-synthetic-1")
        self.assertEqual(self.store.generation, 1)

    def test_losing_attempt_reuses_winning_state_without_second_rotation(self):
        first = self.store.begin_refresh(self.initial_token)
        second = self.store.begin_refresh(self.initial_token)

        winner = self.store.finish_refresh_or_recover(first)
        loser = self.store.finish_refresh_or_recover(second)

        self.assertTrue(winner.rotated)
        self.assertFalse(loser.rotated)
        self.assertEqual(loser.result, winner.result)
        self.assertEqual(self.store.current_refresh_token, winner.result.refresh_token)
        self.assertEqual(self.store.generation, 1)

    def test_attempt_cannot_recover_after_session_advances_again(self):
        stale = self.store.begin_refresh(self.initial_token)
        first = self.store.begin_refresh(self.initial_token)
        first_result = self.store.finish_refresh(first)
        next_attempt = self.store.begin_refresh(first_result.refresh_token)
        self.store.finish_refresh(next_attempt)

        with self.assertRaises(StaleRefreshAttempt):
            self.store.finish_refresh_or_recover(stale)

        self.assertEqual(self.store.generation, 2)


class ConditionalStoreTests(unittest.TestCase):
    def test_matching_expectation_rotates_once(self):
        storage = InMemorySessionStore()

        result = storage.conditional_rotate(
            expected_token="refresh-synthetic-0",
            expected_generation=0,
        )

        self.assertIsNotNone(result)
        self.assertEqual(storage.read().refresh_token, "refresh-synthetic-1")
        self.assertEqual(storage.read().generation, 1)

    def test_stale_generation_returns_conflict_without_mutation(self):
        storage = InMemorySessionStore()
        storage.conditional_rotate(
            expected_token="refresh-synthetic-0",
            expected_generation=0,
        )
        before = storage.read()

        result = storage.conditional_rotate(
            expected_token="refresh-synthetic-0",
            expected_generation=0,
        )

        self.assertIsNone(result)
        self.assertEqual(storage.read(), before)

    def test_matching_generation_with_wrong_token_returns_conflict(self):
        storage = InMemorySessionStore()
        before = storage.read()

        result = storage.conditional_rotate(
            expected_token="refresh-synthetic-other",
            expected_generation=0,
        )

        self.assertIsNone(result)
        self.assertEqual(storage.read(), before)


if __name__ == "__main__":
    unittest.main()
