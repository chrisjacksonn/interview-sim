"""Level 3 hidden suite. Never copied into a session workspace."""

import unittest

from solution import FileStore


class TestLevel3(unittest.TestCase):
    def setUp(self):
        self.store = FileStore()
        self.store.add("docs/a.txt", 100)
        self.store.add("docs/b.txt", 200)
        self.store.add("images/c.png", 50)

    def test_find_by_prefix(self):
        self.assertEqual(self.store.find("docs/"), ["docs/a.txt", "docs/b.txt"])

    def test_find_is_sorted(self):
        self.store.add("docs/A.txt", 1)
        self.assertEqual(self.store.find("docs/"), sorted(self.store.find("docs/")))

    def test_empty_prefix_matches_everything(self):
        expected = ["docs/a.txt", "docs/b.txt", "images/c.png"]
        self.assertEqual(self.store.find(""), expected)

    def test_no_match_returns_empty(self):
        self.assertEqual(self.store.find("nothing"), [])

    def test_prefix_is_a_string_prefix_not_a_path_component(self):
        # "doc" must match "docs/..." even though it is not a whole segment.
        self.assertEqual(len(self.store.find("doc")), 2)

    def test_full_name_as_prefix(self):
        self.assertEqual(self.store.find("docs/a.txt"), ["docs/a.txt"])

    def test_prefix_longer_than_any_name(self):
        self.assertEqual(self.store.find("docs/a.txt.backup"), [])

    def test_prefix_is_case_sensitive(self):
        self.assertEqual(self.store.find("DOCS/"), [])

    def test_find_excludes_deleted_files(self):
        self.store.delete("docs/a.txt")
        self.assertEqual(self.store.find("docs/"), ["docs/b.txt"])

    def test_find_returns_a_list(self):
        self.assertIsInstance(self.store.find(""), list)

    def test_find_on_an_empty_store(self):
        self.assertEqual(FileStore().find(""), [])

    def test_total_with_prefix(self):
        self.assertEqual(self.store.total_size_with_prefix("docs/"), 300)

    def test_total_with_empty_prefix_is_the_whole_store(self):
        self.assertEqual(self.store.total_size_with_prefix(""), 350)
        self.assertEqual(self.store.total_size_with_prefix(""), self.store.total_size())

    def test_total_with_prefix_no_match(self):
        self.assertEqual(self.store.total_size_with_prefix("nothing"), 0)

    def test_total_with_prefix_after_delete(self):
        self.store.delete("docs/a.txt")
        self.assertEqual(self.store.total_size_with_prefix("docs/"), 200)

    def test_total_with_prefix_counts_zero_size_files(self):
        self.store.add("docs/empty", 0)
        self.assertEqual(self.store.total_size_with_prefix("docs/"), 300)

    def test_earlier_levels_still_work(self):
        self.assertEqual(self.store.total_size(), 350)
        self.assertEqual(self.store.largest(1), ["docs/b.txt"])
        self.assertEqual(self.store.get("docs/a.txt"), 100)
        self.assertIs(self.store.add("docs/a.txt", 1), False)

    def test_scale(self):
        store = FileStore()
        for index in range(500):
            store.add("a/%03d" % index, 1)
            store.add("b/%03d" % index, 2)
        self.assertEqual(len(store.find("a/")), 500)
        self.assertEqual(store.total_size_with_prefix("b/"), 1000)
