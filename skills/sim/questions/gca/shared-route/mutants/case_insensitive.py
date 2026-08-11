def solve(first, second):
    if not first or not second: return 0
    first = [x.lower() for x in first]; second = [x.lower() for x in second]
    prev = [0] * (len(second) + 1)
    for a in first:
        cur = [0] * (len(second) + 1)
        for j, b in enumerate(second):
            cur[j+1] = prev[j] + 1 if a == b else max(prev[j+1], cur[j])
        prev = cur
    return prev[len(second)]
