"""Sample tests for Rolling Median. A sanity check, not the grade."""

import unittest

from solution import solve


class TestRollingMedian(unittest.TestCase):
    def test_odd_window(self):
        self.assertEqual(solve([1, 3, 2, 5, 4], 3), [2.0, 3.0, 4.0])

    def test_even_window(self):
        self.assertEqual(solve([1, 2, 3, 4], 2), [1.5, 2.5, 3.5])

    def test_single(self):
        self.assertEqual(solve([5], 1), [5.0])

    def test_window_too_wide(self):
        self.assertEqual(solve([1, 2], 5), [])


if __name__ == "__main__":
    unittest.main()
