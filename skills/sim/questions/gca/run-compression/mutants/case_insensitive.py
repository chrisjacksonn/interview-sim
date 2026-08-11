def solve(text):
    if not text:
        return ""
    out, ch, n = [], text[0], 1
    def flush(c, k):
        out.append(c + str(k) if k >= 3 else c * k)
    for c in text[1:]:
        if c.lower() == ch.lower():
            n += 1
        else:
            flush(ch, n); ch, n = c, 1
    flush(ch, n)
    return "".join(out)
