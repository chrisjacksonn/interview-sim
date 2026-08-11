from collections import deque
def solve(conveyors, start):
    adj = {}
    for s, t in conveyors:
        adj.setdefault(s, []).append(t)
        adj.setdefault(t, []).append(s)
    hops = {start: 0}
    q = deque([start])
    while q:
        z = q.popleft()
        for n in adj.get(z, ()):
            if n not in hops:
                hops[n] = hops[z] + 1
                q.append(n)
    return hops
