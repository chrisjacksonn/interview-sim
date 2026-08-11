def solve(meetings):
    ev = []
    for s, e in meetings:
        if s >= e: continue
        ev.append((s, 1)); ev.append((e, -1))
    ev.sort()
    r = 0
    for _, d in ev:
        r += d
    return max(r, 1) if ev else 0
