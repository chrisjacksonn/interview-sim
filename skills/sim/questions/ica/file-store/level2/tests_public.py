"""Level 2 samples. A sanity check, not the grade."""

import unittest

from solution import FileStore


class TestLevel2(unittest.TestCase):
    def build(self):
        store = FileStore()
        store.add("a.txt", 300)
        store.add("b.txt", 100)
        store.add("c.txt", 300)
        return store

    def test_total_size(self):
        self.assertEqual(self.build().total_size(), 700)

    def test_largest_breaks_ties_by_name(self):
        self.assertEqual(self.build().largest(2), ["a.txt", "c.txt"])

    def test_largest_beyond_the_end(self):
        self.assertEqual(self.build().largest(10), ["a.txt", "c.txt", "b.txt"])

    def test_largest_of_zero(self):
        self.assertEqual(self.build().largest(0), [])

    def test_total_after_delete(self):
        store = self.build()
        store.delete("a.txt")
        self.assertEqual(store.total_size(), 400)


if __name__ == "__main__":
    unittest.main()
