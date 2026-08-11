"""Sample tests for Shelf Tally.

These are a sanity check, not the grade. Passing all of them does not mean the
question is done.
"""

import unittest

from solution import solve


class TestShelfTally(unittest.TestCase):
    def test_sums_shelves_within_an_aisle(self):
        self.assertEqual(solve(["A12-3:40", "A12-1:5", "B7-2:12"]), {"A12": 45, "B7": 12})

    def test_zero_count_is_valid(self):
        self.assertEqual(solve(["A1-0:0", "A1-1:7"]), {"A1": 7})

    def test_skips_malformed_entries(self):
        entries = ["Q9-2:15", "broken", "Q9-x:4", "Q9-2:-3", "", "Q9-1:5"]
        self.assertEqual(solve(entries), {"Q9": 20})

    def test_empty_input(self):
        self.assertEqual(solve([]), {})


if __name__ == "__main__":
    unittest.main()
