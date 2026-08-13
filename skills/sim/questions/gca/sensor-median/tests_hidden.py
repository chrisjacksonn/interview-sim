"""Hidden suite for Rolling Median. Never copied into a session workspace."""

import unittest

from solution import solve


class TestRollingMedian(unittest.TestCase):
    def test_odd_window(self):
        self.assertEqual(solve([1, 3, 2, 5, 4], 3), [2.0, 3.0, 4.0])

    def test_even_window(self):
        self.assertEqual(solve([1, 2, 3, 4], 2), [1.5, 2.5, 3.5])

    def test_width_one_is_the_readings(self):
        self.assertEqual(solve([4, 1, 7], 1), [4.0, 1.0, 7.0])

    def test_width_equals_length(self):
        self.assertEqual(solve([3, 1, 2], 3), [2.0])

    def test_width_one_more_than_length(self):
        self.assertEqual(solve([1, 2], 3), [])

    def test_zero_width(self):
        self.assertEqual(solve([1, 2, 3], 0), [])

    def test_negative_width(self):
        self.assertEqual(solve([1, 2, 3], -2), [])

    def test_empty_readings(self):
        self.assertEqual(solve([], 3), [])

    def test_unsorted_window(self):
        self.assertEqual(solve([9, 1, 5], 3), [5.0])

    def test_duplicates_within_a_window(self):
        self.assertEqual(solve([2, 2, 2, 2], 2), [2.0, 2.0, 2.0])

    def test_duplicates_do_not_break_removal(self):
        # The value leaving the window also appears elsewhere in it.
        self.assertEqual(solve([1, 1, 2, 1], 3), [1.0, 1.0])

    def test_removes_the_reading_that_left_not_the_smallest(self):
        """The reading sliding out is the largest in its window.

        Anything that keeps the window sorted and then drops its front is
        removing the smallest instead of the one that actually left. That is the
        usual way to get this wrong, and it needs a window whose departing
        reading is not already the minimum to show up at all.
        """
        self.assertEqual(solve([9, 0, 9], 2), [4.5, 4.5])
        self.assertEqual(solve([6, 0, 1, 8, 1], 3), [1.0, 1.0, 1.0])
        self.assertEqual(solve([8, 3, 0, 1, 6], 2), [5.5, 1.5, 0.5, 3.5])

    def test_negative_readings(self):
        self.assertEqual(solve([-5, -1, -3], 3), [-3.0])

    def test_spanning_zero(self):
        self.assertEqual(solve([-2, 0, 2, 4], 2), [-1.0, 1.0, 3.0])

    def test_even_window_averages_the_middle_two(self):
        self.assertEqual(solve([1, 10], 2), [5.5])

    def test_results_are_floats(self):
        for value in solve([1, 2, 3], 3):
            self.assertIsInstance(value, float)

    def test_odd_window_returns_a_float_too(self):
        self.assertIsInstance(solve([7], 1)[0], float)

    def test_number_of_windows(self):
        self.assertEqual(len(solve(list(range(10)), 4)), 7)

    def test_input_is_not_mutated(self):
        readings = [5, 1, 3, 2]
        original = list(readings)
        solve(readings, 2)
        self.assertEqual(readings, original)

    def test_large_input(self):
        readings = [(index * 7919) % 1000 for index in range(50000)]
        result = solve(readings, 100)
        self.assertEqual(len(result), 50000 - 100 + 1)

    def test_large_width_one(self):
        readings = list(range(20000))
        self.assertEqual(solve(readings, 1)[-1], 19999.0)
