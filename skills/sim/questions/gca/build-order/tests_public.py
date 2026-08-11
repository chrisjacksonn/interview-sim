"""Sample tests for Build Order. A sanity check, not the grade."""

import unittest

from solution import solve


class TestBuildOrder(unittest.TestCase):
    def test_simple_chain(self):
        self.assertEqual(solve(["a", "b", "c"], [("a", "b"), ("b", "c")]), ["a", "b", "c"])

    def test_no_requirements_is_alphabetical(self):
        self.assertEqual(solve(["c", "a", "b"], []), ["a", "b", "c"])

    def test_ties_break_alphabetically(self):
        tasks = ["build", "test", "lint"]
        self.assertEqual(solve(tasks, [("build", "test")]), ["build", "lint", "test"])

    def test_cycle_returns_empty(self):
        self.assertEqual(solve(["a", "b"], [("a", "b"), ("b", "a")]), [])

    def test_no_tasks(self):
        self.assertEqual(solve([], []), [])


if __name__ == "__main__":
    unittest.main()
