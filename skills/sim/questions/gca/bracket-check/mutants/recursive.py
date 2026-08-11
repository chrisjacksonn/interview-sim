import sys
PAIRS = {")": "(", "]": "[", "}": "{"}
OPEN = frozenset(PAIRS.values())
def solve(text):
    sys.setrecursionlimit(20000)
    def go(i, stack):
        if i == len(text): return not stack
        c = text[i]
        if c in OPEN: return go(i+1, stack + [c])
        if c in PAIRS:
            if not stack or stack[-1] != PAIRS[c]: return False
            return go(i+1, stack[:-1])
        return go(i+1, stack)
    return go(0, [])
