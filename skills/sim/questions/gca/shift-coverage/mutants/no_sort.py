def solve(shifts, horizon):
    if horizon <= 0:
        return 0
    cov, cnt = 0, 0
    i, n = 0, len(shifts)
    while cov < horizon:
        best = cov
        while i < n and shifts[i][0] <= cov:
            if shifts[i][1] > best:
                best = shifts[i][1]
            i += 1
        if best == cov:
            return -1
        cov = best
        cnt += 1
    return cnt
