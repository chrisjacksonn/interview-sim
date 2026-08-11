# Descending inner loop makes each size usable at most once.
def solve(sizes, target):
    ways = [0] * (target + 1)
    ways[0] = 1
    for size in sorted(set(sizes)):
        if size <= 0 or size > target: continue
        for total in range(target, size - 1, -1):
            ways[total] += ways[total - size]
    return ways[target]
