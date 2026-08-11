"""Reference solution for Log Window.

Never copied into a session workspace.

One pass with a running total: add the bucket entering the window, subtract the
one leaving it.
"""


def solve(counts, width):
    if width <= 0 or width > len(counts):
        return 0

    running = sum(counts[:width])
    best = running
    for index in range(width, len(counts)):
        running += counts[index] - counts[index - width]
        if running > best:
            best = running
    return best
