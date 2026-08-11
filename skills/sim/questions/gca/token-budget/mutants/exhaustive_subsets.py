def solve(tasks, budget):
    if budget < 0: return 0
    best = 0
    n = len(tasks)
    for mask in range(1 << n):
        c = v = 0
        for i in range(n):
            if mask >> i & 1:
                c += tasks[i][0]; v += tasks[i][1]
        if c <= budget and v > best: best = v
    return best
