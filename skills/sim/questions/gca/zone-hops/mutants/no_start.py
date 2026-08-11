from collections import deque
def solve(conveyors, start):
    adj = {}
    for s, t in conveyors:
        adj.setdefault(s, []).append(t)
    hops = {}
    q = deque([(start, 0)])
    seen = set([start])
    while q:
        z, d = q.popleft()
        if d:
            hops[z] = d
        for n in adj.get(z, ()):
            if n not in seen:
                seen.add(n)
                q.append((n, d + 1))
    return hops
