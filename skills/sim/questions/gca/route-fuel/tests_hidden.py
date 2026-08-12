"""Hidden suite for Route Fuel. Never copied into a session workspace."""

import unittest

from solution import solve


class TestRouteFuel(unittest.TestCase):
    def test_worked_example(self):
        self.assertEqual(solve(100, 10, [(10, 60), (20, 30), (30, 30), (60, 40)]), 2)

    def test_no_stops_needed(self):
        self.assertEqual(solve(100, 100, []), 0)

    def test_more_fuel_than_needed(self):
        self.assertEqual(solve(50, 1000, [(10, 10)]), 0)

    def test_exactly_enough_fuel(self):
        self.assertEqual(solve(100, 100, [(10, 50)]), 0)

    def test_one_short(self):
        self.assertEqual(solve(100, 99, []), -1)

    def test_no_depots_and_not_enough(self):
        self.assertEqual(solve(100, 10, []), -1)

    def test_cannot_reach_the_first_depot(self):
        self.assertEqual(solve(100, 1, [(10, 100)]), -1)

    def test_reaches_the_depot_exactly(self):
        self.assertEqual(solve(100, 10, [(10, 100)]), 1)

    def test_takes_the_largest_not_the_first(self):
        # Both are reachable; the greedy choice is the 90, not the 10.
        self.assertEqual(solve(100, 20, [(5, 10), (10, 90)]), 1)

    def test_takes_two_when_one_is_not_enough(self):
        # 20 + 50 is the best single stop and still short; both together reach.
        self.assertEqual(solve(100, 20, [(5, 40), (10, 50)]), 2)

    def test_two_stops_still_not_enough(self):
        self.assertEqual(solve(100, 20, [(5, 30), (10, 30)]), -1)

    def test_every_depot_needed(self):
        self.assertEqual(solve(100, 50, [(25, 25), (50, 25)]), 2)

    def test_unsorted_depots(self):
        self.assertEqual(solve(100, 10, [(60, 40), (10, 60), (30, 30)]), 2)

    def test_depots_at_the_same_position(self):
        self.assertEqual(solve(100, 10, [(10, 40), (10, 50)]), 2)

    def test_depot_at_the_destination_is_useless(self):
        self.assertEqual(solve(100, 50, [(100, 1000)]), -1)

    def test_zero_litre_depot(self):
        self.assertEqual(solve(100, 50, [(20, 0), (30, 50)]), 1)

    def test_zero_start_fuel(self):
        self.assertEqual(solve(100, 0, [(0, 100)]), 1)

    def test_zero_start_fuel_with_no_depot_at_zero(self):
        self.assertEqual(solve(100, 0, [(1, 100)]), -1)

    def test_returns_an_int_not_a_bool(self):
        result = solve(10, 10, [])
        self.assertIsInstance(result, int)
        self.assertNotIsInstance(result, bool)

    def test_input_is_not_mutated(self):
        depots = [(10, 60), (20, 30)]
        original = list(depots)
        solve(100, 10, depots)
        self.assertEqual(depots, original)

    def test_large_input_is_not_exponential(self):
        depots = [(index, 2) for index in range(100000)]
        result = solve(100000, 1, depots)
        self.assertGreater(result, 0)

    def test_large_distance_few_depots(self):
        self.assertEqual(solve(1000000000, 1, [(1, 999999999)]), 1)

    def test_many_useless_depots_then_one_good(self):
        depots = [(index, 0) for index in range(1, 50000)]
        depots.append((10, 1000000))
        self.assertEqual(solve(500000, 50, depots), 1)
