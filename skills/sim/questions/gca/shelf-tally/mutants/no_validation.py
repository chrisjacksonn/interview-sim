def solve(entries):
    totals = {}
    for e in entries:
        try:
            aisle, rest = e.split("-")
            shelf, count = rest.split(":")
            totals[aisle] = totals.get(aisle, 0) + int(count)
        except ValueError:
            continue
    return totals
