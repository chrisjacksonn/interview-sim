"""Level 4 samples. A sanity check, not the grade."""

import unittest

from solution import FileStore


class TestLevel4(unittest.TestCase):
    def test_update_changes_the_live_size(self):
        store = FileStore()
        store.add("a.txt", 100)
        self.assertTrue(store.update("a.txt", 250))
        self.assertEqual(store.get("a.txt"), 250)
        self.assertEqual(store.version_count("a.txt"), 2)

    def test_history_is_not_added_to_the_total(self):
        store = FileStore()
        store.add("a.txt", 100)
        store.update("a.txt", 250)
        self.assertEqual(store.total_size(), 250)

    def test_revert(self):
        store = FileStore()
        store.add("a.txt", 100)
        store.update("a.txt", 250)
        self.assertTrue(store.revert("a.txt"))
        self.assertEqual(store.get("a.txt"), 100)

    def test_cannot_revert_the_only_version(self):
        store = FileStore()
        store.add("a.txt", 100)
        self.assertFalse(store.revert("a.txt"))

    def test_update_unknown_file(self):
        self.assertFalse(FileStore().update("ghost", 5))


if __name__ == "__main__":
    unittest.main()
