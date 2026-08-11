def solve(tasks, budget):
    if budget < 0: return 0
    order = sorted(tasks, key=lambda t: (-(t[1] / t[0]) if t[0] else -10**9))
    total = 0; left = budget
    for c, v in order:
        if c <= left:
            left -= c; total += v
    return total
