"""Level 2 hidden suite. Never copied into a session workspace."""

import unittest

from solution import FileStore


class TestLevel2(unittest.TestCase):
    def setUp(self):
        self.store = FileStore()

    def test_total_of_an_empty_store(self):
        self.assertEqual(self.store.total_size(), 0)

    def test_total_sums_every_file(self):
        self.store.add("a", 300)
        self.store.add("b", 100)
        self.assertEqual(self.store.total_size(), 400)

    def test_total_drops_after_delete(self):
        self.store.add("a", 300)
        self.store.add("b", 100)
        self.store.delete("a")
        self.assertEqual(self.store.total_size(), 100)

    def test_total_ignores_refused_adds(self):
        self.store.add("a", 300)
        self.store.add("a", 999)
        self.store.add("bad", -5)
        self.assertEqual(self.store.total_size(), 300)

    def test_total_counts_zero_size_files(self):
        self.store.add("a", 0)
        self.assertEqual(self.store.total_size(), 0)

    def test_largest_orders_by_size(self):
        self.store.add("small", 1)
        self.store.add("big", 900)
        self.store.add("mid", 50)
        self.assertEqual(self.store.largest(3), ["big", "mid", "small"])

    def test_largest_breaks_ties_by_name(self):
        self.store.add("zeta", 100)
        self.store.add("alpha", 100)
        self.assertEqual(self.store.largest(2), ["alpha", "zeta"])

    def test_tie_break_does_not_override_size(self):
        self.store.add("alpha", 1)
        self.store.add("zeta", 999)
        self.assertEqual(self.store.largest(2), ["zeta", "alpha"])

    def test_largest_with_a_small_count(self):
        self.store.add("a", 3)
        self.store.add("b", 2)
        self.store.add("c", 1)
        self.assertEqual(self.store.largest(1), ["a"])

    def test_largest_beyond_the_end(self):
        self.store.add("a", 3)
        self.assertEqual(self.store.largest(50), ["a"])

    def test_largest_of_zero(self):
        self.store.add("a", 3)
        self.assertEqual(self.store.largest(0), [])

    def test_largest_of_a_negative(self):
        self.store.add("a", 3)
        self.store.add("b", 2)
        self.assertEqual(self.store.largest(-1), [])

    def test_largest_of_an_empty_store(self):
        self.assertEqual(self.store.largest(5), [])

    def test_largest_returns_names_not_sizes(self):
        self.store.add("a", 3)
        self.assertEqual(self.store.largest(1), ["a"])

    def test_largest_returns_a_list(self):
        self.store.add("a", 3)
        self.assertIsInstance(self.store.largest(1), list)

    def test_largest_excludes_deleted_files(self):
        self.store.add("gone", 999)
        self.store.add("here", 1)
        self.store.delete("gone")
        self.assertEqual(self.store.largest(5), ["here"])

    def test_zero_size_files_still_appear(self):
        self.store.add("a", 0)
        self.store.add("b", 5)
        self.assertEqual(self.store.largest(2), ["b", "a"])

    def test_level_one_still_works(self):
        self.assertIs(self.store.add("a", 1), True)
        self.assertIs(self.store.add("a", 2), False)
        self.assertEqual(self.store.delete("a"), 1)
        self.assertIsNone(self.store.get("a"))

    def test_scale(self):
        for index in range(400):
            self.store.add("f%03d" % index, index)
        self.assertEqual(self.store.largest(2), ["f399", "f398"])
        self.assertEqual(self.store.total_size(), sum(range(400)))
