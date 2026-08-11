def solve(codes):
    best = run = 0
    seen = set()
    for c in codes:
        if c in seen:
            seen = set()
            run = 0
        seen.add(c)
        run += 1
        best = max(best, run)
    return best
