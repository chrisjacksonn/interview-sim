"""Hidden suite for Merge Feeds.

Never copied into a session workspace.
"""

import unittest

from solution import solve


class TestMergeFeeds(unittest.TestCase):
    # --- merging ---

    def test_basic(self):
        self.assertEqual(solve([[1, 4, 9], [2, 3], [5]], 4), [1, 2, 3, 4])

    def test_takes_everything_in_order(self):
        self.assertEqual(solve([[1, 4, 9], [2, 3], [5]], 6), [1, 2, 3, 4, 5, 9])

    def test_single_feed(self):
        self.assertEqual(solve([[3, 6, 9]], 2), [3, 6])

    def test_one_element_per_feed(self):
        self.assertEqual(solve([[5], [1], [3]], 3), [1, 3, 5])

    def test_feeds_do_not_overlap(self):
        self.assertEqual(solve([[1, 2, 3], [10, 11]], 5), [1, 2, 3, 10, 11])

    def test_second_feed_entirely_before_the_first(self):
        self.assertEqual(solve([[10, 11], [1, 2]], 3), [1, 2, 10])

    def test_interleaved(self):
        self.assertEqual(solve([[1, 3, 5], [2, 4, 6]], 6), [1, 2, 3, 4, 5, 6])

    # --- duplicates ---

    def test_duplicates_within_one_feed(self):
        self.assertEqual(solve([[2, 2, 2]], 3), [2, 2, 2])

    def test_duplicates_across_feeds(self):
        self.assertEqual(solve([[1, 1, 1], [1]], 3), [1, 1, 1])

    def test_duplicates_are_not_deduplicated(self):
        # Catches anything routed through a set.
        self.assertEqual(solve([[5, 5], [5, 5]], 4), [5, 5, 5, 5])

    def test_identical_feeds_do_not_break_tie_ordering(self):
        # Feeds with equal leading values must never be compared to each other.
        self.assertEqual(solve([[1, 2], [1, 3], [1, 4]], 4), [1, 1, 1, 2])

    # --- empties ---

    def test_empty_feeds_are_skipped(self):
        self.assertEqual(solve([[], [1, 2], []], 2), [1, 2])

    def test_all_feeds_empty(self):
        self.assertEqual(solve([[], [], []], 3), [])

    def test_no_feeds_at_all(self):
        self.assertEqual(solve([], 5), [])

    def test_leading_empty_feed(self):
        self.assertEqual(solve([[], [4, 5]], 1), [4])

    # --- limit handling ---

    def test_limit_of_zero(self):
        self.assertEqual(solve([[1, 2, 3]], 0), [])

    def test_negative_limit(self):
        # A plain slice would return everything but the last element here.
        self.assertEqual(solve([[1, 2, 3]], -2), [])

    def test_limit_of_one(self):
        self.assertEqual(solve([[9, 10], [3, 4]], 1), [3])

    def test_limit_beyond_the_total(self):
        self.assertEqual(solve([[7], [8]], 100), [7, 8])

    def test_limit_exactly_the_total(self):
        self.assertEqual(solve([[1, 2], [3]], 3), [1, 2, 3])

    # --- values ---

    def test_negative_readings(self):
        self.assertEqual(solve([[-5, -1], [-3, 0]], 3), [-5, -3, -1])

    def test_mixed_signs(self):
        self.assertEqual(solve([[-2, 4], [-1, 3]], 4), [-2, -1, 3, 4])

    def test_zero_is_a_real_reading(self):
        self.assertEqual(solve([[0], [0]], 2), [0, 0])

    # --- shape ---

    def test_returns_a_list(self):
        self.assertIsInstance(solve([[1]], 1), list)

    def test_input_feeds_are_not_mutated(self):
        # Catches solutions that pop from the caller's lists, and solutions that
        # sort the outer list in place. The feeds are given out of order on
        # purpose: a list that is already sorted cannot show whether an in-place
        # sort disturbed it, which makes the check pass for the wrong reason.
        feeds = [[2, 3], [1, 4]]
        snapshot = [list(feed) for feed in feeds]
        solve(feeds, 3)
        self.assertEqual(feeds, snapshot)

    # --- scale ---

    def test_small_limit_over_a_huge_input(self):
        """5 readings wanted out of 400k.

        Sorting everything works but is wasteful; the point of the heap is that
        the cost tracks the limit, not the input.
        """
        feeds = [[base * 100000 + step for step in range(40000)] for base in range(10)]
        self.assertEqual(solve(feeds, 5), [0, 1, 2, 3, 4])

    def test_many_feeds(self):
        feeds = [[index] for index in range(10000)]
        self.assertEqual(solve(feeds, 4), [0, 1, 2, 3])

    def test_large_limit(self):
        feeds = [list(range(index, 100000, 5)) for index in range(5)]
        result = solve(feeds, 1000)
        self.assertEqual(len(result), 1000)
        self.assertEqual(result, sorted(result))
        self.assertEqual(result[0], 0)


if __name__ == "__main__":
    unittest.main()
