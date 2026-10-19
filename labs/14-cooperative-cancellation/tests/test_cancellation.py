import unittest

from cancellation import simulate_parallel_work


class CooperativeCancellationTests(unittest.TestCase):
    def test_propagated_cancellation_stops_slow_worker(self):
        result = simulate_parallel_work(
            {"fast": 2.0, "slow": 10.0},
            cancel_at=3.0,
            check_interval=1.0,
            propagate_cancellation=True,
        )

        self.assertEqual(result.wall_time, 3.0)
        self.assertEqual(result.total_work, 5.0)
        self.assertTrue(result.workers[0].completed)
        self.assertTrue(result.workers[1].cancelled)

    def test_without_propagation_work_continues_after_caller_stops(self):
        result = simulate_parallel_work(
            {"fast": 2.0, "slow": 10.0},
            cancel_at=3.0,
            check_interval=1.0,
            propagate_cancellation=False,
        )

        self.assertEqual(result.wall_time, 10.0)
        self.assertEqual(result.total_work, 12.0)
        self.assertFalse(any(worker.cancelled for worker in result.workers))

    def test_polling_interval_bounds_cancellation_detection_delay(self):
        result = simulate_parallel_work(
            {"slow": 10.0},
            cancel_at=3.2,
            check_interval=1.0,
            propagate_cancellation=True,
        )

        self.assertEqual(result.wall_time, 4.0)
        self.assertTrue(result.workers[0].cancelled)

    def test_worker_finishing_before_next_check_completes_normally(self):
        result = simulate_parallel_work(
            {"almost-done": 3.5},
            cancel_at=3.2,
            check_interval=1.0,
            propagate_cancellation=True,
        )

        self.assertEqual(result.wall_time, 3.5)
        self.assertTrue(result.workers[0].completed)
        self.assertFalse(result.workers[0].cancelled)

    def test_invalid_inputs_are_rejected(self):
        cases = [
            ({}, 1.0, 1.0),
            ({"worker": 1.0}, -1.0, 1.0),
            ({"worker": 1.0}, 1.0, 0.0),
            ({"worker": float("inf")}, 1.0, 1.0),
        ]

        for workloads, cancel_at, check_interval in cases:
            with self.subTest(
                workloads=workloads,
                cancel_at=cancel_at,
                check_interval=check_interval,
            ):
                with self.assertRaises(ValueError):
                    simulate_parallel_work(
                        workloads,
                        cancel_at=cancel_at,
                        check_interval=check_interval,
                        propagate_cancellation=True,
                    )


if __name__ == "__main__":
    unittest.main()
