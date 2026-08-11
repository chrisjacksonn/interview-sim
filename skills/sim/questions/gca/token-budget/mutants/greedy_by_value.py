def solve(tasks, budget):
    if budget < 0: return 0
    total = 0; left = budget
    for c, v in sorted(tasks, key=lambda t: -t[1]):
        if c <= left:
            left -= c; total += v
    return total
