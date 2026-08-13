"""Deliberately wrong: refuels at the first depot it can reach rather than the
largest one it has passed

Used by tools/qa.py to prove the hidden suite can tell this from correct.
"""


def solve(distance, start_fuel, depots):
    ordered = sorted(depots)

    fuel = start_fuel
    stops = 0
    index = 0
    total = len(ordered)

    while fuel < distance:
        if index >= total or ordered[index][0] > fuel:
            return -1
        fuel += ordered[index][1]
        index += 1
        stops += 1
    return stops
