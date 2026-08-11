"""Reference solution for Shift Coverage.

Never copied into a session workspace.

Sort by start, then sweep: among every shift that starts at or before the point
currently reached, take the one reaching furthest. That greedy choice is optimal
because any covering set must include some shift spanning the current point, and
none of them can do better than the furthest-reaching one.
"""


def solve(shifts, horizon):
    if horizon <= 0:
        return 0

    ordered = sorted(shifts)

    count = 0
    covered = 0
    index = 0
    total = len(ordered)

    while covered < horizon:
        furthest = covered
        while index < total and ordered[index][0] <= covered:
            end = ordered[index][1]
            if end > furthest:
                furthest = end
            index += 1
        if furthest == covered:
            return -1
        covered = furthest
        count += 1
    return count
