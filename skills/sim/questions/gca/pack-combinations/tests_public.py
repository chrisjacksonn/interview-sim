"""Sample tests for Pack Combinations. A sanity check, not the grade."""

import unittest

from solution import solve


class TestPackCombinations(unittest.TestCase):
    def test_worked_example(self):
        self.assertEqual(solve([1, 2, 5], 5), 4)

    def test_impossible(self):
        self.assertEqual(solve([2], 3), 0)

    def test_zero_target_is_one_way(self):
        self.assertEqual(solve([3], 0), 1)

    def test_no_sizes_no_target(self):
        self.assertEqual(solve([], 0), 1)

    def test_no_sizes_with_target(self):
        self.assertEqual(solve([], 7), 0)


if __name__ == "__main__":
    unittest.main()
