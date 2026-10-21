import unittest

from stable_routing import Node, rendezvous_score, route


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

    def test_score_is_stable_for_same_key_and_node(self) -> None:
        node = Node("node-a")
        self.assertEqual(
            rendezvous_score("item-001", node),
            rendezvous_score("item-001", node),
        )

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


if __name__ == "__main__":
    unittest.main()
