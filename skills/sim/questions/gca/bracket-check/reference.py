"""Reference solution for Bracket Check.

Never copied into a session workspace.
"""

PAIRS = {")": "(", "]": "[", "}": "{"}
OPENERS = frozenset(PAIRS.values())


def solve(text):
    stack = []
    for char in text:
        if char in OPENERS:
            stack.append(char)
        elif char in PAIRS:
            if not stack or stack.pop() != PAIRS[char]:
                return False
    return not stack
