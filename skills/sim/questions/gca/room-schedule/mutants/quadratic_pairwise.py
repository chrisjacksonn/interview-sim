def solve(meetings):
    real = [(s, e) for s, e in meetings if s < e]
    best = 0
    for s, e in real:
        n = sum(1 for a, b in real if a < e and s < b)
        best = max(best, n)
    return best
