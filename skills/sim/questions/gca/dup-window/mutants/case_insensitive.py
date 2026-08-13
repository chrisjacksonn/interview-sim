"""Deliberately wrong: folds case, so two differently-cased names are treated as
one alert

Used by tools/qa.py to prove the hidden suite can tell this from correct.
"""


def solve(alerts, window):
    if window < 0:
        return []

    by_name = {}
    for name, stamp in alerts:
        by_name.setdefault(name.lower(), []).append(stamp)

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
