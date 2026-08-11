"""Hidden suite for Room Schedule. Never copied into a session workspace."""

import unittest

from solution import solve


class TestRoomSchedule(unittest.TestCase):
    def test_worked_example(self):
        self.assertEqual(solve([(0, 30), (5, 10), (15, 20)]), 2)

    def test_single_meeting(self):
        self.assertEqual(solve([(0, 1)]), 1)

    def test_no_meetings(self):
        self.assertEqual(solve([]), 0)

    def test_non_overlapping(self):
        self.assertEqual(solve([(0, 1), (2, 3), (4, 5)]), 1)

    def test_touching_endpoints_do_not_overlap(self):
        # The half-open rule. Treating it as closed gives 2.
        self.assertEqual(solve([(0, 5), (5, 10)]), 1)

    def test_long_chain_of_touching_meetings(self):
        meetings = [(index, index + 1) for index in range(1000)]
        self.assertEqual(solve(meetings), 1)

    def test_one_instant_of_overlap(self):
        self.assertEqual(solve([(0, 6), (5, 10)]), 2)

    def test_fully_nested(self):
        self.assertEqual(solve([(0, 100), (10, 20), (12, 15)]), 3)

    def test_staircase(self):
        self.assertEqual(solve([(0, 10), (1, 11), (2, 12), (3, 13)]), 4)

    def test_identical_meetings(self):
        self.assertEqual(solve([(1, 4), (1, 4), (1, 4)]), 3)

    def test_peak_is_not_the_total(self):
        # Six meetings but never more than two at once.
        meetings = [(0, 2), (1, 3), (4, 6), (5, 7), (8, 10), (9, 11)]
        self.assertEqual(solve(meetings), 2)

    def test_peak_in_the_middle(self):
        meetings = [(0, 20), (5, 6), (5, 6), (5, 6), (18, 19)]
        self.assertEqual(solve(meetings), 4)

    def test_unsorted_input(self):
        self.assertEqual(solve([(15, 20), (0, 30), (5, 10)]), 2)

    def test_reverse_sorted_input(self):
        self.assertEqual(solve([(20, 25), (10, 15), (0, 5)]), 1)

    def test_zero_length_meeting_is_ignored(self):
        self.assertEqual(solve([(5, 5)]), 0)

    def test_zero_length_alongside_a_real_one(self):
        self.assertEqual(solve([(5, 5), (0, 10)]), 1)

    def test_backwards_meeting_is_ignored(self):
        self.assertEqual(solve([(10, 2), (0, 1)]), 1)

    def test_backwards_meeting_cannot_suppress_a_real_peak(self):
        """The reason a backwards meeting must be dropped, not just tolerated.

        A zero-length meeting cancels itself out harmlessly, so it is tempting
        to skip the filter. A backwards one does not: its endpoints arrive in
        the wrong order, so the release lands at 5 and the claim at 30, and any
        genuine overlap in between is counted one room short.
        """
        self.assertEqual(solve([(6, 10), (7, 10), (30, 5)]), 2)

    def test_only_degenerate_meetings(self):
        self.assertEqual(solve([(5, 5), (9, 3)]), 0)

    def test_negative_times(self):
        self.assertEqual(solve([(-10, -5), (-7, -1)]), 2)

    def test_spanning_zero(self):
        self.assertEqual(solve([(-5, 5), (0, 1)]), 2)

    def test_returns_an_int_not_a_bool(self):
        result = solve([(0, 1)])
        self.assertIsInstance(result, int)
        self.assertNotIsInstance(result, bool)

    def test_large_all_overlapping(self):
        meetings = [(0, 1000000) for _ in range(20000)]
        self.assertEqual(solve(meetings), 20000)

    def test_large_all_sequential(self):
        meetings = [(index, index + 1) for index in range(100000)]
        self.assertEqual(solve(meetings), 1)

    def test_large_mixed_is_not_quadratic(self):
        meetings = [(index, index + 3) for index in range(100000)]
        self.assertEqual(solve(meetings), 3)
