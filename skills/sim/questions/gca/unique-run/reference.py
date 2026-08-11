"""Reference solution for Unique Run.

Never copied into a session workspace.

Sliding window. last_seen holds the most recent index of each code; when a
repeat turns up inside the window, the left edge jumps past its previous
position. The max() on the left edge matters: a stale entry from before the
current window must not drag it backwards.
"""


def solve(codes):
    last_seen = {}
    longest = 0
    left = 0

    for right, code in enumerate(codes):
        previous = last_seen.get(code)
        if previous is not None and previous >= left:
            left = previous + 1
        last_seen[code] = right
        width = right - left + 1
        if width > longest:
            longest = width
    return longest
