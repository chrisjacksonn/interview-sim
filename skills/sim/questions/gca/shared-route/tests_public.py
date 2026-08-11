"""Sample tests for Shared Route. A sanity check, not the grade."""

import unittest

from solution import solve


class TestSharedRoute(unittest.TestCase):
    def test_simple_shared_pair(self):
        self.assertEqual(solve(["a", "b", "c", "d"], ["b", "d"]), 2)

    def test_reversed_order_shares_only_one(self):
        self.assertEqual(solve(["a", "b", "c"], ["c", "b", "a"]), 1)

    def test_repeats(self):
        self.assertEqual(solve(["x", "y", "x", "z", "y"], ["x", "y", "y"]), 3)

    def test_empty_route(self):
        self.assertEqual(solve(["a", "b"], []), 0)


if __name__ == "__main__":
    unittest.main()
