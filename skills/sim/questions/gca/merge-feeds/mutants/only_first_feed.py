def solve(feeds, limit):
    if limit <= 0: return []
    return (feeds[0][:limit] if feeds else [])
