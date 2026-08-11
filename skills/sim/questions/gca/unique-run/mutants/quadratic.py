def solve(codes):
    best = 0
    n = len(codes)
    for i in range(n):
        seen = set()
        for j in range(i, n):
            if codes[j] in seen: break
            seen.add(codes[j])
            if j - i + 1 > best: best = j - i + 1
    return best
