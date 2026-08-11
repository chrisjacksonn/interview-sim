"""Hidden suite for Log Window. Never copied into a session workspace."""

import unittest

from solution import solve


class TestLogWindow(unittest.TestCase):
    def test_worked_example(self):
        self.assertEqual(solve([1, 4, 2, 10, 2, 3, 1, 0, 20], 4), 24)

    def test_best_window_at_the_start(self):
        self.assertEqual(solve([9, 9, 1, 1, 1], 2), 18)

    def test_best_window_in_the_middle(self):
        self.assertEqual(solve([1, 1, 9, 9, 1, 1], 2), 18)

    def test_best_window_at_the_end(self):
        self.assertEqual(solve([1, 1, 1, 9, 9], 2), 18)

    def test_width_of_one_is_the_maximum(self):
        self.assertEqual(solve([3, 7, 2], 1), 7)

    def test_width_equal_to_the_length(self):
        self.assertEqual(solve([3, 7, 2], 3), 12)

    def test_width_one_more_than_the_length(self):
        self.assertEqual(solve([3, 7, 2], 4), 0)

    def test_width_zero(self):
        self.assertEqual(solve([3, 7, 2], 0), 0)

    def test_negative_width(self):
        self.assertEqual(solve([3, 7, 2], -2), 0)

    def test_empty_counts(self):
        self.assertEqual(solve([], 3), 0)

    def test_empty_counts_zero_width(self):
        self.assertEqual(solve([], 0), 0)

    def test_all_zeros(self):
        self.assertEqual(solve([0, 0, 0, 0], 2), 0)

    def test_zeros_and_a_spike(self):
        self.assertEqual(solve([0, 0, 50, 0, 0], 3), 50)

    def test_ties_between_windows(self):
        self.assertEqual(solve([5, 1, 5, 1, 5], 2), 6)

    def test_uniform_counts(self):
        self.assertEqual(solve([4] * 10, 3), 12)

    def test_two_buckets_width_two(self):
        self.assertEqual(solve([1, 2], 2), 3)

    def test_returns_an_int_not_a_bool(self):
        result = solve([1], 1)
        self.assertIsInstance(result, int)
        self.assertNotIsInstance(result, bool)

    def test_input_is_not_mutated(self):
        counts = [1, 4, 2, 10]
        original = list(counts)
        solve(counts, 2)
        self.assertEqual(counts, original)

    def test_large_input_is_not_quadratic(self):
        # 300k buckets with a width of 1000. Re-summing each window is 3e8 adds.
        counts = [(index % 17) for index in range(300000)]
        result = solve(counts, 1000)
        self.assertGreater(result, 0)

    def test_large_uniform(self):
        self.assertEqual(solve([2] * 200000, 100000), 200000)

    def test_large_spike_at_the_very_end(self):
        counts = [0] * 200000 + [7] * 10
        self.assertEqual(solve(counts, 10), 70)

    def test_large_width_of_one(self):
        counts = [index % 9999 for index in range(250000)]
        self.assertEqual(solve(counts, 1), 9998)
