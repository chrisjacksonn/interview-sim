# The classic error: totals outside, sizes inside. Counts orderings.
def solve(sizes, target):
    ways = [0] * (target + 1)
    ways[0] = 1
    uniq = sorted(set(sizes))
    for total in range(1, target + 1):
        for size in uniq:
            if 0 < size <= total:
                ways[total] += ways[total - size]
    return ways[target]
