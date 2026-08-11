"""Reference solution for Shelf Tally.

Never copied into a session workspace. CI runs this against tests_hidden.py to
confirm the hidden suite is satisfiable, and runs deliberately-broken variants
against it to confirm the suite actually discriminates.
"""

DIGITS = frozenset("0123456789")


def _nonneg_int(text):
    """True when text is a non-empty run of ASCII digits.

    Deliberately stricter than str.isdigit, which accepts superscripts and
    other Unicode digit forms that int() then refuses.
    """
    return bool(text) and all(char in DIGITS for char in text)


def solve(entries):
    totals = {}
    for raw in entries:
        entry = raw.strip()
        if entry.count("-") != 1 or entry.count(":") != 1:
            continue
        dash = entry.index("-")
        colon = entry.index(":")
        if dash > colon:
            continue
        aisle = entry[:dash]
        shelf = entry[dash + 1 : colon]
        count = entry[colon + 1 :]
        if not aisle or not _nonneg_int(shelf) or not _nonneg_int(count):
            continue
        totals[aisle] = totals.get(aisle, 0) + int(count)
    return totals
