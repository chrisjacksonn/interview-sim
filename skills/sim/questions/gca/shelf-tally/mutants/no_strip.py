DIGITS = frozenset("0123456789")
def _n(t): return bool(t) and all(c in DIGITS for c in t)
def solve(entries):
    totals = {}
    for entry in entries:
        if entry.count("-") != 1 or entry.count(":") != 1: continue
        d, c = entry.index("-"), entry.index(":")
        if d > c: continue
        a, s, n = entry[:d], entry[d+1:c], entry[c+1:]
        if not a or not _n(s) or not _n(n): continue
        totals[a] = totals.get(a, 0) + int(n)
    return totals
