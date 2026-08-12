"""Request Budget.

Read problem.md for the full statement.
"""


class RateLimiter:
    """At most `limit` allowed requests per client in any `window` seconds."""

    def __init__(self, limit, window):
        raise NotImplementedError

    def allow(self, key, at):
        """Record a request from `key` at time `at`. True if inside the budget.

        A refused request must not count against the budget.
        """
        raise NotImplementedError

    def count(self, key, at):
        """How many allowed requests for `key` are still inside the budget."""
        raise NotImplementedError
