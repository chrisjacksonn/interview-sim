def solve(tasks, requirements):
    known = set(tasks)
    dep = dict((t, []) for t in tasks); blocked = dict((t, 0) for t in tasks)
    seen = set()
    for b, a in requirements:
        if b not in known or a not in known or (b, a) in seen: continue
        seen.add((b, a)); dep[b].append(a); blocked[a] += 1
    ready = sorted(t for t in tasks if blocked[t] == 0)
    order = []
    while ready:
        t = ready.pop(0); order.append(t)
        for f in dep[t]:
            blocked[f] -= 1
            if blocked[f] == 0:
                ready.append(f)
    return order if len(order) == len(tasks) else []
