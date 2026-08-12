# Correct but slow: relaxes every edge repeatedly until nothing changes, which is
# O(V*E). Converges in a couple of passes on small or favourably-ordered graphs
# and not at all on a large one listed against the traversal order.
def solve(conveyors, start):
    hops = {start: 0}
    changed = True
    while changed:
        changed = False
        for s, t in conveyors:
            if s in hops and hops[s] + 1 < hops.get(t, 1 << 60):
                hops[t] = hops[s] + 1
                changed = True
    return hops
