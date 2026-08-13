"""Deliberately wrong: sorts the caller's list in place to group the names

Used by tools/qa.py to prove the hidden suite can tell this from correct.
"""


def solve(alerts, window):
    if window < 0:
        return []

    alerts.sort()

    noisy = []
    index = 0
    total = len(alerts)
    while index < total:
        name = alerts[index][0]
        run = index
        while run < total and alerts[run][0] == name:
            run += 1
        stamps = [alerts[at][1] for at in range(index, run)]
        for at in range(1, len(stamps)):
            if stamps[at] - stamps[at - 1] <= window:
                noisy.append(name)
                break
        index = run
    return sorted(noisy)
