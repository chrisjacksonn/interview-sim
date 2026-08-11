def solve(shifts, horizon):
    if horizon <= 0:
        return 0
    o = sorted(shifts)
    n, cov, i, cnt = len(o), 0, 0, 0
    while cov < horizon:
        best = cov
        while i < n and o[i][0] < cov:
            if o[i][1] > best:
                best = o[i][1]
            i += 1
        if best == cov:
            return -1
        cov = best
        cnt += 1
    return cnt
