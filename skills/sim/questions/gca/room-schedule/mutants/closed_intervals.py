def solve(meetings):
    ev = []
    for s, e in meetings:
        if s >= e: continue
        ev.append((s, 1)); ev.append((e, -1))
    ev.sort(key=lambda p: (p[0], -p[1]))
    r = m = 0
    for _, d in ev:
        r += d; m = max(m, r)
    return m
