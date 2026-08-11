"""Sample tests for Log Window. A sanity check, not the grade."""

import unittest

from solution import solve


class TestLogWindow(unittest.TestCase):
    def test_best_window_is_at_the_end(self):
        self.assertEqual(solve([1, 4, 2, 10, 2, 3, 1, 0, 20], 4), 24)

    def test_single_bucket(self):
        self.assertEqual(solve([5], 1), 5)

    def test_window_wider_than_the_input(self):
        self.assertEqual(solve([1, 2], 5), 0)

    def test_empty(self):
        self.assertEqual(solve([], 3), 0)


if __name__ == "__main__":
    unittest.main()
