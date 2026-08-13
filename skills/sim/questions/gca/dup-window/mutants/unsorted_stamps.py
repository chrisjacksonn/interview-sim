"""Deliberately wrong: compares timestamps in arrival order instead of sorting
them, so a close pair that arrives out of order is missed

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
        for index in range(1, len(stamps)):
            if stamps[index] - stamps[index - 1] <= window:
                noisy.append(name)
                break
    return sorted(noisy)
