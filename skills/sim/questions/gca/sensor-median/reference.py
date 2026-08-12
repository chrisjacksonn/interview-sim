"""Reference solution for Rolling Median.

Keeps the window sorted and uses bisect to move it, which is fast enough at
these sizes without reaching for two heaps and lazy deletion.
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
        leaving = readings[index - width]
        window.pop(bisect.bisect_left(window, leaving))
        bisect.insort(window, readings[index])
        out.append(median())
    return out
