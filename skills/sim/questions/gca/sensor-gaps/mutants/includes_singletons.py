def solve(readings):
    by = {}
    for s, t in readings:
        by.setdefault(s, []).append(t)
    out = {}
    for s, ts in by.items():
        ts.sort()
        w = 0
        for i in range(1, len(ts)):
            w = max(w, ts[i] - ts[i-1])
        out[s] = w
    return out
