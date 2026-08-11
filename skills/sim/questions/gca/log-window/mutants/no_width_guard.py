def solve(counts, width):
    if not counts: return 0
    run = sum(counts[:width]); best = run
    for i in range(width, len(counts)):
        run += counts[i] - counts[i-width]
        best = max(best, run)
    return best
