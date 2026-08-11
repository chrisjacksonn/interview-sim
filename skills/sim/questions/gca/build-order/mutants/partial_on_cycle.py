import heapq
def solve(tasks, requirements):
    known = set(tasks)
    dep = dict((t, []) for t in tasks); blocked = dict((t, 0) for t in tasks)
    seen = set()
    for b, a in requirements:
        if b not in known or a not in known or (b, a) in seen: continue
        seen.add((b, a)); dep[b].append(a); blocked[a] += 1
    ready = [t for t in tasks if blocked[t] == 0]; heapq.heapify(ready)
    order = []
    while ready:
        t = heapq.heappop(ready); order.append(t)
        for f in dep[t]:
            blocked[f] -= 1
            if blocked[f] == 0: heapq.heappush(ready, f)
    return order
