"""Reference solution for Token Budget.

Never copied into a session workspace.

Nought-one knapsack. The inner loop runs downward, which is what stops a task
being taken twice: by the time a cell is written, the cells it reads from still
describe the state before this task was considered. Running it upward turns the
question into the unbounded one and quietly allows repeats.
"""


def solve(tasks, budget):
    if budget < 0:
        return 0

    best = [0] * (budget + 1)
    for cost, value in tasks:
        if cost > budget:
            continue
        if cost == 0:
            # A free task is pure gain and never competes for budget.
            for spend in range(budget + 1):
                best[spend] += value
            continue
        for spend in range(budget, cost - 1, -1):
            candidate = best[spend - cost] + value
            if candidate > best[spend]:
                best[spend] = candidate
    return best[budget]
