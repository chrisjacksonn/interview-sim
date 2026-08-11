DIGITS = frozenset("0123456789")
def _n(t): return bool(t) and all(c in DIGITS for c in t)
def solve(entries):
    totals, seen = {}, {}
    for raw in entries:
        entry = raw.strip()
        if entry.count("-") != 1 or entry.count(":") != 1: continue
        d, c = entry.index("-"), entry.index(":")
        if d > c: continue
        a, s, n = entry[:d], entry[d+1:c], entry[c+1:]
        if not a or not _n(s) or not _n(n): continue
        seen[(a, s)] = int(n)
    for (a, _s), v in seen.items():
        totals[a] = totals.get(a, 0) + v
    return totals
