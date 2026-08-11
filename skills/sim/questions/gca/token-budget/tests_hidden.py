"""Hidden suite for Token Budget. Never copied into a session workspace."""

import unittest

from solution import solve


class TestTokenBudget(unittest.TestCase):
    def test_worked_example(self):
        self.assertEqual(solve([(3, 4), (4, 5), (2, 3)], 6), 8)

    def test_single_affordable_task(self):
        self.assertEqual(solve([(3, 9)], 5), 9)

    def test_single_unaffordable_task(self):
        self.assertEqual(solve([(6, 9)], 5), 0)

    def test_exact_budget(self):
        self.assertEqual(solve([(5, 12)], 5), 12)

    def test_take_everything(self):
        self.assertEqual(solve([(1, 1), (2, 2), (3, 3)], 100), 6)

    # --- each task at most once, which is the whole question ---

    def test_a_task_cannot_be_taken_twice(self):
        """Budget 10 with one task costing 5.

        Taking it twice gives 20. The inner loop has to run downward, and the
        upward version silently allows repeats.
        """
        self.assertEqual(solve([(5, 10)], 10), 10)

    def test_a_task_cannot_be_taken_four_times(self):
        self.assertEqual(solve([(1, 3)], 4), 3)

    def test_repeats_would_beat_the_honest_answer(self):
        # Repeating the cheap task gives 15; taking each once gives 11.
        self.assertEqual(solve([(1, 3), (4, 8)], 5), 11)

    # --- choosing well ---

    def test_greedy_by_value_is_wrong(self):
        # Highest value first takes (5, 9) for 9. The pair is worth 10.
        self.assertEqual(solve([(5, 9), (3, 5), (2, 5)], 5), 10)

    def test_greedy_by_ratio_is_wrong(self):
        # Best ratio is (1, 2). Taking it strands the budget at 2 value; the
        # single heavy task is worth 3.
        self.assertEqual(solve([(1, 2), (2, 3)], 2), 3)

    def test_leaving_budget_unspent_can_be_optimal(self):
        self.assertEqual(solve([(3, 100)], 10), 100)

    # --- zeros ---

    def test_free_task_on_zero_budget(self):
        self.assertEqual(solve([(0, 7)], 0), 7)

    def test_several_free_tasks(self):
        self.assertEqual(solve([(0, 3), (0, 4)], 0), 7)

    def test_free_tasks_alongside_paid_ones(self):
        self.assertEqual(solve([(0, 5), (3, 4)], 3), 9)

    def test_zero_value_tasks_are_harmless(self):
        self.assertEqual(solve([(2, 0), (2, 5)], 2), 5)

    def test_zero_budget_with_only_paid_tasks(self):
        self.assertEqual(solve([(1, 100)], 0), 0)

    def test_all_zero(self):
        self.assertEqual(solve([(0, 0)], 0), 0)

    # --- empties ---

    def test_no_tasks(self):
        self.assertEqual(solve([], 10), 0)

    def test_no_tasks_no_budget(self):
        self.assertEqual(solve([], 0), 0)

    # --- shape ---

    def test_returns_an_int_not_a_bool(self):
        result = solve([(1, 1)], 1)
        self.assertIsInstance(result, int)
        self.assertNotIsInstance(result, bool)

    def test_input_is_not_mutated(self):
        tasks = [(3, 4), (4, 5)]
        original = list(tasks)
        solve(tasks, 6)
        self.assertEqual(tasks, original)

    # --- scale ---

    def test_large_is_not_exponential(self):
        # 400 tasks. Enumerating subsets is 2**400.
        tasks = [((index % 97) + 1, (index % 31) + 1) for index in range(400)]
        result = solve(tasks, 5000)
        self.assertGreater(result, 0)

    def test_large_budget(self):
        tasks = [(index + 1, index + 1) for index in range(400)]
        # Costs equal values, so the answer is capped by the budget itself.
        self.assertEqual(solve(tasks, 20000), min(20000, sum(i + 1 for i in range(400))))

    def test_many_free_tasks(self):
        tasks = [(0, 2)] * 300
        self.assertEqual(solve(tasks, 0), 600)
