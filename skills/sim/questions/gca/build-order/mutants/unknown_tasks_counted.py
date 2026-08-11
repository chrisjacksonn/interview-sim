import heapq
def solve(tasks, requirements):
    dep = {}; blocked = dict((t, 0) for t in tasks)
    seen = set()
    for b, a in requirements:
        if (b, a) in seen: continue
        seen.add((b, a))
        dep.setdefault(b, []).append(a)
        blocked[a] = blocked.get(a, 0) + 1
    ready = [t for t in tasks if blocked.get(t, 0) == 0]; heapq.heapify(ready)
    order = []
    while ready:
        t = heapq.heappop(ready); order.append(t)
        for f in dep.get(t, ()):
            if f not in blocked: continue
            blocked[f] -= 1
            if blocked[f] == 0: heapq.heappush(ready, f)
    return order if len(order) == len(tasks) else []
