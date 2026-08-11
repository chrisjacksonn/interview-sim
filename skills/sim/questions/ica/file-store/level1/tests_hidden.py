"""Level 1 hidden suite. Never copied into a session workspace."""

import unittest

from solution import FileStore


class TestLevel1(unittest.TestCase):
    def setUp(self):
        self.store = FileStore()

    def test_add_returns_true(self):
        self.assertIs(self.store.add("a", 10), True)

    def test_get_returns_the_size(self):
        self.store.add("a", 10)
        self.assertEqual(self.store.get("a"), 10)

    def test_get_missing_is_none(self):
        self.assertIsNone(self.store.get("ghost"))

    def test_duplicate_add_returns_false(self):
        self.store.add("a", 10)
        self.assertIs(self.store.add("a", 99), False)

    def test_duplicate_add_does_not_change_the_size(self):
        self.store.add("a", 10)
        self.store.add("a", 99)
        self.assertEqual(self.store.get("a"), 10)

    def test_zero_size_is_allowed(self):
        self.assertIs(self.store.add("empty", 0), True)
        self.assertEqual(self.store.get("empty"), 0)

    def test_zero_size_is_not_treated_as_missing(self):
        self.store.add("empty", 0)
        self.assertIsNotNone(self.store.get("empty"))

    def test_negative_size_is_refused(self):
        self.assertIs(self.store.add("bad", -1), False)
        self.assertIsNone(self.store.get("bad"))

    def test_empty_name_is_refused(self):
        self.assertIs(self.store.add("", 10), False)

    def test_delete_returns_the_size(self):
        self.store.add("a", 42)
        self.assertEqual(self.store.delete("a"), 42)

    def test_delete_removes_the_file(self):
        self.store.add("a", 42)
        self.store.delete("a")
        self.assertIsNone(self.store.get("a"))

    def test_delete_missing_is_none(self):
        self.assertIsNone(self.store.delete("ghost"))

    def test_delete_twice(self):
        self.store.add("a", 42)
        self.store.delete("a")
        self.assertIsNone(self.store.delete("a"))

    def test_delete_of_a_zero_size_file_returns_zero_not_none(self):
        self.store.add("empty", 0)
        self.assertEqual(self.store.delete("empty"), 0)

    def test_name_is_reusable_after_delete(self):
        self.store.add("a", 42)
        self.store.delete("a")
        self.assertIs(self.store.add("a", 7), True)
        self.assertEqual(self.store.get("a"), 7)

    def test_names_are_case_sensitive(self):
        self.store.add("a", 1)
        self.assertIs(self.store.add("A", 2), True)
        self.assertEqual(self.store.get("a"), 1)

    def test_files_are_independent(self):
        self.store.add("a", 1)
        self.store.add("b", 2)
        self.store.delete("a")
        self.assertEqual(self.store.get("b"), 2)

    def test_two_stores_are_independent(self):
        other = FileStore()
        self.store.add("a", 1)
        self.assertIsNone(other.get("a"))

    def test_many_files(self):
        for index in range(300):
            self.store.add("f%03d" % index, index)
        self.assertEqual(self.store.get("f150"), 150)
