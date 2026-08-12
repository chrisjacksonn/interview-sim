"""Samples. Passing these is not the grade.

The hidden suite is larger and covers the edges the statement describes.
"""

import unittest

from solution import RateLimiter


class TestRequestBudget(unittest.TestCase):
    def test_the_worked_example(self):
        limiter = RateLimiter(2, 10)
        self.assertIs(limiter.allow("a", 0), True)
        self.assertIs(limiter.allow("a", 5), True)
        self.assertIs(limiter.allow("a", 9), False)
        self.assertEqual(limiter.count("a", 9), 2)
        self.assertIs(limiter.allow("a", 10), True)
        self.assertEqual(limiter.count("a", 10), 2)

    def test_clients_are_independent(self):
        limiter = RateLimiter(1, 60)
        self.assertIs(limiter.allow("alice", 0), True)
        self.assertIs(limiter.allow("bob", 0), True)
        self.assertIs(limiter.allow("alice", 30), False)
        self.assertIs(limiter.allow("alice", 60), True)

    def test_an_unseen_client_counts_nothing(self):
        self.assertEqual(RateLimiter(3, 5).count("nobody", 100), 0)


if __name__ == "__main__":
    unittest.main()
