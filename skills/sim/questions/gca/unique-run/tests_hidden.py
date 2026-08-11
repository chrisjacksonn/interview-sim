"""Hidden suite for Unique Run.

Never copied into a session workspace.
"""

import unittest

from solution import solve


class TestUniqueRun(unittest.TestCase):
    # --- the basics ---

    def test_repeat_forces_a_later_start(self):
        self.assertEqual(solve(["a", "b", "c", "a", "d"]), 4)

    def test_all_distinct(self):
        self.assertEqual(solve(["p", "q", "r", "s"]), 4)

    def test_all_identical(self):
        self.assertEqual(solve(["x", "x", "x"]), 1)

    def test_single_code(self):
        self.assertEqual(solve(["only"]), 1)

    def test_empty(self):
        self.assertEqual(solve([]), 0)

    def test_two_the_same(self):
        self.assertEqual(solve(["a", "a"]), 1)

    def test_two_different(self):
        self.assertEqual(solve(["a", "b"]), 2)

    # --- where the window has to restart ---

    def test_the_window_must_not_move_backwards(self):
        """The classic bug in this shape.

        When 'a' repeats at the end, the left edge is already past the first
        'a'. Jumping to that stale position instead of leaving the edge alone
        widens the window over a stretch that is not clean.
        """
        self.assertEqual(solve(["a", "b", "b", "a"]), 2)

    def test_stale_index_further_back(self):
        self.assertEqual(solve(["a", "b", "c", "c", "b", "a"]), 3)

    def test_repeat_at_the_very_end(self):
        self.assertEqual(solve(["a", "b", "c", "c"]), 3)

    def test_repeat_at_the_very_start(self):
        self.assertEqual(solve(["a", "a", "b", "c", "d"]), 4)

    def test_best_run_is_in_the_middle(self):
        # The clean stretch is c, d, e starting at index 3, extended left by the
        # second 'a'. It neither starts nor ends at the edges of the input.
        self.assertEqual(solve(["a", "b", "a", "c", "d", "e", "c"]), 5)

    def test_best_run_is_at_the_end(self):
        # Starts on the second 'z', not after it.
        self.assertEqual(solve(["z", "z", "a", "b", "c", "d"]), 5)

    def test_alternating_pair(self):
        self.assertEqual(solve(["a", "b"] * 20), 2)

    def test_every_code_repeats_once_far_apart(self):
        codes = ["a", "b", "c", "d", "a", "b", "c", "d"]
        self.assertEqual(solve(codes), 4)

    # --- it is consecutive, not a subsequence ---

    def test_distinct_count_is_not_the_answer(self):
        # Four distinct codes, but the repeated 'a' means no clean stretch is
        # longer than three. Catches anything returning len(set(codes)).
        codes = ["a", "b", "a", "c", "a", "d", "a"]
        self.assertEqual(len(set(codes)), 4)
        self.assertEqual(solve(codes), 3)

    def test_distinct_count_is_not_the_answer_at_scale(self):
        # Sixty alternating codes then three new ones. The best stretch is the
        # trailing x, y, p, q, r.
        codes = ["x", "y"] * 30 + ["p", "q", "r"]
        self.assertEqual(len(set(codes)), 5)
        self.assertEqual(solve(codes), 5)

    # --- codes are strings ---

    def test_multicharacter_codes(self):
        self.assertEqual(solve(["p01", "p02", "p01", "p03"]), 3)

    def test_codes_are_case_sensitive(self):
        self.assertEqual(solve(["a", "A", "a"]), 2)

    # --- shape ---

    def test_returns_an_int_not_a_bool(self):
        result = solve(["a"])
        self.assertIsInstance(result, int)
        self.assertNotIsInstance(result, bool)

    def test_input_is_not_mutated(self):
        codes = ["a", "b", "a"]
        original = list(codes)
        solve(codes)
        self.assertEqual(codes, original)

    # --- scale ---

    def test_large_all_distinct(self):
        codes = ["c%d" % index for index in range(150000)]
        self.assertEqual(solve(codes), 150000)

    def test_large_all_identical(self):
        self.assertEqual(solve(["same"] * 150000), 1)

    def test_large_with_a_bounded_alphabet(self):
        # 200k codes drawn from 50 distinct values. Anything that rechecks the
        # whole window per step will not finish.
        codes = ["c%d" % (index % 50) for index in range(200000)]
        self.assertEqual(solve(codes), 50)

    def test_large_best_run_at_the_end(self):
        codes = ["dup"] * 100000 + ["u%d" % index for index in range(500)]
        self.assertEqual(solve(codes), 501)


if __name__ == "__main__":
    unittest.main()
