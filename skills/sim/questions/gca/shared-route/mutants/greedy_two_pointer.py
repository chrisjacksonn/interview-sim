def solve(first, second):
    i = j = n = 0
    while i < len(first) and j < len(second):
        if first[i] == second[j]:
            n += 1; i += 1; j += 1
        else:
            i += 1
    return n
