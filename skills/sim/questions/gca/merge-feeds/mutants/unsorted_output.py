def solve(feeds, limit):
    if limit <= 0: return []
    out = []
    for f in feeds:
        out.extend(f)
        if len(out) >= limit: break
    return out[:limit]
