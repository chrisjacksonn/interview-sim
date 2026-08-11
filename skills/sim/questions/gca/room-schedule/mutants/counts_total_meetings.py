def solve(meetings):
    return len([1 for s, e in meetings if s < e])
