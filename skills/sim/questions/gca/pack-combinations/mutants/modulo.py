MOD = 10 ** 9 + 7
def solve(sizes, target):
    ways = [0] * (target + 1)
    ways[0] = 1
    for size in sorted(set(sizes)):
        if size <= 0 or size > target: continue
        for total in range(size, target + 1):
            ways[total] = (ways[total] + ways[total - size]) % MOD
    return ways[target]
