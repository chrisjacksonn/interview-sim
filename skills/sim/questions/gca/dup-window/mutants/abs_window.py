"""Deliberately wrong: takes the magnitude of the window, so a negative window
behaves like a positive one instead of matching nothing

Used by tools/qa.py to prove the hidden suite can tell this from correct.
"""


def solve(alerts, window):
    span = abs(window)

    by_name = {}
    for name, stamp in alerts:
        by_name.setdefault(name, []).append(stamp)

    noisy = []
    for name, stamps in by_name.items():
        if len(stamps) < 2:
            continue
        ordered = sorted(stamps)
        for index in range(1, len(ordered)):
            if ordered[index] - ordered[index - 1] <= span:
                noisy.append(name)
                break
    return sorted(noisy)
