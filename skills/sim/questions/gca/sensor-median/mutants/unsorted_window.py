"""Deliberately wrong: takes the middle of the window in arrival order instead of
sorting it, which is the position, not the median

Used by tools/qa.py to prove the hidden suite can tell this from correct.
"""


def solve(readings, width):
    if width <= 0 or width > len(readings):
        return []

    middle = width // 2
    out = []
    for start in range(0, len(readings) - width + 1):
        window = readings[start:start + width]
        if width % 2:
            out.append(float(window[middle]))
        else:
            out.append((window[middle - 1] + window[middle]) / 2.0)
    return out
