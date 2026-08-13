"""Deliberately wrong: a width larger than the reading count still produces one
window, built from fewer readings than asked for

Used by tools/qa.py to prove the hidden suite can tell this from correct.
"""

import bisect


def solve(readings, width):
    if width <= 0:
        return []

    window = sorted(readings[:width])
    if not window:
        return []
    middle = len(window) // 2
    out = []

    def median():
        if len(window) % 2:
            return float(window[middle])
        return (window[middle - 1] + window[middle]) / 2.0

    out.append(median())
    for index in range(width, len(readings)):
        leaving = readings[index - width]
        window.pop(bisect.bisect_left(window, leaving))
        bisect.insort(window, readings[index])
        out.append(median())
    return out
