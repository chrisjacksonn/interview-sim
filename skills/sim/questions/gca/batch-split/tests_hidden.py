"""Hidden suite for Batch Split.

Never copied into a session workspace.
"""

import unittest

from solution import solve


class TestBatchSplit(unittest.TestCase):
    # --- worked cases ---

    def test_basic(self):
        self.assertEqual(solve([7, 2, 5, 10, 8], 2), 18)

    def test_balanced_split_is_better_than_the_obvious_one(self):
        self.assertEqual(solve([1, 2, 3, 4, 5], 2), 9)

    def test_three_crews(self):
        self.assertEqual(solve([7, 2, 5, 10, 8], 3), 14)

    def test_four_crews(self):
        self.assertEqual(solve([7, 2, 5, 10, 8], 4), 10)

    # --- the ends of the range ---

    def test_one_crew_takes_everything(self):
        self.assertEqual(solve([1, 2, 3, 4], 1), 10)

    def test_one_crew_per_parcel(self):
        self.assertEqual(solve([4, 1, 7, 2], 4), 7)

    def test_single_parcel_single_crew(self):
        self.assertEqual(solve([10], 1), 10)

    def test_answer_is_never_below_the_heaviest_parcel(self):
        # No group can be lighter than its heaviest member, even with many crews.
        self.assertEqual(solve([1, 1, 100, 1, 1], 4), 100)

    # --- order is fixed ---

    def test_order_cannot_be_rearranged(self):
        """The heavy parcel is stranded in the middle.

        Every in-order split leaves it grouped with at least one neighbour, so
        the answer is 10. Sorting first would allow [1,1,1] and [9] for 9, which
        is why a solution that sorts gets this wrong. Note the heavy item cannot
        simply be first, since [9] and [1,1,1] is a legal in-order split that
        also gives 9.
        """
        self.assertEqual(solve([1, 9, 1, 1], 2), 10)

    def test_sorting_can_also_make_the_answer_look_worse(self):
        # Sorted gives [2,2,8,8] -> 12. In order, [2,8] and [2,8] gives 10.
        self.assertEqual(solve([2, 8, 2, 8], 2), 10)

    def test_heavy_parcel_first_is_not_stranded(self):
        self.assertEqual(solve([9, 1, 1, 1], 2), 9)

    # --- zeros and flat inputs ---

    def test_all_zero_weights(self):
        self.assertEqual(solve([0, 0, 0, 0], 2), 0)

    def test_zeros_mixed_in(self):
        self.assertEqual(solve([0, 5, 0, 5, 0], 2), 5)

    def test_uniform_weights(self):
        self.assertEqual(solve([3] * 9, 3), 9)

    def test_uniform_weights_uneven_split(self):
        self.assertEqual(solve([3] * 10, 3), 12)

    # --- crews larger than needed is impossible by the constraints, but
    # --- crews equal to the length is the boundary
    def test_crews_equal_to_length(self):
        self.assertEqual(solve([2, 9, 4], 3), 9)

    def test_two_parcels_two_crews(self):
        self.assertEqual(solve([1, 1000], 2), 1000)

    # --- cases where the greedy fill uses fewer crews than allowed ---

    def test_fewer_groups_than_allowed_is_still_valid(self):
        # A feasible limit that needs only 2 groups must not be rejected when 3
        # are permitted, since any group can be split further for free.
        self.assertEqual(solve([1, 1, 1, 1, 1, 1], 3), 2)

    def test_heavy_tail(self):
        self.assertEqual(solve([1, 1, 1, 1, 50], 2), 50)

    def test_heavy_head(self):
        self.assertEqual(solve([50, 1, 1, 1, 1], 2), 50)

    # --- shape ---

    def test_returns_an_int_not_a_bool(self):
        result = solve([1, 2], 2)
        self.assertIsInstance(result, int)
        self.assertNotIsInstance(result, bool)

    def test_input_is_not_mutated(self):
        weights = [7, 2, 5, 10, 8]
        original = list(weights)
        solve(weights, 2)
        self.assertEqual(weights, original)

    # --- scale ---

    def test_large_input_is_not_quadratic_or_exhaustive(self):
        """200k parcels. Only a search on the answer finishes this."""
        weights = [(index % 97) + 1 for index in range(200000)]
        result = solve(weights, 1000)
        self.assertGreaterEqual(result, max(weights))
        self.assertLessEqual(result, sum(weights))

    def test_large_uniform_split_is_exact(self):
        self.assertEqual(solve([1] * 100000, 1000), 100)

    def test_large_single_crew(self):
        weights = [2] * 150000
        self.assertEqual(solve(weights, 1), 300000)

    def test_large_values(self):
        self.assertEqual(solve([1000000] * 10, 5), 2000000)


if __name__ == "__main__":
    unittest.main()
