"""Hidden suite for Sensor Gaps.

Never copied into a session workspace. Each test targets a distinct way a
plausible solution goes wrong.
"""

import unittest

from solution import solve


class TestSensorGaps(unittest.TestCase):
    # --- the happy path ---

    def test_basic(self):
        readings = [("s1", 100), ("s2", 40), ("s1", 250), ("s1", 130)]
        self.assertEqual(solve(readings), {"s1": 120})

    def test_two_readings_only(self):
        self.assertEqual(solve([("a", 3), ("a", 11)]), {"a": 8})

    # --- ordering ---

    def test_input_is_not_sorted(self):
        # Catches anything that walks the list as given.
        self.assertEqual(solve([("a", 50), ("a", 0), ("a", 10)]), {"a": 40})

    def test_reverse_ordered_input(self):
        self.assertEqual(solve([("a", 30), ("a", 20), ("a", 0)]), {"a": 20})

    def test_sensors_are_interleaved(self):
        # Catches anything that diffs consecutive rows without grouping first.
        readings = [("a", 0), ("b", 1000), ("a", 5), ("b", 1001), ("a", 9)]
        self.assertEqual(solve(readings), {"a": 5, "b": 1})

    # --- which sensors appear at all ---

    def test_single_reading_sensor_is_absent(self):
        self.assertEqual(solve([("lonely", 7)]), {})

    def test_single_reading_sensor_absent_alongside_others(self):
        readings = [("a", 1), ("a", 4), ("solo", 99)]
        self.assertEqual(solve(readings), {"a": 3})

    def test_many_single_reading_sensors(self):
        readings = [("s%d" % i, i) for i in range(20)]
        self.assertEqual(solve(readings), {})

    # --- gap arithmetic ---

    def test_longest_not_first_and_not_last(self):
        # Catches solutions that keep the first or the last gap instead of max.
        self.assertEqual(solve([("a", 0), ("a", 2), ("a", 50), ("a", 51)]), {"a": 48})

    def test_longest_is_the_first_gap(self):
        self.assertEqual(solve([("a", 0), ("a", 40), ("a", 41)]), {"a": 40})

    def test_longest_is_the_last_gap(self):
        self.assertEqual(solve([("a", 0), ("a", 1), ("a", 41)]), {"a": 40})

    def test_duplicate_timestamps_do_not_shrink_the_answer(self):
        # Catches solutions that dedupe and lose a real gap, or that take min.
        self.assertEqual(solve([("a", 0), ("a", 0), ("a", 25)]), {"a": 25})

    def test_all_duplicates_is_zero_not_absent(self):
        self.assertEqual(solve([("a", 4), ("a", 4), ("a", 4)]), {"a": 0})

    def test_negative_timestamps(self):
        self.assertEqual(solve([("a", -100), ("a", -40)]), {"a": 60})

    def test_spanning_zero(self):
        self.assertEqual(solve([("a", -5), ("a", 5)]), {"a": 10})

    # --- keys ---

    def test_sensor_ids_are_case_sensitive(self):
        readings = [("A", 0), ("A", 3), ("a", 0), ("a", 100)]
        self.assertEqual(solve(readings), {"A": 3, "a": 100})

    # --- shape and scale ---

    def test_empty_input(self):
        result = solve([])
        self.assertEqual(result, {})
        self.assertIsInstance(result, dict)

    def test_values_are_integers(self):
        result = solve([("a", 0), ("a", 7)])
        self.assertIsInstance(result["a"], int)

    def test_large_input(self):
        readings = []
        for sensor in range(50):
            for step in range(200):
                readings.append(("s%d" % sensor, step * 3))
        readings.append(("s0", 100000))
        result = solve(readings)
        self.assertEqual(len(result), 50)
        self.assertEqual(result["s1"], 3)
        self.assertEqual(result["s0"], 100000 - 199 * 3)


if __name__ == "__main__":
    unittest.main()
