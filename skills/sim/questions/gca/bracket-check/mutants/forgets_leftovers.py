PAIRS = {")": "(", "]": "[", "}": "{"}
OPEN = frozenset(PAIRS.values())
def solve(text):
    stack = []
    for c in text:
        if c in OPEN: stack.append(c)
        elif c in PAIRS:
            if not stack or stack.pop() != PAIRS[c]: return False
    return True
