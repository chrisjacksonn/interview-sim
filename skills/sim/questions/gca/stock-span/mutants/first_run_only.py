"""Deliberately wrong: stops at the first quiet streak instead of looking for the
longest one

Used by tools/qa.py to prove the hidden suite can tell this from correct.
"""


def solve(counts):
    run = 0
    for count in counts:
        if count == 0:
            run += 1
        elif run:
            return run
    return run
