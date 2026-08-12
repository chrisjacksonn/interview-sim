"""Hidden suite for Quiet Streaks. Never copied into a session workspace."""

import unittest

from solution import solve


class TestQuietStreaks(unittest.TestCase):
    def test_longest_of_several(self):
        self.assertEqual(solve([3, 0, 0, 1, 0, 0, 0, 2]), 3)

    def test_all_zero(self):
        self.assertEqual(solve([0, 0, 0]), 3)

    def test_no_zeros(self):
        self.assertEqual(solve([1, 2, 3]), 0)

    def test_empty(self):
        self.assertEqual(solve([]), 0)

    def test_single_zero(self):
        self.assertEqual(solve([0]), 1)

    def test_single_nonzero(self):
        self.assertEqual(solve([5]), 0)

    def test_streak_at_the_start(self):
        self.assertEqual(solve([0, 0, 0, 1, 0]), 3)

    def test_streak_at_the_end(self):
        self.assertEqual(solve([1, 0, 0, 0]), 3)

    def test_streak_in_the_middle(self):
        self.assertEqual(solve([1, 0, 0, 0, 1]), 3)

    def test_two_equal_streaks(self):
        self.assertEqual(solve([0, 0, 5, 0, 0]), 2)

    def test_later_streak_is_longer(self):
        self.assertEqual(solve([0, 0, 5, 0, 0, 0]), 3)

    def test_earlier_streak_is_longer(self):
        self.assertEqual(solve([0, 0, 0, 5, 0]), 3)

    def test_alternating(self):
        self.assertEqual(solve([0, 1] * 50), 1)

    def test_large_counts_are_not_zero(self):
        self.assertEqual(solve([10 ** 9, 0, 10 ** 9]), 1)

    def test_returns_an_int_not_a_bool(self):
        result = solve([0])
        self.assertIsInstance(result, int)
        self.assertNotIsInstance(result, bool)

    def test_input_is_not_mutated(self):
        counts = [1, 0, 0, 2]
        original = list(counts)
        solve(counts)
        self.assertEqual(counts, original)

    def test_large_all_zero(self):
        self.assertEqual(solve([0] * 200000), 200000)

    def test_large_no_zeros(self):
        self.assertEqual(solve([1] * 200000), 0)

    def test_large_streak_at_the_end(self):
        self.assertEqual(solve([1] * 100000 + [0] * 5000), 5000)
