import unittest

from check_in import accept_offline, merge_sync, reconcile


class OfflineCheckInTests(unittest.TestCase):
    def test_distinct_credentials_reconcile_without_conflict(self):
        check_ins = [
            accept_offline("CHECK-001", "PASS-EXAMPLE-001", "DEVICE-A", 100),
            accept_offline("CHECK-002", "PASS-EXAMPLE-002", "DEVICE-B", 101),
        ]

        result = reconcile(check_ins)

        self.assertEqual(2, len(result.accepted))
        self.assertEqual((), result.conflicts)

    def test_duplicate_offline_acceptance_surfaces_conflict(self):
        check_ins = [
            accept_offline("CHECK-001", "PASS-EXAMPLE-001", "DEVICE-A", 100),
            accept_offline("CHECK-002", "PASS-EXAMPLE-001", "DEVICE-B", 101),
        ]

        result = reconcile(check_ins)

        self.assertEqual(("DEVICE-A",), tuple(item.device_id for item in result.accepted))
        self.assertEqual(("DEVICE-B",), tuple(item.device_id for item in result.conflicts))

    def test_input_order_does_not_change_earliest_winner(self):
        later = accept_offline("CHECK-002", "PASS-EXAMPLE-001", "DEVICE-B", 101)
        earlier = accept_offline("CHECK-001", "PASS-EXAMPLE-001", "DEVICE-A", 100)

        result = reconcile([later, earlier])

        self.assertEqual(("DEVICE-A",), tuple(item.device_id for item in result.accepted))
        self.assertEqual(("DEVICE-B",), tuple(item.device_id for item in result.conflicts))

    def test_equal_timestamps_use_device_id_as_deterministic_tiebreaker(self):
        check_ins = [
            accept_offline("CHECK-002", "PASS-EXAMPLE-001", "DEVICE-B", 100),
            accept_offline("CHECK-001", "PASS-EXAMPLE-001", "DEVICE-A", 100),
        ]

        result = reconcile(check_ins)

        self.assertEqual(("DEVICE-A",), tuple(item.device_id for item in result.accepted))
        self.assertEqual(("DEVICE-B",), tuple(item.device_id for item in result.conflicts))

    def test_replaying_same_batch_does_not_duplicate_decisions(self):
        batch = [
            accept_offline("CHECK-001", "PASS-EXAMPLE-001", "DEVICE-A", 100),
            accept_offline("CHECK-002", "PASS-EXAMPLE-001", "DEVICE-B", 101),
        ]

        once = merge_sync([], batch)
        replayed = merge_sync(list(once), batch)
        result = reconcile(list(replayed))

        self.assertEqual(once, replayed)
        self.assertEqual(1, len(result.accepted))
        self.assertEqual(1, len(result.conflicts))

    def test_overlapping_incremental_batches_add_only_unseen_decisions(self):
        first_batch = [
            accept_offline("CHECK-001", "PASS-EXAMPLE-001", "DEVICE-A", 100),
            accept_offline("CHECK-002", "PASS-EXAMPLE-002", "DEVICE-B", 101),
        ]
        second_batch = [
            first_batch[1],
            accept_offline("CHECK-003", "PASS-EXAMPLE-003", "DEVICE-C", 102),
        ]

        known = merge_sync([], first_batch)
        merged = merge_sync(list(known), second_batch)

        self.assertEqual(("CHECK-001", "CHECK-002", "CHECK-003"), tuple(item.check_in_id for item in merged))
        self.assertEqual(3, len(reconcile(list(merged)).accepted))

    def test_reused_check_in_id_with_different_payload_fails_closed(self):
        original = accept_offline("CHECK-001", "PASS-EXAMPLE-001", "DEVICE-A", 100)
        conflicting = accept_offline("CHECK-001", "PASS-EXAMPLE-999", "DEVICE-A", 100)

        with self.assertRaisesRegex(ValueError, "conflicting payload"):
            merge_sync([original], [conflicting])


if __name__ == "__main__":
    unittest.main()
