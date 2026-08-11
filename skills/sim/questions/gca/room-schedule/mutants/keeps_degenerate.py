def solve(meetings):
    ev = []
    for s, e in meetings:
        ev.append((s, 1)); ev.append((e, -1))
    ev.sort()
    r = m = 0
    for _, d in ev:
        r += d; m = max(m, r)
    return m
