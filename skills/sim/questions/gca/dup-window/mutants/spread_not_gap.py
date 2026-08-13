"""Deliberately wrong: measures the whole spread from first to last firing rather
than the gap between consecutive ones, so a close pair inside a long-running
alert is missed

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
        if max(stamps) - min(stamps) <= window:
            noisy.append(name)
    return sorted(noisy)
