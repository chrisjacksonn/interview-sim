def solve(feeds, limit):
    if limit <= 0: return []
    out = []
    while len(out) < limit:
        best = None
        for f in feeds:
            if f and (best is None or f[0] < feeds[best][0]):
                best = feeds.index(f)
        if best is None: break
        out.append(feeds[best].pop(0))
    return out
