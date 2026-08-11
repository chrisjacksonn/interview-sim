"""Sample tests for Room Schedule. A sanity check, not the grade."""

import unittest

from solution import solve


class TestRoomSchedule(unittest.TestCase):
    def test_overlapping_pair(self):
        self.assertEqual(solve([(0, 30), (5, 10), (15, 20)]), 2)

    def test_back_to_back_needs_one(self):
        self.assertEqual(solve([(0, 5), (5, 10), (10, 15)]), 1)

    def test_identical_meetings(self):
        self.assertEqual(solve([(1, 4), (1, 4), (1, 4)]), 3)

    def test_empty(self):
        self.assertEqual(solve([]), 0)


if __name__ == "__main__":
    unittest.main()
