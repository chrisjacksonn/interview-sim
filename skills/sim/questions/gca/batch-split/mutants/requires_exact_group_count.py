def solve(weights, crews):
    lo, hi = max(weights) if weights else 0, sum(weights)
    def need(limit):
        used, load = 1, 0
        for x in weights:
            if load + x > limit: used += 1; load = x
            else: load += x
        return used
    while lo < hi:
        mid = (lo + hi) // 2
        if need(mid) == crews: hi = mid
        else: lo = mid + 1
    return lo
