"""Deliberately wrong: sorts the caller's list in place.

The answer comes out right, so the only thing that catches this is the
input-preservation test, and only if its fixture is in an order that
sorting would disturb.

Used by tools/qa.py to prove the hidden suite can tell this from correct.
"""

def solve(tasks, budget):
    if budget < 0:
        return 0

    tasks.sort()
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
