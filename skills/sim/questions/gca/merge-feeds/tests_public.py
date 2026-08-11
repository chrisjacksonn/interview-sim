"""Sample tests for Merge Feeds. A sanity check, not the grade."""

import unittest

from solution import solve


class TestMergeFeeds(unittest.TestCase):
    def test_merges_across_feeds(self):
        self.assertEqual(solve([[1, 4, 9], [2, 3], [5]], 4), [1, 2, 3, 4])

    def test_duplicates_each_count(self):
        self.assertEqual(solve([[1, 1, 1], [1]], 3), [1, 1, 1])

    def test_limit_beyond_the_total(self):
        self.assertEqual(solve([[7], [8]], 10), [7, 8])

    def test_zero_limit(self):
        self.assertEqual(solve([[1, 2, 3]], 0), [])

    def test_no_feeds(self):
        self.assertEqual(solve([], 5), [])


if __name__ == "__main__":
    unittest.main()
