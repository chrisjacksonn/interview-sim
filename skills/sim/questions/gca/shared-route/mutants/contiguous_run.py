def solve(first, second):
    if not first or not second: return 0
    best = 0
    prev = [0] * (len(second) + 1)
    for a in first:
        cur = [0] * (len(second) + 1)
        for j, b in enumerate(second):
            if a == b:
                cur[j+1] = prev[j] + 1
                best = max(best, cur[j+1])
        prev = cur
    return best
