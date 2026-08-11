"""Hidden suite for Pack Combinations.

Never copied into a session workspace.
"""

import unittest

from solution import solve


class TestPackCombinations(unittest.TestCase):
    # --- worked cases ---

    def test_worked_example(self):
        self.assertEqual(solve([1, 2, 5], 5), 4)

    def test_single_size_that_divides(self):
        self.assertEqual(solve([3], 9), 1)

    def test_single_size_that_does_not_divide(self):
        self.assertEqual(solve([3], 10), 0)

    def test_ones_only(self):
        self.assertEqual(solve([1], 50), 1)

    def test_two_sizes(self):
        # 0..3 twos paired with the right number of ones.
        self.assertEqual(solve([1, 2], 6), 4)

    # --- order must not matter ---

    def test_combinations_not_permutations(self):
        """The central trap.

        With sizes 1 and 2 and a target of 4 the combinations are 1+1+1+1,
        1+1+2 and 2+2, so three. Counting orderings instead gives five, because
        1+1+2, 1+2+1 and 2+1+1 are then all distinct.
        """
        self.assertEqual(solve([1, 2], 4), 3)

    def test_combinations_not_permutations_larger(self):
        # Orderings would give 13 here; combinations give 4.
        self.assertEqual(solve([1, 2, 3], 5), 5)

    def test_two_sizes_one_target_each_way(self):
        self.assertEqual(solve([2, 3], 5), 1)

    def test_size_order_in_the_input_does_not_matter(self):
        self.assertEqual(solve([5, 2, 1], 5), solve([1, 2, 5], 5))

    def test_reversed_input(self):
        self.assertEqual(solve([3, 2, 1], 8), solve([1, 2, 3], 8))

    # --- duplicates in the input ---

    def test_duplicate_sizes_do_not_multiply_the_answer(self):
        self.assertEqual(solve([2, 2], 4), solve([2], 4))

    def test_duplicate_sizes_among_others(self):
        self.assertEqual(solve([1, 2, 2, 5], 5), solve([1, 2, 5], 5))

    def test_all_duplicates(self):
        self.assertEqual(solve([3, 3, 3], 9), 1)

    # --- edges ---

    def test_target_zero_with_sizes(self):
        self.assertEqual(solve([3, 5], 0), 1)

    def test_target_zero_without_sizes(self):
        self.assertEqual(solve([], 0), 1)

    def test_no_sizes_nonzero_target(self):
        self.assertEqual(solve([], 7), 0)

    def test_size_larger_than_the_target(self):
        self.assertEqual(solve([100], 5), 0)

    def test_size_equal_to_the_target(self):
        self.assertEqual(solve([5], 5), 1)

    def test_mix_of_usable_and_oversized(self):
        self.assertEqual(solve([1, 100, 200], 3), 1)

    def test_target_of_one(self):
        self.assertEqual(solve([1, 2, 3], 1), 1)

    # --- shape ---

    def test_returns_an_int_not_a_bool(self):
        result = solve([1], 1)
        self.assertIsInstance(result, int)
        self.assertNotIsInstance(result, bool)

    def test_input_is_not_mutated(self):
        sizes = [5, 2, 1]
        original = list(sizes)
        solve(sizes, 7)
        self.assertEqual(sizes, original)

    # --- scale ---

    def test_large_target_is_not_exponential(self):
        # Enumerating combinations of these over 10k units will not finish.
        result = solve([1, 2, 5, 10, 25], 10000)
        self.assertGreater(result, 0)
        self.assertIsInstance(result, int)

    def test_many_sizes(self):
        sizes = list(range(1, 201))
        result = solve(sizes, 2000)
        self.assertGreater(result, 0)

    def test_answer_can_exceed_a_machine_word(self):
        # Twenty-two digits, so anything reporting the count modulo a prime, or
        # doing the arithmetic in a fixed-width type, gets this wrong.
        result = solve(list(range(1, 11)), 5000)
        self.assertGreater(result, 2 ** 64)

    def test_known_large_value(self):
        # Ones and twos: one combination per count of twos, floor(n/2) + 1.
        self.assertEqual(solve([1, 2], 20000), 10001)


if __name__ == "__main__":
    unittest.main()
