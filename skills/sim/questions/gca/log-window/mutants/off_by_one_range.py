def solve(counts, width):
    if width <= 0 or width > len(counts): return 0
    run = sum(counts[:width]); best = run
    for i in range(width, len(counts)-1):
        run += counts[i] - counts[i-width]
        best = max(best, run)
    return best
