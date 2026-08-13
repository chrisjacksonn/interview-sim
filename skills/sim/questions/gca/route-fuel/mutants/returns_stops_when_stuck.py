"""Deliberately wrong: reports the stops it managed instead of -1 when the route
cannot be finished at all

Used by tools/qa.py to prove the hidden suite can tell this from correct.
"""

import heapq


def solve(distance, start_fuel, depots):
    ordered = sorted(depots)

    passed = []
    fuel = start_fuel
    stops = 0
    index = 0
    total = len(ordered)

    while fuel < distance:
        while index < total and ordered[index][0] <= fuel:
            heapq.heappush(passed, -ordered[index][1])
            index += 1
        if not passed:
            return stops
        fuel += -heapq.heappop(passed)
        stops += 1
    return stops
