import unittest

from load_shedding import admit_burst, drain_admitted


class LoadSheddingTests(unittest.TestCase):
    def test_burst_uses_running_then_queue_then_sheds(self):
        result = admit_burst(
            ["req-a", "req-b", "req-c", "req-d", "req-e"],
            concurrency_limit=2,
            queue_limit=1,
        )

        self.assertEqual(
            [admission.decision for admission in result.admissions],
            ["running", "running", "queued", "shed", "shed"],
        )
        self.assertEqual((result.running, result.queued, result.shed), (2, 1, 2))

    def test_zero_queue_sheds_after_execution_capacity(self):
        result = admit_burst(
            ["req-a", "req-b", "req-c"],
            concurrency_limit=1,
            queue_limit=0,
        )

        self.assertEqual(
            [admission.decision for admission in result.admissions],
            ["running", "shed", "shed"],
        )

    def test_request_order_is_preserved(self):
        request_ids = ["req-c", "req-a", "req-b"]
        result = admit_burst(request_ids, concurrency_limit=1, queue_limit=1)

        self.assertEqual(
            [admission.request_id for admission in result.admissions], request_ids
        )

    def test_empty_burst_has_zero_counts(self):
        result = admit_burst([], concurrency_limit=2, queue_limit=2)

        self.assertEqual(result.admissions, ())
        self.assertEqual((result.running, result.queued, result.shed), (0, 0, 0))

    def test_invalid_capacities_are_rejected(self):
        invalid_cases = [(-1, 0), (0, -1), (1.5, 0), (1, True)]

        for concurrency_limit, queue_limit in invalid_cases:
            with self.subTest(
                concurrency_limit=concurrency_limit, queue_limit=queue_limit
            ):
                with self.assertRaises(ValueError):
                    admit_burst(
                        ["req-a"],
                        concurrency_limit=concurrency_limit,
                        queue_limit=queue_limit,
                    )

    def test_invalid_request_ids_are_rejected(self):
        for request_id in ["", None, 42]:
            with self.subTest(request_id=request_id):
                with self.assertRaises(ValueError):
                    admit_burst(
                        [request_id], concurrency_limit=1, queue_limit=0
                    )

    def test_drain_promotes_queued_work_in_fifo_order(self):
        result = admit_burst(
            ["req-a", "req-b", "req-c", "req-d", "req-e"],
            concurrency_limit=2,
            queue_limit=2,
        )

        steps = drain_admitted(result, concurrency_limit=2)

        self.assertEqual(len(steps), 2)
        self.assertEqual(steps[0].completed, ("req-a", "req-b"))
        self.assertEqual(steps[0].promoted, ("req-c", "req-d"))
        self.assertEqual(steps[0].queued, ())
        self.assertEqual(steps[1].completed, ("req-c", "req-d"))
        self.assertEqual(steps[1].promoted, ())

    def test_shed_work_never_enters_recovery(self):
        result = admit_burst(
            ["req-a", "req-b", "req-c"], concurrency_limit=1, queue_limit=1
        )

        steps = drain_admitted(result, concurrency_limit=1)
        observed = [request_id for step in steps for request_id in step.completed]

        self.assertEqual(observed, ["req-a", "req-b"])
        self.assertNotIn("req-c", observed)

    def test_empty_admission_has_no_recovery_steps(self):
        result = admit_burst([], concurrency_limit=1, queue_limit=1)

        self.assertEqual(drain_admitted(result, concurrency_limit=1), ())

    def test_drain_rejects_capacity_below_existing_running_work(self):
        result = admit_burst(["req-a", "req-b"], concurrency_limit=2, queue_limit=0)

        with self.assertRaises(ValueError):
            drain_admitted(result, concurrency_limit=1)


if __name__ == "__main__":
    unittest.main()
