OPEN = frozenset("([{")
CLOSE = frozenset(")]}")
def solve(text):
    depth = 0
    for c in text:
        if c in OPEN: depth += 1
        elif c in CLOSE:
            depth -= 1
            if depth < 0: return False
    return depth == 0
