from collections import deque
def solve(conveyors, start):
    adj = {}
    for s, t in conveyors:
        adj.setdefault(s, []).append(t)
    hops = {start: 0}
    q = deque([start])
    while q:
        z = q.popleft()
        for n in adj.get(z, ()):
            hops[n] = hops[z] + 1
            q.append(n)
    return hops
