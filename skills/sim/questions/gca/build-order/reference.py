"""Reference solution for Build Order.

Never copied into a session workspace.

Kahn's algorithm with a sorted ready set. The ready set is kept as a heap so the
alphabetically first available task is always the next one out.
"""

import heapq


def solve(tasks, requirements):
    known = set(tasks)
    dependents = dict((task, []) for task in tasks)
    blocked_by = dict((task, 0) for task in tasks)

    seen_pairs = set()
    for before, after in requirements:
        if before not in known or after not in known:
            continue
        if (before, after) in seen_pairs:
            continue
        seen_pairs.add((before, after))
        dependents[before].append(after)
        blocked_by[after] += 1

    ready = [task for task in tasks if blocked_by[task] == 0]
    heapq.heapify(ready)

    order = []
    while ready:
        task = heapq.heappop(ready)
        order.append(task)
        for follower in dependents[task]:
            blocked_by[follower] -= 1
            if blocked_by[follower] == 0:
                heapq.heappush(ready, follower)

    if len(order) != len(tasks):
        return []
    return order
