import sys
def solve(sizes, target):
    sys.setrecursionlimit(100000)
    uniq = sorted(set(s for s in sizes if s > 0))
    def go(i, rem):
        if rem == 0: return 1
        if i >= len(uniq): return 0
        total = 0
        take = 0
        while take * uniq[i] <= rem:
            total += go(i + 1, rem - take * uniq[i])
            take += 1
        return total
    return go(0, target)
