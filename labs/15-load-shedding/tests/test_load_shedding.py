import unittest

from load_shedding import admit_burst


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


if __name__ == "__main__":
    unittest.main()
