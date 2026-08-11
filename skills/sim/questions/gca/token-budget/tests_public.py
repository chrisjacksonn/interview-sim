"""Sample tests for Token Budget. A sanity check, not the grade."""

import unittest

from solution import solve


class TestTokenBudget(unittest.TestCase):
    def test_worked_example(self):
        self.assertEqual(solve([(3, 4), (4, 5), (2, 3)], 6), 8)

    def test_nothing_affordable(self):
        self.assertEqual(solve([(5, 10)], 4), 0)

    def test_free_task_on_a_zero_budget(self):
        self.assertEqual(solve([(0, 7)], 0), 7)

    def test_no_tasks(self):
        self.assertEqual(solve([], 10), 0)


if __name__ == "__main__":
    unittest.main()
