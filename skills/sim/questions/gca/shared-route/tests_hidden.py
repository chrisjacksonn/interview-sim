"""Hidden suite for Shared Route.

Never copied into a session workspace.
"""

import unittest

from solution import solve


class TestSharedRoute(unittest.TestCase):
    # --- the basics ---

    def test_simple_shared_pair(self):
        self.assertEqual(solve(["a", "b", "c", "d"], ["b", "d"]), 2)

    def test_identical_routes(self):
        route = ["a", "b", "c", "d"]
        self.assertEqual(solve(route, list(route)), 4)

    def test_nothing_in_common(self):
        self.assertEqual(solve(["a", "b"], ["c", "d"]), 0)

    def test_one_shared_stop(self):
        self.assertEqual(solve(["a", "b", "c"], ["z", "b", "y"]), 1)

    # --- order matters ---

    def test_reversed_order_shares_only_one(self):
        self.assertEqual(solve(["a", "b", "c"], ["c", "b", "a"]), 1)

    def test_order_is_relative_not_adjacent(self):
        # Catches solutions that look for a contiguous run.
        self.assertEqual(solve(["a", "x", "b", "y", "c"], ["a", "b", "c"]), 3)

    def test_interleaved_choice_matters(self):
        # Greedily taking the first match of each stop gives 2, not 3.
        self.assertEqual(solve(["a", "b", "c", "a", "d"], ["a", "c", "d"]), 3)

    def test_must_not_reuse_a_position(self):
        # Counting shared stops by frequency gives 2 here.
        self.assertEqual(solve(["a", "b"], ["b", "a"]), 1)

    # --- repeats ---

    def test_repeated_stops_in_both(self):
        self.assertEqual(solve(["x", "y", "x", "z", "y"], ["x", "y", "y"]), 3)

    def test_all_the_same_stop(self):
        self.assertEqual(solve(["a"] * 5, ["a"] * 3), 3)

    def test_repeats_capped_by_the_shorter_route(self):
        self.assertEqual(solve(["a", "a"], ["a", "a", "a", "a"]), 2)

    def test_set_intersection_is_not_the_answer(self):
        # The distinct shared stops are a and b, but order allows only one pair.
        self.assertEqual(solve(["a", "b", "a", "b"], ["b", "a"]), 2)

    # --- empties ---

    def test_both_empty(self):
        self.assertEqual(solve([], []), 0)

    def test_first_empty(self):
        self.assertEqual(solve([], ["a", "b"]), 0)

    def test_second_empty(self):
        self.assertEqual(solve(["a", "b"], []), 0)

    def test_single_elements_matching(self):
        self.assertEqual(solve(["a"], ["a"]), 1)

    def test_single_elements_not_matching(self):
        self.assertEqual(solve(["a"], ["b"]), 0)

    # --- asymmetry ---

    def test_argument_order_does_not_change_the_answer(self):
        first = ["a", "b", "c", "d", "e"]
        second = ["b", "d", "a", "e"]
        self.assertEqual(solve(first, second), solve(second, first))

    def test_much_longer_first(self):
        self.assertEqual(solve(list("abcdefghij"), list("aej")), 3)

    def test_much_longer_second(self):
        self.assertEqual(solve(list("aej"), list("abcdefghij")), 3)

    # --- codes are strings, not characters ---

    def test_multicharacter_codes(self):
        first = ["stop12", "stop3", "stop45"]
        second = ["stop3", "stop45"]
        self.assertEqual(solve(first, second), 2)

    def test_codes_are_case_sensitive(self):
        self.assertEqual(solve(["A", "b"], ["a", "B"]), 0)

    # --- shape ---

    def test_returns_an_int_not_a_bool(self):
        result = solve(["a"], ["a"])
        self.assertIsInstance(result, int)
        self.assertNotIsInstance(result, bool)

    # --- scale ---

    def test_large_input_is_not_exponential(self):
        """1200 by 1200. Anything enumerating subsequences will not finish."""
        first = ["s%d" % (index % 60) for index in range(1200)]
        second = ["s%d" % (index % 45) for index in range(1200)]
        result = solve(first, second)
        self.assertGreater(result, 0)
        self.assertLessEqual(result, 1200)

    def test_large_identical_routes(self):
        route = ["s%d" % index for index in range(1400)]
        self.assertEqual(solve(route, list(route)), 1400)

    def test_large_disjoint_routes(self):
        first = ["a%d" % index for index in range(1200)]
        second = ["b%d" % index for index in range(1200)]
        self.assertEqual(solve(first, second), 0)


if __name__ == "__main__":
    unittest.main()
