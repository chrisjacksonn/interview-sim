"""Hidden suite for Build Order.

Never copied into a session workspace.
"""

import unittest

from solution import solve


class TestBuildOrder(unittest.TestCase):
    # --- ordering ---

    def test_simple_chain(self):
        self.assertEqual(solve(["a", "b", "c"], [("a", "b"), ("b", "c")]), ["a", "b", "c"])

    def test_chain_given_out_of_order(self):
        tasks = ["c", "a", "b"]
        requirements = [("b", "c"), ("a", "b")]
        self.assertEqual(solve(tasks, requirements), ["a", "b", "c"])

    def test_no_requirements_is_purely_alphabetical(self):
        self.assertEqual(solve(["delta", "alpha", "charlie"], []), ["alpha", "charlie", "delta"])

    def test_alphabetical_tie_break_is_dynamic_not_a_pre_sort(self):
        """The ready set changes as tasks complete.

        Sorting the whole list up front gives ["a", "b", "z"], which violates
        the requirement that z runs before b.
        """
        tasks = ["a", "b", "z"]
        self.assertEqual(solve(tasks, [("z", "b")]), ["a", "z", "b"])

    def test_blocked_alphabetically_first_task_waits(self):
        tasks = ["a", "b"]
        self.assertEqual(solve(tasks, [("b", "a")]), ["b", "a"])

    def test_diamond(self):
        tasks = ["a", "b", "c", "d"]
        requirements = [("a", "b"), ("a", "c"), ("b", "d"), ("c", "d")]
        self.assertEqual(solve(tasks, requirements), ["a", "b", "c", "d"])

    def test_two_independent_chains_interleave_alphabetically(self):
        tasks = ["a1", "a2", "b1", "b2"]
        requirements = [("a1", "a2"), ("b1", "b2")]
        self.assertEqual(solve(tasks, requirements), ["a1", "a2", "b1", "b2"])

    def test_later_task_unblocks_an_earlier_name(self):
        tasks = ["m", "z", "a"]
        requirements = [("z", "a")]
        self.assertEqual(solve(tasks, requirements), ["m", "z", "a"])

    # --- cycles ---

    def test_two_task_cycle(self):
        self.assertEqual(solve(["a", "b"], [("a", "b"), ("b", "a")]), [])

    def test_three_task_cycle(self):
        tasks = ["a", "b", "c"]
        requirements = [("a", "b"), ("b", "c"), ("c", "a")]
        self.assertEqual(solve(tasks, requirements), [])

    def test_self_requirement_is_a_cycle(self):
        self.assertEqual(solve(["a"], [("a", "a")]), [])

    def test_cycle_in_one_component_kills_the_whole_answer(self):
        # Catches solutions that return the part they managed to order.
        tasks = ["a", "b", "x", "y"]
        requirements = [("x", "y"), ("y", "x")]
        self.assertEqual(solve(tasks, requirements), [])

    def test_no_cycle_despite_a_shared_dependency(self):
        tasks = ["a", "b", "c"]
        requirements = [("a", "c"), ("b", "c")]
        self.assertEqual(solve(tasks, requirements), ["a", "b", "c"])

    # --- awkward input ---

    def test_requirement_naming_an_unknown_task_is_ignored(self):
        self.assertEqual(solve(["a", "b"], [("a", "ghost"), ("a", "b")]), ["a", "b"])

    def test_requirement_entirely_about_unknown_tasks(self):
        self.assertEqual(solve(["a"], [("x", "y")]), ["a"])

    def test_unknown_task_cannot_create_a_phantom_cycle(self):
        self.assertEqual(solve(["a"], [("ghost", "a"), ("a", "ghost")]), ["a"])

    def test_duplicate_requirements_are_harmless(self):
        # Counting a duplicate twice leaves a task permanently blocked.
        tasks = ["a", "b"]
        requirements = [("a", "b"), ("a", "b"), ("a", "b")]
        self.assertEqual(solve(tasks, requirements), ["a", "b"])

    def test_empty_tasks(self):
        self.assertEqual(solve([], []), [])

    def test_empty_tasks_with_requirements(self):
        self.assertEqual(solve([], [("a", "b")]), [])

    def test_single_task(self):
        self.assertEqual(solve(["only"], []), ["only"])

    # --- names ---

    def test_names_are_case_sensitive_and_uppercase_sorts_first(self):
        self.assertEqual(solve(["b", "A"], []), ["A", "b"])

    def test_every_task_appears_exactly_once(self):
        tasks = ["a", "b", "c", "d"]
        requirements = [("a", "b"), ("a", "c"), ("a", "d")]
        result = solve(tasks, requirements)
        self.assertEqual(sorted(result), sorted(tasks))
        self.assertEqual(len(result), len(set(result)))

    # --- shape and scale ---

    def test_returns_a_list(self):
        self.assertIsInstance(solve(["a"], []), list)

    def test_long_chain_does_not_recurse_to_death(self):
        tasks = ["t%05d" % index for index in range(4000)]
        requirements = [(tasks[i], tasks[i + 1]) for i in range(len(tasks) - 1)]
        self.assertEqual(solve(tasks, requirements), tasks)

    def test_wide_graph(self):
        tasks = ["root"] + ["leaf%04d" % index for index in range(3000)]
        requirements = [("root", "leaf%04d" % index) for index in range(3000)]
        result = solve(tasks, requirements)
        self.assertEqual(result[0], "root")
        self.assertEqual(len(result), 3001)

    def test_large_cycle_is_detected(self):
        tasks = ["t%05d" % index for index in range(3000)]
        requirements = [(tasks[i], tasks[(i + 1) % len(tasks)]) for i in range(len(tasks))]
        self.assertEqual(solve(tasks, requirements), [])


if __name__ == "__main__":
    unittest.main()
