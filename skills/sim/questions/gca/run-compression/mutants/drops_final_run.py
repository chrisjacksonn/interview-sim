def solve(text):
    if not text:
        return ""
    out, ch, n = [], text[0], 1
    for c in text[1:]:
        if c == ch:
            n += 1
        else:
            out.append(ch + str(n) if n >= 3 else ch * n)
            ch, n = c, 1
    return "".join(out)
