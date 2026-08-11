def solve(codes):
    last, best, left = {}, 0, 0
    for right, c in enumerate(codes):
        p = last.get(c)
        if p is not None and p >= left:
            left = p + 1
        last[c] = right
        best = max(best, right - left)
    return best
