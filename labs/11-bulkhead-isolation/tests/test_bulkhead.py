import unittest

from bulkhead import Bulkhead


class BulkheadTests(unittest.TestCase):
    def test_rejects_work_when_partition_is_saturated(self):
        bulkhead = Bulkhead({"search": 2})
        self.assertTrue(bulkhead.admit("search").allowed)
        self.assertTrue(bulkhead.admit("search").allowed)
        decision = bulkhead.admit("search")
        self.assertFalse(decision.allowed)
        self.assertEqual(decision.reason, "partition_saturated")
        self.assertEqual((decision.in_flight, decision.capacity), (2, 2))

    def test_saturation_is_isolated_between_partitions(self):
        bulkhead = Bulkhead({"search": 1, "exports": 1})
        bulkhead.admit("search")
        self.assertFalse(bulkhead.admit("search").allowed)
        self.assertTrue(bulkhead.admit("exports").allowed)

    def test_release_restores_capacity(self):
        bulkhead = Bulkhead({"search": 1})
        bulkhead.admit("search")
        bulkhead.release("search")
        self.assertTrue(bulkhead.admit("search").allowed)

    def test_weighted_admission_consumes_requested_permits(self):
        bulkhead = Bulkhead({"exports": 4})
        decision = bulkhead.admit("exports", permits=3)
        self.assertTrue(decision.allowed)
        self.assertEqual(decision.permits, 3)
        self.assertEqual(bulkhead.snapshot()["exports"], (3, 4))
        self.assertFalse(bulkhead.admit("exports", permits=2).allowed)

    def test_weighted_release_restores_requested_permits(self):
        bulkhead = Bulkhead({"exports": 4})
        bulkhead.admit("exports", permits=3)
        bulkhead.release("exports", permits=2)
        self.assertEqual(bulkhead.snapshot()["exports"], (1, 4))

    def test_scoped_admission_releases_capacity(self):
        bulkhead = Bulkhead({"search": 1})
        with bulkhead.admission("search") as decision:
            self.assertTrue(decision.allowed)
            self.assertEqual(bulkhead.snapshot()["search"], (1, 1))
        self.assertEqual(bulkhead.snapshot()["search"], (0, 1))

    def test_weighted_scoped_admission_releases_all_permits(self):
        bulkhead = Bulkhead({"exports": 4})
        with bulkhead.admission("exports", permits=3) as decision:
            self.assertTrue(decision.allowed)
            self.assertEqual(bulkhead.snapshot()["exports"], (3, 4))
        self.assertEqual(bulkhead.snapshot()["exports"], (0, 4))

    def test_scoped_admission_releases_capacity_after_exception(self):
        bulkhead = Bulkhead({"search": 1})
        with self.assertRaisesRegex(RuntimeError, "synthetic failure"):
            with bulkhead.admission("search") as decision:
                self.assertTrue(decision.allowed)
                raise RuntimeError("synthetic failure")
        self.assertEqual(bulkhead.snapshot()["search"], (0, 1))

    def test_rejected_scoped_admission_does_not_release_existing_work(self):
        bulkhead = Bulkhead({"search": 1})
        bulkhead.admit("search")
        with bulkhead.admission("search") as decision:
            self.assertFalse(decision.allowed)
        self.assertEqual(bulkhead.snapshot()["search"], (1, 1))

    def test_rejects_release_without_admitted_work(self):
        bulkhead = Bulkhead({"search": 1})
        with self.assertRaises(RuntimeError):
            bulkhead.release("search")

    def test_rejects_release_above_admitted_permits(self):
        bulkhead = Bulkhead({"exports": 4})
        bulkhead.admit("exports", permits=2)
        with self.assertRaises(RuntimeError):
            bulkhead.release("exports", permits=3)
        self.assertEqual(bulkhead.snapshot()["exports"], (2, 4))

    def test_rejects_non_positive_permits(self):
        bulkhead = Bulkhead({"search": 2})
        for permits in (0, -1):
            with self.subTest(permits=permits), self.assertRaises(ValueError):
                bulkhead.admit("search", permits=permits)
            with self.subTest(permits=permits), self.assertRaises(ValueError):
                bulkhead.release("search", permits=permits)

    def test_rejects_unknown_partition(self):
        bulkhead = Bulkhead({"search": 1})
        with self.assertRaises(KeyError):
            bulkhead.admit("missing")
        with self.assertRaises(KeyError):
            bulkhead.release("missing")

    def test_rejects_invalid_configuration(self):
        for capacities in ({}, {"": 1}, {"search": 0}, {"search": -1}):
            with self.subTest(capacities=capacities), self.assertRaises(ValueError):
                Bulkhead(capacities)

    def test_snapshot_reports_each_partition_independently(self):
        bulkhead = Bulkhead({"search": 2, "exports": 1})
        bulkhead.admit("search")
        self.assertEqual(bulkhead.snapshot(), {"search": (1, 2), "exports": (0, 1)})


if __name__ == "__main__":
    unittest.main()
