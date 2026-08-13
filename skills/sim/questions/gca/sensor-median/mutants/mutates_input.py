"""Deliberately wrong: sorts the caller's readings in place before scanning, so
every window comes from the sorted series

Used by tools/qa.py to prove the hidden suite can tell this from correct.
"""


def solve(readings, width):
    if width <= 0 or width > len(readings):
        return []

    readings.sort()
    middle = width // 2
    out = []
    for start in range(0, len(readings) - width + 1):
        window = sorted(readings[start:start + width])
        if width % 2:
            out.append(float(window[middle]))
        else:
            out.append((window[middle - 1] + window[middle]) / 2.0)
    return out
