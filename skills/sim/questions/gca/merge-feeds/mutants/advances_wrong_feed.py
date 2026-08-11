# Advances position within the popped feed but reads it from the first feed.
import heapq
def solve(feeds, limit):
    if limit <= 0: return []
    h = [(f[0], i, 0) for i, f in enumerate(feeds) if f]
    heapq.heapify(h)
    out = []
    while h and len(out) < limit:
        v, i, p = heapq.heappop(h)
        out.append(v)
        first = feeds[0]
        if p + 1 < len(first): heapq.heappush(h, (first[p+1], 0, p+1))
    return out
