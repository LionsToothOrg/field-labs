import unittest

from check_in import accept_offline, reconcile


class OfflineCheckInTests(unittest.TestCase):
    def test_distinct_credentials_reconcile_without_conflict(self):
        check_ins = [
            accept_offline("PASS-EXAMPLE-001", "DEVICE-A", 100),
            accept_offline("PASS-EXAMPLE-002", "DEVICE-B", 101),
        ]

        result = reconcile(check_ins)

        self.assertEqual(2, len(result.accepted))
        self.assertEqual((), result.conflicts)

    def test_duplicate_offline_acceptance_surfaces_conflict(self):
        check_ins = [
            accept_offline("PASS-EXAMPLE-001", "DEVICE-A", 100),
            accept_offline("PASS-EXAMPLE-001", "DEVICE-B", 101),
        ]

        result = reconcile(check_ins)

        self.assertEqual(("DEVICE-A",), tuple(item.device_id for item in result.accepted))
        self.assertEqual(("DEVICE-B",), tuple(item.device_id for item in result.conflicts))

    def test_input_order_does_not_change_earliest_winner(self):
        later = accept_offline("PASS-EXAMPLE-001", "DEVICE-B", 101)
        earlier = accept_offline("PASS-EXAMPLE-001", "DEVICE-A", 100)

        result = reconcile([later, earlier])

        self.assertEqual(("DEVICE-A",), tuple(item.device_id for item in result.accepted))
        self.assertEqual(("DEVICE-B",), tuple(item.device_id for item in result.conflicts))

    def test_equal_timestamps_use_device_id_as_deterministic_tiebreaker(self):
        check_ins = [
            accept_offline("PASS-EXAMPLE-001", "DEVICE-B", 100),
            accept_offline("PASS-EXAMPLE-001", "DEVICE-A", 100),
        ]

        result = reconcile(check_ins)

        self.assertEqual(("DEVICE-A",), tuple(item.device_id for item in result.accepted))
        self.assertEqual(("DEVICE-B",), tuple(item.device_id for item in result.conflicts))


if __name__ == "__main__":
    unittest.main()
