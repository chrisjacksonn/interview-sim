"""Reference solution for Quiet Streaks."""


def solve(counts):
    best = 0
    run = 0
    for count in counts:
        if count == 0:
            run += 1
            if run > best:
                best = run
        else:
            run = 0
    return best
