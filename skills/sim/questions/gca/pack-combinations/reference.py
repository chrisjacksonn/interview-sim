"""Reference solution for Pack Combinations.

Never copied into a session workspace.

The loop order is the whole question. Sizes on the outside and totals on the
inside counts each combination once, because a combination is only ever built by
considering the sizes in a fixed order. Swapping the loops counts orderings
instead, and turns 1+2 and 2+1 into two answers.

Duplicate sizes are dropped first, since a repeated size offers nothing new.
"""


def solve(sizes, target):
    ways = [0] * (target + 1)
    ways[0] = 1

    for size in sorted(set(sizes)):
        if size <= 0 or size > target:
            continue
        for total in range(size, target + 1):
            ways[total] += ways[total - size]
    return ways[target]
