"""Sample tests for Sensor Gaps.

A sanity check, not the grade.
"""

import unittest

from solution import solve


class TestSensorGaps(unittest.TestCase):
    def test_longest_gap_after_ordering(self):
        readings = [("s1", 100), ("s2", 40), ("s1", 250), ("s1", 130)]
        self.assertEqual(solve(readings), {"s1": 120})

    def test_identical_timestamps_are_a_zero_gap(self):
        self.assertEqual(solve([("a", 5), ("a", 5)]), {"a": 0})

    def test_negative_timestamps(self):
        readings = [("x", 10), ("x", -10), ("y", 3), ("y", 8), ("y", 4)]
        self.assertEqual(solve(readings), {"x": 20, "y": 4})

    def test_empty_input(self):
        self.assertEqual(solve([]), {})


if __name__ == "__main__":
    unittest.main()
