def solve(tasks, budget):
    if budget < 0: return 0
    NEG = -10**9
    best = [NEG] * (budget + 1)
    best[0] = 0
    for cost, value in tasks:
        if cost > budget: continue
        for s in range(budget, cost - 1, -1):
            if best[s - cost] > NEG:
                best[s] = max(best[s], best[s - cost] + value)
    return max(best[budget], 0)
