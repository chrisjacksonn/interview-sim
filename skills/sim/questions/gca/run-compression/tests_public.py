"""Sample tests for Run Compression. A sanity check, not the grade."""

import unittest

from solution import solve


class TestRunCompression(unittest.TestCase):
    def test_only_long_runs_compress(self):
        self.assertEqual(solve("aaabbc"), "a3bbc")

    def test_long_run(self):
        self.assertEqual(solve("aaaaaaaaaaaa"), "a12")

    def test_nothing_to_compress(self):
        self.assertEqual(solve("abc"), "abc")

    def test_runs_are_counted_separately(self):
        self.assertEqual(solve("aabbbaa"), "aab3aa")

    def test_empty(self):
        self.assertEqual(solve(""), "")


if __name__ == "__main__":
    unittest.main()
