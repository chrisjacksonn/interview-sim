"""Deliberately wrong: counts the departure as a stop, so every reachable route
costs one more than it should

Used by tools/qa.py to prove the hidden suite can tell this from correct.
"""

import heapq


def solve(distance, start_fuel, depots):
    ordered = sorted(depots)

    passed = []
    fuel = start_fuel
    stops = 1
    index = 0
    total = len(ordered)

    while fuel < distance:
        while index < total and ordered[index][0] <= fuel:
            heapq.heappush(passed, -ordered[index][1])
            index += 1
        if not passed:
            return -1
        fuel += -heapq.heappop(passed)
        stops += 1
    return stops
