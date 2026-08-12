"""Reference solution for Route Fuel.

Drive as far as the fuel allows, keeping every depot passed in a max-heap. When
the tank runs out short of the end, take the largest depot seen so far. That is
optimal because any solution reaching this point must have taken some passed
depot, and none of them is worth more than the largest.
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
            # Negated because heapq is a min-heap.
            heapq.heappush(passed, -ordered[index][1])
            index += 1
        if not passed:
            return -1
        fuel += -heapq.heappop(passed)
        stops += 1
    return stops
