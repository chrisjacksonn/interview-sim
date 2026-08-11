def solve(weights, crews):
    n = len(weights)
    from functools import lru_cache
    import sys
    sys.setrecursionlimit(100000)
    @lru_cache(maxsize=None)
    def go(i, k):
        if k == 1:
            return sum(weights[i:])
        best = None
        total = 0
        for j in range(i, n - k + 1):
            total += weights[j]
            rest = go(j + 1, k - 1)
            cand = total if total > rest else rest
            if best is None or cand < best:
                best = cand
        return best
    return go(0, crews)
