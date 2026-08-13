"""Deliberately wrong: collapses repeated timestamps into a set, so an alert
firing twice at the same instant no longer looks like two firings

Used by tools/qa.py to prove the hidden suite can tell this from correct.
"""


def solve(alerts, window):
    if window < 0:
        return []

    by_name = {}
    for name, stamp in alerts:
        by_name.setdefault(name, set()).add(stamp)

    noisy = []
    for name, stamps in by_name.items():
        if len(stamps) < 2:
            continue
        ordered = sorted(stamps)
        for index in range(1, len(ordered)):
            if ordered[index] - ordered[index - 1] <= window:
                noisy.append(name)
                break
    return sorted(noisy)
