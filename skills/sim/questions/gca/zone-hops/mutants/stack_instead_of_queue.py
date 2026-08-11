def solve(conveyors, start):
    adj = {}
    for s, t in conveyors:
        adj.setdefault(s, []).append(t)
    hops = {start: 0}
    stack = [start]
    while stack:
        z = stack.pop()
        for n in adj.get(z, ()):
            if n not in hops:
                hops[n] = hops[z] + 1
                stack.append(n)
    return hops
