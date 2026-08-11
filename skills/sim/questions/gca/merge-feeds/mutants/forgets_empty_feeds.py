import heapq
def solve(feeds, limit):
    if limit <= 0: return []
    h = [(f[0], i, 0) for i, f in enumerate(feeds)]
    heapq.heapify(h)
    out = []
    while h and len(out) < limit:
        v, i, p = heapq.heappop(h)
        out.append(v)
        if p + 1 < len(feeds[i]): heapq.heappush(h, (feeds[i][p+1], i, p+1))
    return out
