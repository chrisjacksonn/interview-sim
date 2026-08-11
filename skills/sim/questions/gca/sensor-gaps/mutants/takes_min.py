def solve(readings):
    by = {}
    for s, t in readings:
        by.setdefault(s, []).append(t)
    out = {}
    for s, ts in by.items():
        if len(ts) < 2:
            continue
        ts.sort()
        out[s] = min(ts[i] - ts[i-1] for i in range(1, len(ts)))
    return out
