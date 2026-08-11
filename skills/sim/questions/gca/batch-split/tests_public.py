"""Sample tests for Batch Split. A sanity check, not the grade."""

import unittest

from solution import solve


class TestBatchSplit(unittest.TestCase):
    def test_two_crews(self):
        self.assertEqual(solve([7, 2, 5, 10, 8], 2), 18)

    def test_balanced_split(self):
        self.assertEqual(solve([1, 2, 3, 4, 5], 2), 9)

    def test_one_each(self):
        self.assertEqual(solve([5, 5, 5, 5], 4), 5)

    def test_single_parcel(self):
        self.assertEqual(solve([10], 1), 10)


if __name__ == "__main__":
    unittest.main()
