DIGITS = frozenset("0123456789")
def _n(t): return bool(t) and all(c in DIGITS for c in t)
def solve(entries):
    totals = {}
    for raw in entries:
        entry = raw.strip()
        if "-" not in entry or ":" not in entry: continue
        a, rest = entry.split("-", 1)
        s, n = rest.split(":", 1)
        if not a or not _n(s) or not _n(n): continue
        totals[a] = totals.get(a, 0) + int(n)
    return totals
