PAIRS = {")": "(", "]": "[", "}": "{"}
OPEN = frozenset(PAIRS.values())
def solve(text):
    stack = []
    for c in text:
        if c in OPEN: stack.append(c)
        elif c in PAIRS:
            if stack and stack.pop() != PAIRS[c]: return False
    return not stack
