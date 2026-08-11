def solve(text):
    if not text:
        return ""
    counts = {}
    for c in text:
        counts[c] = counts.get(c, 0) + 1
    out, seen = [], set()
    for c in text:
        if c in seen:
            continue
        seen.add(c)
        k = counts[c]
        out.append(c + str(k) if k >= 3 else c * k)
    return "".join(out)
