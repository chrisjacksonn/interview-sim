"""Deliberately wrong: sweeps the depots in the order given, so depots listed out
of position order are never seen as reachable

Used by tools/qa.py to prove the hidden suite can tell this from correct.
"""

import heapq


def solve(distance, start_fuel, depots):
    passed = []
    fuel = start_fuel
    stops = 0
    index = 0
    total = len(depots)

    while fuel < distance:
        while index < total and depots[index][0] <= fuel:
            heapq.heappush(passed, -depots[index][1])
            index += 1
        if not passed:
            return -1
        fuel += -heapq.heappop(passed)
        stops += 1
    return stops
