import unittest

from solution import solve

# Defined once, here, and only here. values.py imports these and prints the
# expected value for every case; run it, paste the answers into the tests.
DATA = []
CASES = [
    # ("test_name", CASE_ARGS),
]


class TestHidden(unittest.TestCase):
    # Descriptive names, no docstrings: the debrief reads the name back as
    # English, so the name is the documentation.
    def test_the_worked_example(self):
        self.assertEqual(solve(DATA), None)
