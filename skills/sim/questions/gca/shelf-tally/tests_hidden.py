"""Hidden suite for Shelf Tally.

Never copied into a session workspace, never read into an agent's context. The
grader runs this file and reports pass and fail counts only.

Each test targets a distinct way a plausible-looking solution goes wrong, so
that partial credit means something rather than tracking one bug across ten
assertions.
"""

import unittest

from solution import solve


class TestShelfTally(unittest.TestCase):
    # --- the happy path, restated so a totally broken solution scores zero ---

    def test_basic_aggregation(self):
        self.assertEqual(solve(["A12-3:40", "A12-1:5", "B7-2:12"]), {"A12": 45, "B7": 12})

    def test_same_shelf_twice_accumulates(self):
        # Catches solutions that key on aisle-shelf and overwrite instead of sum.
        self.assertEqual(solve(["C3-1:10", "C3-1:4"]), {"C3": 14})

    # --- malformed entries ---

    def test_no_separators_is_skipped(self):
        self.assertEqual(solve(["nonsense", "A1-1:3"]), {"A1": 3})

    def test_separators_out_of_order_is_skipped(self):
        # Colon before dash. Catches naive split(':') then split('-').
        self.assertEqual(solve(["A1:2-5"]), {})

    def test_extra_separator_is_skipped(self):
        # Catches split with maxsplit that silently swallows the remainder.
        self.assertEqual(solve(["A1-2:3:4", "A1-2-3:4"]), {})

    def test_empty_aisle_is_skipped(self):
        self.assertEqual(solve(["-2:5"]), {})

    def test_empty_shelf_is_skipped(self):
        self.assertEqual(solve(["A1-:5"]), {})

    def test_empty_count_is_skipped(self):
        self.assertEqual(solve(["A1-2:"]), {})

    def test_non_numeric_shelf_is_skipped(self):
        self.assertEqual(solve(["A1-x:5"]), {})

    def test_non_numeric_count_is_skipped(self):
        self.assertEqual(solve(["A1-2:five"]), {})

    def test_negative_count_is_skipped(self):
        # Catches solutions that sum before validating the sign.
        self.assertEqual(solve(["A1-2:-3", "A1-2:10"]), {"A1": 10})

    def test_empty_string_entry_is_skipped(self):
        self.assertEqual(solve([""]), {})

    # --- aisles that end up empty ---

    def test_aisle_with_only_invalid_entries_is_absent(self):
        # Catches solutions that pre-seed the dict with every aisle they parse.
        self.assertEqual(solve(["Z1-x:5", "Z1-y:6"]), {})

    def test_zero_count_still_creates_the_aisle(self):
        # The mirror of the previous test: a valid zero is not "no entry".
        self.assertEqual(solve(["Z2-1:0"]), {"Z2": 0})

    # --- details that are easy to miss ---

    def test_surrounding_whitespace_is_tolerated(self):
        self.assertEqual(solve(["  A1-2:5  ", "\tA1-3:5\n"]), {"A1": 10})

    def test_aisle_labels_are_case_sensitive(self):
        self.assertEqual(solve(["a1-1:2", "A1-1:3"]), {"a1": 2, "A1": 3})

    def test_leading_zeros_are_fine(self):
        self.assertEqual(solve(["A1-007:0042"]), {"A1": 42})

    def test_shelf_number_does_not_affect_the_total(self):
        self.assertEqual(solve(["A1-99:1", "A1-0:1"]), {"A1": 2})

    # --- shape ---

    def test_empty_input_returns_empty_dict(self):
        result = solve([])
        self.assertEqual(result, {})
        self.assertIsInstance(result, dict)

    def test_large_input(self):
        entries = ["A%d-1:2" % (index % 50,) for index in range(10000)]
        result = solve(entries)
        self.assertEqual(len(result), 50)
        self.assertEqual(sum(result.values()), 20000)


if __name__ == "__main__":
    unittest.main()
