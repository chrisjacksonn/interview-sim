"""Sample tests for Repeat Alerts. A sanity check, not the grade."""

import unittest

from solution import solve


class TestRepeatAlerts(unittest.TestCase):
    def test_within_the_window(self):
        self.assertEqual(solve([("disk", 1), ("cpu", 3), ("disk", 4)], 5), ["disk"])

    def test_outside_the_window(self):
        self.assertEqual(solve([("disk", 1), ("disk", 40)], 5), [])

    def test_boundary_is_inclusive(self):
        alerts = [("a", 1), ("a", 6), ("b", 2), ("b", 3)]
        self.assertEqual(solve(alerts, 5), ["a", "b"])

    def test_empty(self):
        self.assertEqual(solve([], 10), [])


if __name__ == "__main__":
    unittest.main()
