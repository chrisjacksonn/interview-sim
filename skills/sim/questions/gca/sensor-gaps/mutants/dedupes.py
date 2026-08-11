def solve(readings):
    by = {}
    for s, t in readings:
        by.setdefault(s, set()).add(t)
    out = {}
    for s, ts in by.items():
        if len(ts) < 2:
            continue
        ts = sorted(ts)
        out[s] = max(ts[i] - ts[i-1] for i in range(1, len(ts)))
    return out
