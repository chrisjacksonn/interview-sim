def solve(tasks, budget):
    if budget < 0: return 0
    best = [0] * (budget + 1)
    for cost, value in tasks:
        if cost > budget or cost == 0: continue
        for s in range(budget, cost - 1, -1):
            best[s] = max(best[s], best[s - cost] + value)
    return best[budget]
