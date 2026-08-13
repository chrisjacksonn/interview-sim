"""Deliberately wrong: only records a run when it ends, so a streak running to the
last minute is never counted

Used by tools/qa.py to prove the hidden suite can tell this from correct.
"""


def solve(counts):
    best = 0
    run = 0
    for count in counts:
        if count == 0:
            run += 1
        else:
            if run > best:
                best = run
            run = 0
    return best
