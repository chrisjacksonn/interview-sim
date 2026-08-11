import heapq
def solve(feeds, limit):
    h = [(f[0], i, 0) for i, f in enumerate(feeds) if f]
    heapq.heapify(h)
    out = []
    while h and len(out) < max(limit, 0) if limit > 0 else h:
        v, i, p = heapq.heappop(h)
        out.append(v)
        if p + 1 < len(feeds[i]): heapq.heappush(h, (feeds[i][p+1], i, p+1))
        if limit > 0 and len(out) >= limit: break
    return out[:limit]
