def solve(codes):
    last, best, left = {}, 0, 0
    for right, raw in enumerate(codes):
        c = raw.lower()
        p = last.get(c)
        if p is not None and p >= left:
            left = p + 1
        last[c] = right
        best = max(best, right - left + 1)
    return best
