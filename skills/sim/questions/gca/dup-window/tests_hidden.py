"""Hidden suite for Repeat Alerts. Never copied into a session workspace."""

import unittest

from solution import solve


class TestRepeatAlerts(unittest.TestCase):
    def test_basic(self):
        self.assertEqual(solve([("disk", 1), ("cpu", 3), ("disk", 4)], 5), ["disk"])

    def test_outside_the_window(self):
        self.assertEqual(solve([("disk", 1), ("disk", 40)], 5), [])

    def test_boundary_is_inclusive(self):
        self.assertEqual(solve([("a", 1), ("a", 6)], 5), ["a"])

    def test_one_past_the_boundary(self):
        self.assertEqual(solve([("a", 1), ("a", 7)], 5), [])

    def test_result_is_sorted(self):
        alerts = [("zed", 1), ("zed", 2), ("amy", 1), ("amy", 2)]
        self.assertEqual(solve(alerts, 5), ["amy", "zed"])

    def test_each_name_appears_once(self):
        alerts = [("a", 1), ("a", 2), ("a", 3), ("a", 4)]
        self.assertEqual(solve(alerts, 5), ["a"])

    def test_unsorted_input(self):
        self.assertEqual(solve([("a", 40), ("a", 1), ("a", 3)], 5), ["a"])

    def test_out_of_order_and_far_apart(self):
        """Descending arrivals that are not noisy.

        Comparing timestamps in arrival order gives a negative gap here, and a
        negative gap is always within a non-negative window, so anything that
        skips the sort calls this noisy.
        """
        self.assertEqual(solve([("a", 100), ("a", 1)], 5), [])
        self.assertEqual(solve([("a", 30), ("a", 20), ("a", 10)], 5), [])

    def test_only_the_close_pair_counts(self):
        self.assertEqual(solve([("a", 0), ("a", 100), ("a", 103)], 5), ["a"])

    def test_single_alert_is_never_noisy(self):
        self.assertEqual(solve([("a", 1)], 100), [])

    def test_names_are_case_sensitive(self):
        self.assertEqual(solve([("A", 1), ("a", 2)], 5), [])

    def test_identical_timestamps(self):
        self.assertEqual(solve([("a", 5), ("a", 5)], 0), ["a"])

    def test_zero_window_needs_an_exact_match(self):
        self.assertEqual(solve([("a", 5), ("a", 6)], 0), [])

    def test_negative_window_is_never_noisy(self):
        self.assertEqual(solve([("a", 5), ("a", 5)], -1), [])

    def test_negative_timestamps(self):
        self.assertEqual(solve([("a", -10), ("a", -8)], 5), ["a"])

    def test_spanning_zero(self):
        self.assertEqual(solve([("a", -2), ("a", 2)], 5), ["a"])

    def test_empty_input(self):
        result = solve([], 10)
        self.assertEqual(result, [])
        self.assertIsInstance(result, list)

    def test_input_is_not_mutated(self):
        """The order has to be one sorting would disturb, or an in-place sort
        looks like it left the list alone."""
        alerts = [("zed", 9), ("amy", 4), ("zed", 1), ("amy", 40)]
        original = list(alerts)
        solve(alerts, 5)
        self.assertEqual(alerts, original)

    def test_many_names_none_noisy(self):
        alerts = [("n%d" % index, index * 100) for index in range(2000)]
        self.assertEqual(solve(alerts, 5), [])

    def test_large_input(self):
        alerts = []
        for index in range(50000):
            alerts.append(("quiet%d" % index, index * 1000))
        alerts.append(("noisy", 1))
        alerts.append(("noisy", 2))
        self.assertEqual(solve(alerts, 5), ["noisy"])
