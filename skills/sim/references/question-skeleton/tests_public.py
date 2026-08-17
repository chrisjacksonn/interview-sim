import unittest

from solution import solve


class TestPublic(unittest.TestCase):
    def test_the_worked_example(self):
        self.assertEqual(solve(None), None)
