"""Deliberately wrong: averages the middle two with integer division, so an even
window reports a whole number

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
        return (window[middle - 1] + window[middle]) // 2

    out.append(median())
    for index in range(width, len(readings)):
        leaving = readings[index - width]
        window.pop(bisect.bisect_left(window, leaving))
        bisect.insort(window, readings[index])
        out.append(median())
    return out
