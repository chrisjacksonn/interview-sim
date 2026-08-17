import unittest

from solution import solve


class TestHidden(unittest.TestCase):
    # Descriptive names, no docstrings: the debrief reads the name back as
    # English, so the name is the documentation.
    def test_the_worked_example(self):
        self.assertEqual(solve(None), None)
