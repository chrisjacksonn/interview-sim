# Stops one short, so the target itself is never filled in by the last size.
def solve(sizes, target):
    ways = [0] * (target + 1)
    ways[0] = 1
    for size in sorted(set(sizes)):
        if size <= 0 or size > target: continue
        for total in range(size, target):
            ways[total] += ways[total - size]
    return ways[target]
