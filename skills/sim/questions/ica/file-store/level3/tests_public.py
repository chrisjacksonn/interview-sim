"""Level 3 samples. A sanity check, not the grade."""

import unittest

from solution import FileStore


class TestLevel3(unittest.TestCase):
    def build(self):
        store = FileStore()
        store.add("docs/a.txt", 100)
        store.add("docs/b.txt", 200)
        store.add("images/c.png", 50)
        return store

    def test_find_by_prefix(self):
        self.assertEqual(self.build().find("docs/"), ["docs/a.txt", "docs/b.txt"])

    def test_empty_prefix_matches_everything(self):
        expected = ["docs/a.txt", "docs/b.txt", "images/c.png"]
        self.assertEqual(self.build().find(""), expected)

    def test_no_match(self):
        self.assertEqual(self.build().find("nothing"), [])

    def test_total_with_prefix(self):
        self.assertEqual(self.build().total_size_with_prefix("docs/"), 300)

    def test_total_with_empty_prefix(self):
        self.assertEqual(self.build().total_size_with_prefix(""), 350)


if __name__ == "__main__":
    unittest.main()
