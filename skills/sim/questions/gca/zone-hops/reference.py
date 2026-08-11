"""Reference solution for Zone Hops.

Never copied into a session workspace.
"""

from collections import deque


def solve(conveyors, start):
    outgoing = {}
    for source, target in conveyors:
        outgoing.setdefault(source, []).append(target)

    hops = {start: 0}
    queue = deque([start])
    while queue:
        zone = queue.popleft()
        distance = hops[zone]
        for neighbour in outgoing.get(zone, ()):
            if neighbour not in hops:
                hops[neighbour] = distance + 1
                queue.append(neighbour)
    return hops
