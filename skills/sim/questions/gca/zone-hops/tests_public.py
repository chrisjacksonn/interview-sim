"""Sample tests for Zone Hops.

A sanity check, not the grade.
"""

import unittest

from solution import solve


class TestZoneHops(unittest.TestCase):
    def test_shortest_route_wins(self):
        conveyors = [("A", "B"), ("B", "C"), ("A", "C"), ("C", "D")]
        self.assertEqual(solve(conveyors, "A"), {"A": 0, "B": 1, "C": 1, "D": 2})

    def test_unreachable_zones_are_absent(self):
        self.assertEqual(solve([("A", "B"), ("C", "D")], "A"), {"A": 0, "B": 1})

    def test_isolated_start(self):
        self.assertEqual(solve([], "solo"), {"solo": 0})

    def test_conveyors_are_one_way(self):
        self.assertEqual(solve([("A", "B"), ("B", "A")], "B"), {"B": 0, "A": 1})


if __name__ == "__main__":
    unittest.main()
