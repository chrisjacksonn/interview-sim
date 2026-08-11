def solve(shifts, horizon):
    if horizon <= 0:
        return 0
    cov, cnt = 0, 0
    while cov < horizon:
        best = cov
        for s, e in shifts:
            if s <= cov and e > best:
                best = e
        if best == cov:
            return -1
        cov = best
        cnt += 1
    return cnt
