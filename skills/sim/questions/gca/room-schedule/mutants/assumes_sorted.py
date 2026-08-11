def solve(meetings):
    live = []
    m = 0
    for s, e in meetings:
        if s >= e: continue
        live = [x for x in live if x > s]
        live.append(e)
        m = max(m, len(live))
    return m
