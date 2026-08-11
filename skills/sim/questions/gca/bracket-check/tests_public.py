"""Sample tests for Bracket Check. A sanity check, not the grade."""

import unittest

from solution import solve


class TestBracketCheck(unittest.TestCase):
    def test_balanced_with_other_characters(self):
        self.assertIs(solve("a(b[c]d)e"), True)

    def test_crossed_brackets(self):
        self.assertIs(solve("([)]"), False)

    def test_never_closed(self):
        self.assertIs(solve("((("), False)

    def test_no_brackets(self):
        self.assertIs(solve("no brackets here"), True)

    def test_empty(self):
        self.assertIs(solve(""), True)


if __name__ == "__main__":
    unittest.main()
