# Pops the smallest but never pushes that feed's next reading, so only the head
# of each feed is ever considered.
import heapq
def solve(feeds, limit):
    if limit <= 0: return []
    h = [(f[0], i, 0) for i, f in enumerate(feeds) if f]
    heapq.heapify(h)
    out = []
    while h and len(out) < limit:
        v, i, p = heapq.heappop(h)
        out.append(v)
    return out
