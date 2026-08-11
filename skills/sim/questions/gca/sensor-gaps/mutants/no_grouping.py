def solve(readings):
    out = {}
    for i in range(1, len(readings)):
        s, t = readings[i]
        gap = t - readings[i-1][1]
        if gap > out.get(s, -1):
            out[s] = gap
    return out
