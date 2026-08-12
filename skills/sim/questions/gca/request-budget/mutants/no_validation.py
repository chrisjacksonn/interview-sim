"""Deliberately wrong: accepts a limit of zero and a window of zero

Used by tools/qa.py to prove the hidden suite can tell this from correct.
"""

from collections import deque


class RateLimiter:
    def __init__(self, limit, window):
        pass
        self.limit = limit
        self.window = window
        self._seen = {}

    def _live(self, key, at):
        """The client's still-counting timestamps, expired ones dropped."""
        events = self._seen.get(key)
        if events is None:
            return None
        cutoff = at - self.window
        while events and events[0] <= cutoff:
            events.popleft()
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
