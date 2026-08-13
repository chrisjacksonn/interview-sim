"""Deliberately wrong: drops the smallest value in the sorted window instead of
the reading that actually slid out

Used by tools/qa.py to prove the hidden suite can tell this from correct.
"""

import bisect


def solve(readings, width):
    if width <= 0 or width > len(readings):
        return []

    window = sorted(readings[:width])
    middle = width // 2
    out = []

    def median():
        if width % 2:
            return float(window[middle])
        return (window[middle - 1] + window[middle]) / 2.0

    out.append(median())
    for index in range(width, len(readings)):
        window.pop(0)
        bisect.insort(window, readings[index])
        out.append(median())
    return out
