import unittest

from stable_routing import (
    Node,
    compare_ownership_snapshots,
    measure_membership_transition,
    measure_ownership_distribution,
    rendezvous_score,
    route,
)


class StableRoutingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.nodes = (Node("node-a"), Node("node-b"), Node("node-c"))
        self.keys = tuple(f"item-{index:03d}" for index in range(100))

    def test_routing_is_deterministic_and_independent_of_node_order(self) -> None:
        forward = [route(key, self.nodes) for key in self.keys]
        reversed_order = [route(key, reversed(self.nodes)) for key in self.keys]
        self.assertEqual(forward, reversed_order)
        self.assertEqual(forward, [route(key, self.nodes) for key in self.keys])

    def test_single_node_owns_every_key(self) -> None:
        only_node = Node("node-only")
        for key in self.keys:
            self.assertEqual(route(key, (only_node,)), only_node)

    def test_adding_one_node_only_moves_keys_to_the_added_node(self) -> None:
        before = {key: route(key, self.nodes).name for key in self.keys}
        added = Node("node-d")
        after_nodes = self.nodes + (added,)
        after = {key: route(key, after_nodes).name for key in self.keys}
        moved = [key for key in self.keys if before[key] != after[key]]
        self.assertTrue(moved, "synthetic corpus should exercise at least one move")
        self.assertTrue(all(after[key] == added.name for key in moved))

    def test_removing_one_node_only_moves_keys_owned_by_removed_node(self) -> None:
        removed = self.nodes[-1]
        before = {key: route(key, self.nodes).name for key in self.keys}
        after_nodes = self.nodes[:-1]
        after = {key: route(key, after_nodes).name for key in self.keys}
        moved = [key for key in self.keys if before[key] != after[key]]
        self.assertTrue(moved, "synthetic corpus should exercise at least one move")
        self.assertTrue(all(before[key] == removed.name for key in moved))

    def test_transition_measurement_reports_exact_synthetic_movement(self) -> None:
        added = Node("node-d")
        report = measure_membership_transition(self.keys, self.nodes, self.nodes + (added,))
        self.assertEqual(report.total_keys, 100)
        self.assertEqual(report.moved_count, 19)
        self.assertEqual(report.movement_ratio, 0.19)
        self.assertTrue(all(route(key, self.nodes + (added,)) == added for key in report.moved_keys))

    def test_transition_measurement_is_zero_for_unchanged_membership(self) -> None:
        report = measure_membership_transition(self.keys, self.nodes, reversed(self.nodes))
        self.assertEqual(report.moved_keys, ())
        self.assertEqual(report.movement_ratio, 0.0)

    def test_transition_measurement_rejects_ambiguous_key_corpora(self) -> None:
        with self.assertRaises(ValueError):
            measure_membership_transition((), self.nodes, self.nodes)
        with self.assertRaises(ValueError):
            measure_membership_transition(("item-001", "item-001"), self.nodes, self.nodes)

    def test_distribution_reports_exact_synthetic_ownership(self) -> None:
        report = measure_ownership_distribution(self.keys, self.nodes)
        self.assertEqual(report.total_keys, 100)
        self.assertEqual(report.ownership, (("node-a", 38), ("node-b", 32), ("node-c", 30)))
        self.assertEqual(report.min_count, 30)
        self.assertEqual(report.max_count, 38)
        self.assertEqual(report.spread, 8)

    def test_distribution_includes_nodes_with_zero_owned_keys(self) -> None:
        report = measure_ownership_distribution(("item-001",), self.nodes)
        self.assertEqual(report.total_keys, 1)
        self.assertEqual(sum(report.counts.values()), 1)
        self.assertEqual(set(report.counts), {"node-a", "node-b", "node-c"})
        self.assertEqual(sum(count == 0 for count in report.counts.values()), 2)

    def test_distribution_is_independent_of_node_order(self) -> None:
        forward = measure_ownership_distribution(self.keys, self.nodes)
        reversed_order = measure_ownership_distribution(self.keys, reversed(self.nodes))
        self.assertEqual(forward, reversed_order)

    def test_ownership_transition_reports_exact_synthetic_deltas(self) -> None:
        report = compare_ownership_snapshots(self.keys, self.nodes, self.nodes + (Node("node-d"),))
        self.assertEqual(report.total_keys, 100)
        self.assertEqual(report.before.ownership, (("node-a", 38), ("node-b", 32), ("node-c", 30)))
        self.assertEqual(report.after.ownership, (("node-a", 32), ("node-b", 25), ("node-c", 24), ("node-d", 19)))
        self.assertEqual(report.deltas, (("node-a", -6), ("node-b", -7), ("node-c", -6), ("node-d", 19)))
        self.assertEqual(sum(report.delta_counts.values()), 0)

    def test_ownership_transition_is_zero_for_unchanged_membership(self) -> None:
        report = compare_ownership_snapshots(self.keys, self.nodes, reversed(self.nodes))
        self.assertEqual(report.deltas, (("node-a", 0), ("node-b", 0), ("node-c", 0)))

    def test_score_is_stable_for_same_key_and_node(self) -> None:
        node = Node("node-a")
        self.assertEqual(rendezvous_score("item-001", node), rendezvous_score("item-001", node))

    def test_invalid_inputs_fail_explicitly(self) -> None:
        with self.assertRaises(ValueError):
            Node("")
        with self.assertRaises(ValueError):
            route("", self.nodes)
        with self.assertRaises(ValueError):
            route("item-001", ())
        with self.assertRaises(ValueError):
            route("item-001", (Node("node-a"), Node("node-a")))
        with self.assertRaises(TypeError):
            route("item-001", (Node("node-a"), "node-b"))
        with self.assertRaises(ValueError):
            measure_ownership_distribution((), self.nodes)
        with self.assertRaises(ValueError):
            compare_ownership_snapshots((), self.nodes, self.nodes)


if __name__ == "__main__":
    unittest.main()
