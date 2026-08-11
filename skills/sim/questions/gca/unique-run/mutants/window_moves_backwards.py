def solve(codes):
    last, best, left = {}, 0, 0
    for right, c in enumerate(codes):
        if c in last:
            left = last[c] + 1
        last[c] = right
        best = max(best, right - left + 1)
    return best
