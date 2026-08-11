"""Sample tests for Unique Run. A sanity check, not the grade."""

import unittest

from solution import solve


class TestUniqueRun(unittest.TestCase):
    def test_repeat_forces_a_later_start(self):
        self.assertEqual(solve(["a", "b", "c", "a", "d"]), 4)

    def test_all_the_same(self):
        self.assertEqual(solve(["x", "x", "x"]), 1)

    def test_all_distinct(self):
        self.assertEqual(solve(["p", "q", "r", "s"]), 4)

    def test_empty(self):
        self.assertEqual(solve([]), 0)


if __name__ == "__main__":
    unittest.main()
