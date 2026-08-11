"""Reference solution for Merge Feeds.

Never copied into a session workspace.

A heap holding one candidate per feed. Each step takes the smallest and pushes
that feed's next reading, so the work is proportional to the number of readings
actually returned rather than to the size of the input.
"""

import heapq


def solve(feeds, limit):
    if limit <= 0:
        return []

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
