from collections import deque
def solve(conveyors, start):
    adj = {}
    zones = set([start])
    for s, t in conveyors:
        adj.setdefault(s, []).append(t)
        zones.add(s); zones.add(t)
    hops = {z: -1 for z in zones}
    hops[start] = 0
    q = deque([start])
    while q:
        z = q.popleft()
        for n in adj.get(z, ()):
            if hops[n] == -1:
                hops[n] = hops[z] + 1
                q.append(n)
    return hops
