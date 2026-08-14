"""Deliberately wrong: sorts the caller's list in place.

The answer comes out right, so the only thing that catches this is the
input-preservation test, and only if its fixture is in an order that
sorting would disturb.

Used by tools/qa.py to prove the hidden suite can tell this from correct.
"""

import heapq


def solve(feeds, limit):
    if limit <= 0:
        return []

    feeds.sort()
    heap = []
    for index, feed in enumerate(feeds):
        if feed:
            # The feed index breaks ties without ever comparing the feeds
            # themselves, which would fail on lists of equal first elements.
            heap.append((feed[0], index, 0))
    heapq.heapify(heap)

    out = []
    while heap and len(out) < limit:
        value, feed_index, position = heapq.heappop(heap)
        out.append(value)
        feed = feeds[feed_index]
        if position + 1 < len(feed):
            heapq.heappush(heap, (feed[position + 1], feed_index, position + 1))
    return out
