def solve(text):
    for o, c in (("(", ")"), ("[", "]"), ("{", "}")):
        if text.count(o) != text.count(c): return False
    return True
