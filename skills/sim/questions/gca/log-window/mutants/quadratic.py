def solve(counts, width):
    if width <= 0 or width > len(counts): return 0
    return max(sum(counts[i:i+width]) for i in range(len(counts)-width+1))
