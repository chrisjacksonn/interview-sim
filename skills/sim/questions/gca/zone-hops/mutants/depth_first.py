def solve(conveyors, start):
    out = {}
    for s, t in conveyors:
        out.setdefault(s, []).append(t)
    hops = {}
    def walk(z, d):
        if z in hops:
            return
        hops[z] = d
        for n in out.get(z, ()):
            walk(n, d + 1)
    walk(start, 0)
    return hops
