"""Deliberately wrong: never expires anything, so a client is limited forever after one burst

Used by tools/qa.py to prove the hidden suite can tell this from correct.
"""

from collections import deque


class RateLimiter:
    def __init__(self, limit, window):
        if not isinstance(limit, int) or isinstance(limit, bool) or limit < 1:
            raise ValueError("limit must be an integer of at least 1")
        if window <= 0:
            raise ValueError("window must be positive")
        self.limit = limit
        self.window = window
        self._seen = {}

    def _live(self, key, at):
        """The client's still-counting timestamps, expired ones dropped."""
        events = self._seen.get(key)
        if events is None:
            return None
        return events

    def allow(self, key, at):
        if not isinstance(key, str) or not key:
            return False
        events = self._live(key, at)
        if events is None:
            events = deque()
            self._seen[key] = events
        if len(events) >= self.limit:
            return False
        events.append(at)
        return True

    def count(self, key, at):
        if not isinstance(key, str) or not key:
            return 0
        events = self._live(key, at)
        return len(events) if events else 0
