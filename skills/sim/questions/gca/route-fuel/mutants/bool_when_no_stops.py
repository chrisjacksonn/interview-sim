"""Deliberately wrong: answers the "does it need refuelling" question with a
boolean, which counts as zero without being an int

Used by tools/qa.py to prove the hidden suite can tell this from correct.
"""

import heapq


def solve(distance, start_fuel, depots):
    if start_fuel >= distance:
        return start_fuel < distance

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
            return -1
        fuel += -heapq.heappop(passed)
        stops += 1
    return stops
