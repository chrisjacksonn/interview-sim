import sys
def solve(first, second):
    sys.setrecursionlimit(10000)
    def go(i, j):
        if i >= len(first) or j >= len(second): return 0
        if first[i] == second[j]: return 1 + go(i+1, j+1)
        return max(go(i+1, j), go(i, j+1))
    return go(0, 0)
