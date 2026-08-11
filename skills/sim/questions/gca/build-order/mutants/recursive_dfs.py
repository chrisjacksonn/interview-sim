def solve(tasks, requirements):
    known = set(tasks)
    dep = dict((t, []) for t in tasks)
    seen_pairs = set()
    for b, a in requirements:
        if b not in known or a not in known or (b, a) in seen_pairs: continue
        seen_pairs.add((b, a)); dep[b].append(a)
    state = {}; order = []
    def visit(t):
        if state.get(t) == 1: raise ValueError("cycle")
        if state.get(t) == 2: return
        state[t] = 1
        for f in sorted(dep[t]): visit(f)
        state[t] = 2; order.append(t)
    try:
        for t in sorted(tasks): visit(t)
    except ValueError:
        return []
    except RecursionError:
        return []
    return order[::-1]
