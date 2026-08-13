"""Deliberately wrong: returns names in the order they were first seen rather
than sorted

Used by tools/qa.py to prove the hidden suite can tell this from correct.
"""


def solve(alerts, window):
    if window < 0:
        return []

    by_name = {}
    for name, stamp in alerts:
        by_name.setdefault(name, []).append(stamp)

    noisy = []
    for name, stamps in by_name.items():
        if len(stamps) < 2:
            continue
        ordered = sorted(stamps)
        for index in range(1, len(ordered)):
            if ordered[index] - ordered[index - 1] <= window:
                noisy.append(name)
                break
    return noisy
