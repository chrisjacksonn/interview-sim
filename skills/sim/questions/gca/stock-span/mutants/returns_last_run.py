"""Deliberately wrong: returns the run in progress at the end, not the longest one

Used by tools/qa.py to prove the hidden suite can tell this from correct.
"""


def solve(counts):
    run = 0
    for count in counts:
        if count == 0:
            run += 1
        else:
            run = 0
    return run
