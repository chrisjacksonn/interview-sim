"""Sample tests for Shift Coverage.

A sanity check, not the grade.
"""

import unittest

from solution import solve


class TestShiftCoverage(unittest.TestCase):
    def test_all_three_needed(self):
        self.assertEqual(solve([(0, 4), (2, 8), (7, 10)], 10), 3)

    def test_greedy_choice_matters(self):
        self.assertEqual(solve([(0, 5), (1, 9), (4, 6)], 9), 2)

    def test_gap_is_impossible(self):
        self.assertEqual(solve([(0, 3), (5, 9)], 9), -1)

    def test_must_start_at_zero(self):
        self.assertEqual(solve([(2, 9)], 9), -1)

    def test_nothing_to_cover(self):
        self.assertEqual(solve([], 0), 0)


if __name__ == "__main__":
    unittest.main()
