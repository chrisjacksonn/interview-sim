"""Reference solution for Shared Route.

Never copied into a session workspace.

Standard two-row dynamic programme. Only the previous row is needed, so memory
stays at O(min(n, m)) rather than the full table.
"""


def solve(first, second):
    if not first or not second:
        return 0

    # Iterate over the longer list, keep rows the length of the shorter one.
    if len(second) > len(first):
        first, second = second, first

    width = len(second)
    previous = [0] * (width + 1)
    current = [0] * (width + 1)

    for item in first:
        for index in range(width):
            if item == second[index]:
                current[index + 1] = previous[index] + 1
            elif previous[index + 1] >= current[index]:
                current[index + 1] = previous[index + 1]
            else:
                current[index + 1] = current[index]
        previous, current = current, previous
    return previous[width]
