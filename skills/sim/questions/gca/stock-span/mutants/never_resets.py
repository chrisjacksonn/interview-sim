"""Deliberately wrong: never resets on a loud minute, so it totals every quiet
minute instead of measuring the longest consecutive run

Used by tools/qa.py to prove the hidden suite can tell this from correct.
"""


def solve(counts):
    best = 0
    run = 0
    for count in counts:
        if count == 0:
            run += 1
            if run > best:
                best = run
    return best
