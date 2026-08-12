"""Sample tests for Quiet Streaks. A sanity check, not the grade."""

import unittest

from solution import solve


class TestQuietStreaks(unittest.TestCase):
    def test_longest_of_several(self):
        self.assertEqual(solve([3, 0, 0, 1, 0, 0, 0, 2]), 3)

    def test_all_zero(self):
        self.assertEqual(solve([0, 0, 0]), 3)

    def test_no_zeros(self):
        self.assertEqual(solve([1, 2, 3]), 0)

    def test_empty(self):
        self.assertEqual(solve([]), 0)


if __name__ == "__main__":
    unittest.main()
