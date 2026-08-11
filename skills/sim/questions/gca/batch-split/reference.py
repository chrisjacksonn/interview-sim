"""Reference solution for Batch Split.

Never copied into a session workspace.

Binary search on the answer. For a candidate limit, greedily fill each shift
until adding the next parcel would exceed it; the number of shifts that takes is
the fewest possible for that limit, so the limit is feasible when that count is
at most `crews`. Using fewer shifts than allowed is fine because a group can
always be split further without raising the maximum.

The search runs from the heaviest single parcel (no group can be lighter than
its heaviest member) up to the total.
"""


def solve(weights, crews):
    low = max(weights) if weights else 0
    high = sum(weights)

    def shifts_needed(limit):
        used = 1
        load = 0
        for weight in weights:
            if load + weight > limit:
                used += 1
                load = weight
            else:
                load += weight
        return used

    while low < high:
        middle = (low + high) // 2
        if shifts_needed(middle) <= crews:
            high = middle
        else:
            low = middle + 1
    return low
