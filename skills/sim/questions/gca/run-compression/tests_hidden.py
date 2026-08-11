"""Hidden suite for Run Compression.

Never copied into a session workspace.
"""

import unittest

from solution import solve


class TestRunCompression(unittest.TestCase):
    # --- the threshold, which is the whole question ---

    def test_run_of_one_is_untouched(self):
        self.assertEqual(solve("a"), "a")

    def test_run_of_two_is_untouched(self):
        # The common wrong answer is "a2", which is not shorter.
        self.assertEqual(solve("aa"), "aa")

    def test_run_of_three_compresses(self):
        self.assertEqual(solve("aaa"), "a3")

    def test_run_of_four_compresses(self):
        self.assertEqual(solve("aaaa"), "a4")

    def test_mixed_thresholds(self):
        self.assertEqual(solve("abbcccdddd"), "abbc3d4")

    # --- run boundaries ---

    def test_runs_are_counted_separately_when_a_char_returns(self):
        self.assertEqual(solve("aaabaaa"), "a3ba3")

    def test_adjacent_long_runs(self):
        self.assertEqual(solve("aaabbb"), "a3b3")

    def test_run_at_the_very_end_is_flushed(self):
        # Catches solutions that only emit a run when a different char arrives.
        self.assertEqual(solve("abccc"), "abc3")

    def test_run_at_the_very_start(self):
        self.assertEqual(solve("cccab"), "c3ab")

    def test_single_run_is_the_whole_string(self):
        self.assertEqual(solve("zzzzz"), "z5")

    # --- lengths of two digits and more ---

    def test_ten_is_written_as_ten(self):
        self.assertEqual(solve("a" * 10), "a10")

    def test_long_count(self):
        self.assertEqual(solve("q" * 1234), "q1234")

    # --- characters that are not letters ---

    def test_digits_in_the_input(self):
        # "111" compresses to "13", which is ambiguous to read and still correct.
        self.assertEqual(solve("111"), "13")

    def test_digit_runs_below_the_threshold(self):
        self.assertEqual(solve("11"), "11")

    def test_spaces_compress(self):
        self.assertEqual(solve("a   b"), "a 3b")

    def test_punctuation(self):
        self.assertEqual(solve("!!!?"), "!3?")

    def test_case_is_significant(self):
        # "aaA" is a run of two then a run of one, so nothing compresses.
        self.assertEqual(solve("aaA"), "aaA")

    def test_uppercase_run_compresses(self):
        self.assertEqual(solve("AAAa"), "A3a")

    # --- shape ---

    def test_empty_string(self):
        result = solve("")
        self.assertEqual(result, "")
        self.assertIsInstance(result, str)

    def test_returns_a_string(self):
        self.assertIsInstance(solve("aaa"), str)

    def test_no_compression_returns_the_same_text(self):
        text = "abcdefghij"
        self.assertEqual(solve(text), text)

    # --- scale ---

    def test_large_alternating_input(self):
        text = "ab" * 40000
        self.assertEqual(solve(text), text)

    def test_large_single_run(self):
        self.assertEqual(solve("x" * 100000), "x100000")

    def test_large_mixed(self):
        text = ("a" * 5 + "bb") * 10000
        self.assertEqual(solve(text), "a5bb" * 10000)


if __name__ == "__main__":
    unittest.main()
