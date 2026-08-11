"""Level 1 samples. A sanity check, not the grade."""

import unittest

from solution import FileStore


class TestLevel1(unittest.TestCase):
    def test_add_and_get(self):
        store = FileStore()
        self.assertTrue(store.add("notes.txt", 120))
        self.assertEqual(store.get("notes.txt"), 120)

    def test_duplicate_add_is_refused(self):
        store = FileStore()
        store.add("notes.txt", 120)
        self.assertFalse(store.add("notes.txt", 999))
        self.assertEqual(store.get("notes.txt"), 120)

    def test_delete_returns_the_size(self):
        store = FileStore()
        store.add("notes.txt", 120)
        self.assertEqual(store.delete("notes.txt"), 120)
        self.assertIsNone(store.get("notes.txt"))

    def test_delete_missing(self):
        self.assertIsNone(FileStore().delete("nope"))

    def test_zero_size_is_a_real_file(self):
        store = FileStore()
        self.assertTrue(store.add("empty", 0))
        self.assertEqual(store.get("empty"), 0)


if __name__ == "__main__":
    unittest.main()
