def solve(readings):
    by = {}
    for s, t in readings:
        by.setdefault(s, []).append(t)
    out = {}
    for s, ts in by.items():
        if len(ts) < 2:
            continue
        out[s] = max(ts) - min(ts)
    return out
