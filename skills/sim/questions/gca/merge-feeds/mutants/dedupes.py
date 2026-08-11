import heapq
def solve(feeds, limit):
    if limit <= 0: return []
    return sorted(set(x for f in feeds for x in f))[:limit]
