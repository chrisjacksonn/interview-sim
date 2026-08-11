def solve(first, second):
    from collections import Counter
    a, b = Counter(first), Counter(second)
    return sum(min(a[k], b[k]) for k in a if k in b)
