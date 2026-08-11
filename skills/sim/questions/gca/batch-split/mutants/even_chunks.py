def solve(weights, crews):
    n = len(weights)
    size = (n + crews - 1) // crews
    best = 0
    for i in range(0, n, size):
        best = max(best, sum(weights[i:i+size]))
    return best
