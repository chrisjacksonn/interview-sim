"""Deliberately wrong: sorts the caller's list in place, which both destroys the
input and gathers every quiet minute into one run

Used by tools/qa.py to prove the hidden suite can tell this from correct.
"""


def solve(counts):
    counts.sort()
    best = 0
    run = 0
    for count in counts:
        if count == 0:
            run += 1
            if run > best:
                best = run
        else:
            run = 0
    return best
