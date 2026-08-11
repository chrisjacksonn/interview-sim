def solve(tasks, budget):
    if budget < 0: return 0
    best = [0] * (budget + 1)
    for cost, value in tasks:
        if cost > budget: continue
        if cost == 0:
            for s in range(budget + 1): best[s] += value
            continue
        for s in range(cost, budget + 1):
            best[s] = max(best[s], best[s - cost] + value)
    return best[budget]
