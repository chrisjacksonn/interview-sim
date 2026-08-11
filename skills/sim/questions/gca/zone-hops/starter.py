"""Zone Hops.

Read problem.md for the full statement.
"""


def solve(conveyors, start):
    """Fewest one-way conveyors needed to reach each zone from start.

    Args:
        conveyors: list of (from_zone, to_zone) pairs. One-way. May contain
            duplicates, self-loops, and cycles.
        start: the zone to start from. Always in the result at 0 hops.

    Returns:
        dict mapping reachable zone to its minimum hop count. Unreachable zones
        are absent.
    """
    # Your code here.
    raise NotImplementedError
