# Dedupes the dependents list but not the blocked count, so a task named by a
# duplicate requirement can never reach zero and is never scheduled.
import heapq
def solve(tasks, requirements):
    known = set(tasks)
    dep = dict((t, []) for t in tasks); blocked = dict((t, 0) for t in tasks)
    seen = set()
    for b, a in requirements:
        if b not in known or a not in known: continue
        blocked[a] += 1
        if (b, a) in seen: continue
        seen.add((b, a)); dep[b].append(a)
    ready = [t for t in tasks if blocked[t] == 0]; heapq.heapify(ready)
    order = []
    while ready:
        t = heapq.heappop(ready); order.append(t)
        for f in dep[t]:
            blocked[f] -= 1
            if blocked[f] == 0: heapq.heappush(ready, f)
    return order if len(order) == len(tasks) else []
