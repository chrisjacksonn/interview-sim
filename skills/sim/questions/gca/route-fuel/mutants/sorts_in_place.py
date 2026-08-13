"""Deliberately wrong: sorts the caller's depot list in place

Used by tools/qa.py to prove the hidden suite can tell this from correct.
"""

import heapq


def solve(distance, start_fuel, depots):
    depots.sort()

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
