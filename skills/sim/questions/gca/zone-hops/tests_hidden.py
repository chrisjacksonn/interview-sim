"""Hidden suite for Zone Hops.

Never copied into a session workspace.
"""

import unittest

from solution import solve


class TestZoneHops(unittest.TestCase):
    # --- the happy path ---

    def test_basic(self):
        conveyors = [("A", "B"), ("B", "C"), ("A", "C"), ("C", "D")]
        self.assertEqual(solve(conveyors, "A"), {"A": 0, "B": 1, "C": 1, "D": 2})

    def test_straight_chain(self):
        conveyors = [("a", "b"), ("b", "c"), ("c", "d"), ("d", "e")]
        self.assertEqual(solve(conveyors, "a"), {"a": 0, "b": 1, "c": 2, "d": 3, "e": 4})

    # --- shortest, not just any, path ---

    def test_shortcut_beats_the_long_way(self):
        # Catches depth-first traversal, which finds D at 3 hops down the chain.
        conveyors = [("A", "B"), ("B", "C"), ("C", "D"), ("A", "D")]
        self.assertEqual(solve(conveyors, "A")["D"], 1)

    def test_long_way_listed_first(self):
        # Same check with edge order reversed, so a solution cannot pass by luck.
        conveyors = [("A", "D"), ("A", "B"), ("B", "C"), ("C", "D")]
        self.assertEqual(solve(conveyors, "A")["D"], 1)

    def test_shorter_route_discovered_later(self):
        conveyors = [("A", "B"), ("B", "Z"), ("A", "C"), ("C", "Z"), ("A", "Z")]
        self.assertEqual(solve(conveyors, "A")["Z"], 1)

    def test_must_expand_breadth_first(self):
        """X is two hops away via C, three via B and D.

        Catches a stack-based traversal, which descends the B branch first and
        stamps X at 3 before ever looking at C. Every other shortest-path test
        here happens to survive that bug because the target is a direct
        neighbour of the start.
        """
        conveyors = [("A", "C"), ("A", "B"), ("B", "D"), ("C", "X"), ("D", "X")]
        self.assertEqual(solve(conveyors, "A")["X"], 2)

    def test_must_expand_breadth_first_other_edge_order(self):
        # Same graph, edges listed the other way round, so neither a queue nor a
        # stack can pass by accident of ordering.
        conveyors = [("D", "X"), ("C", "X"), ("B", "D"), ("A", "B"), ("A", "C")]
        self.assertEqual(solve(conveyors, "A")["X"], 2)

    # --- start zone ---

    def test_start_is_always_present_at_zero(self):
        self.assertEqual(solve([], "only")["only"], 0)

    def test_start_absent_from_every_conveyor(self):
        self.assertEqual(solve([("X", "Y")], "Q"), {"Q": 0})

    def test_start_is_not_reset_by_a_cycle_back_to_it(self):
        # Catches solutions that overwrite an existing distance.
        conveyors = [("A", "B"), ("B", "A")]
        self.assertEqual(solve(conveyors, "A"), {"A": 0, "B": 1})

    # --- awkward input ---

    def test_self_loop_is_harmless(self):
        conveyors = [("A", "A"), ("A", "B")]
        self.assertEqual(solve(conveyors, "A"), {"A": 0, "B": 1})

    def test_duplicate_conveyors(self):
        conveyors = [("A", "B"), ("A", "B"), ("A", "B")]
        self.assertEqual(solve(conveyors, "A"), {"A": 0, "B": 1})

    def test_cycle_terminates(self):
        # An unvisited check that is missing turns this into an infinite loop.
        conveyors = [("A", "B"), ("B", "C"), ("C", "A")]
        self.assertEqual(solve(conveyors, "A"), {"A": 0, "B": 1, "C": 2})

    def test_two_cycles_joined(self):
        conveyors = [("A", "B"), ("B", "A"), ("B", "C"), ("C", "D"), ("D", "B")]
        self.assertEqual(solve(conveyors, "A"), {"A": 0, "B": 1, "C": 2, "D": 3})

    def test_empty_conveyors(self):
        self.assertEqual(solve([], "A"), {"A": 0})

    # --- reachability ---

    def test_disconnected_component_is_absent(self):
        conveyors = [("A", "B"), ("C", "D"), ("D", "E")]
        self.assertEqual(solve(conveyors, "A"), {"A": 0, "B": 1})

    def test_zone_only_reachable_backwards_is_absent(self):
        # Catches anyone who built an undirected graph.
        conveyors = [("A", "B"), ("C", "A")]
        self.assertEqual(solve(conveyors, "A"), {"A": 0, "B": 1})

    def test_names_are_case_sensitive(self):
        conveyors = [("a", "B"), ("A", "c")]
        self.assertEqual(solve(conveyors, "a"), {"a": 0, "B": 1})

    # --- shape and scale ---

    def test_values_are_integers(self):
        result = solve([("A", "B")], "A")
        self.assertIsInstance(result["B"], int)

    def test_long_chain_does_not_recurse_to_death(self):
        # A naive recursive traversal blows the stack here.
        conveyors = [("z%d" % i, "z%d" % (i + 1)) for i in range(3000)]
        result = solve(conveyors, "z0")
        self.assertEqual(len(result), 3001)
        self.assertEqual(result["z3000"], 3000)

    def test_wide_graph(self):
        conveyors = [("hub", "leaf%d" % i) for i in range(5000)]
        result = solve(conveyors, "hub")
        self.assertEqual(len(result), 5001)
        self.assertEqual(result["leaf4999"], 1)


if __name__ == "__main__":
    unittest.main()
