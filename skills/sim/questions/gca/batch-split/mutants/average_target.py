def solve(weights, crews):
    target = (sum(weights) + crews - 1) // crews
    return max(target, max(weights) if weights else 0)
