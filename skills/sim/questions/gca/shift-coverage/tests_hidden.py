"""Hidden suite for Shift Coverage.

Never copied into a session workspace.
"""

import unittest

from solution import solve


class TestShiftCoverage(unittest.TestCase):
    # --- the happy path ---

    def test_basic(self):
        self.assertEqual(solve([(0, 4), (2, 8), (7, 10)], 10), 3)

    def test_single_shift_covers_everything(self):
        self.assertEqual(solve([(0, 100)], 100), 1)

    def test_shift_overshooting_the_horizon(self):
        self.assertEqual(solve([(0, 500)], 10), 1)

    def test_exactly_meeting_shifts_leave_no_gap(self):
        self.assertEqual(solve([(0, 5), (5, 9)], 9), 2)

    # --- the greedy choice ---

    def test_must_take_the_furthest_reaching(self):
        # Taking (1, 6) second instead of (1, 9) strands the run after 6.
        self.assertEqual(solve([(0, 5), (1, 6), (1, 9)], 9), 2)

    def test_nested_shift_is_never_worth_taking(self):
        self.assertEqual(solve([(0, 10), (2, 4), (3, 5)], 10), 1)

    def test_greedy_beats_taking_the_earliest_ending(self):
        self.assertEqual(solve([(0, 2), (0, 7), (2, 3), (7, 10)], 10), 2)

    def test_long_chain_of_forced_choices(self):
        shifts = [(index, index + 2) for index in range(0, 20)]
        # Each step advances 2, so covering 0 to 20 takes 10 of them.
        self.assertEqual(solve(shifts, 20), 10)

    # --- impossible ---

    def test_gap_in_the_middle(self):
        self.assertEqual(solve([(0, 3), (5, 9)], 9), -1)

    def test_nothing_starts_at_zero(self):
        self.assertEqual(solve([(1, 9)], 9), -1)

    def test_coverage_stops_short_of_the_horizon(self):
        self.assertEqual(solve([(0, 5), (2, 8)], 12), -1)

    def test_no_shifts_at_all(self):
        self.assertEqual(solve([], 5), -1)

    def test_touching_at_a_point_is_not_a_gap_but_stopping_is(self):
        self.assertEqual(solve([(0, 4), (4, 4)], 6), -1)

    # --- degenerate shifts ---

    def test_zero_length_shifts_are_useless(self):
        self.assertEqual(solve([(0, 0), (0, 6)], 6), 1)

    def test_backwards_shift_is_ignored(self):
        self.assertEqual(solve([(9, 2), (0, 9)], 9), 1)

    def test_only_useless_shifts(self):
        self.assertEqual(solve([(0, 0), (3, 3), (5, 1)], 4), -1)

    # --- horizon edge cases ---

    def test_zero_horizon_needs_nothing(self):
        self.assertEqual(solve([(0, 5)], 0), 0)

    def test_zero_horizon_with_no_shifts(self):
        self.assertEqual(solve([], 0), 0)

    # --- input shape ---

    def test_unsorted_input(self):
        self.assertEqual(solve([(7, 10), (0, 4), (2, 8)], 10), 3)

    def test_duplicate_shifts(self):
        self.assertEqual(solve([(0, 5), (0, 5), (5, 9), (5, 9)], 9), 2)

    def test_returns_an_int_not_a_bool_or_float(self):
        result = solve([(0, 5)], 5)
        self.assertIsInstance(result, int)
        self.assertNotIsInstance(result, bool)

    # --- scale ---

    def test_large_input_is_not_quadratic(self):
        """200k shifts, and the answer needs ~67k greedy steps.

        A single sorted sweep does this in well under a second. Rescanning the
        whole list at each step is 1.3e10 operations and will not finish. Sized
        deliberately: at 60k shifts a quadratic solution still squeaked in at
        19s, under the grading timeout, so the test caught nothing.
        """
        shifts = [(index, index + 3) for index in range(200000)]
        self.assertEqual(solve(shifts, 200000), 66667)

    def test_large_horizon_with_few_shifts(self):
        self.assertEqual(solve([(0, 500000000), (500000000, 1000000000)], 1000000000), 2)

    def test_many_useless_shifts_around_a_thin_solution(self):
        shifts = [(index, index) for index in range(20000)]
        shifts.append((0, 10))
        shifts.append((10, 25))
        self.assertEqual(solve(shifts, 25), 2)


if __name__ == "__main__":
    unittest.main()
