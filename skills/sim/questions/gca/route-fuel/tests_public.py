"""Sample tests for Route Fuel. A sanity check, not the grade."""

import unittest

from solution import solve


class TestRouteFuel(unittest.TestCase):
    def test_two_stops(self):
        self.assertEqual(solve(100, 10, [(10, 60), (20, 30), (30, 30), (60, 40)]), 2)

    def test_no_stops_needed(self):
        self.assertEqual(solve(100, 100, []), 0)

    def test_unreachable(self):
        self.assertEqual(solve(100, 1, [(10, 100)]), -1)

    def test_every_depot_needed(self):
        self.assertEqual(solve(100, 50, [(25, 25), (50, 25)]), 2)


if __name__ == "__main__":
    unittest.main()
