"""Hidden suite for Bracket Check.

Never copied into a session workspace.
"""

import unittest

from solution import solve


class TestBracketCheck(unittest.TestCase):
    # --- balanced ---

    def test_simple_pair(self):
        self.assertIs(solve("()"), True)

    def test_all_three_kinds(self):
        self.assertIs(solve("()[]{}"), True)

    def test_nested(self):
        self.assertIs(solve("([{}])"), True)

    def test_deeply_nested(self):
        self.assertIs(solve("(((((())))))"), True)

    def test_balanced_with_text_between(self):
        self.assertIs(solve("a(b[c]d)e"), True)

    def test_sequential_groups(self):
        self.assertIs(solve("(a)(b)(c)"), True)

    # --- unbalanced ---

    def test_crossed(self):
        self.assertIs(solve("([)]"), False)

    def test_crossed_the_other_way(self):
        self.assertIs(solve("[(])"), False)

    def test_opener_never_closed(self):
        self.assertIs(solve("((("), False)

    def test_one_unclosed_at_the_end(self):
        # Catches solutions that forget to check the stack is empty at the end.
        self.assertIs(solve("()("), False)

    def test_closer_with_nothing_open(self):
        self.assertIs(solve(")"), False)

    def test_closer_first(self):
        self.assertIs(solve(")("), False)

    def test_wrong_kind_of_closer(self):
        self.assertIs(solve("(]"), False)

    def test_extra_closer_after_a_balanced_pair(self):
        self.assertIs(solve("())"), False)

    def test_mismatch_deep_inside(self):
        self.assertIs(solve("(((()}))"), False)

    # --- counting is not enough ---

    def test_equal_counts_but_wrong_order(self):
        # Catches solutions that only count openers against closers.
        self.assertIs(solve(")("), False)

    def test_equal_counts_of_each_kind_but_crossed(self):
        self.assertIs(solve("([)]"), False)

    # --- non-bracket characters ---

    def test_no_brackets_at_all(self):
        self.assertIs(solve("hello world"), True)

    def test_angle_brackets_are_not_brackets(self):
        # Only three kinds count, so these are ordinary characters.
        self.assertIs(solve("<>"), True)

    def test_unmatched_angle_bracket_is_still_balanced(self):
        self.assertIs(solve("a<b"), True)

    def test_brackets_inside_words(self):
        self.assertIs(solve("key[0]=value{1}"), True)

    def test_empty_string(self):
        self.assertIs(solve(""), True)

    # --- shape ---

    def test_returns_a_bool(self):
        self.assertIsInstance(solve("()"), bool)

    def test_returns_a_bool_when_false(self):
        self.assertIsInstance(solve("("), bool)

    # --- scale ---

    def test_deep_nesting_does_not_recurse_to_death(self):
        self.assertIs(solve("(" * 50000 + ")" * 50000), True)

    def test_long_unbalanced(self):
        self.assertIs(solve("(" * 50000 + ")" * 49999), False)

    def test_long_flat_sequence(self):
        self.assertIs(solve("()" * 50000), True)

    def test_long_text_without_brackets(self):
        self.assertIs(solve("x" * 200000), True)


if __name__ == "__main__":
    unittest.main()
