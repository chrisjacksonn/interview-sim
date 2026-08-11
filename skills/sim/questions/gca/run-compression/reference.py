"""Reference solution for Run Compression.

Never copied into a session workspace.
"""


def solve(text):
    if not text:
        return ""

    pieces = []
    run_char = text[0]
    run_length = 1

    def flush(char, length):
        if length >= 3:
            pieces.append(char)
            pieces.append(str(length))
        else:
            pieces.append(char * length)

    for char in text[1:]:
        if char == run_char:
            run_length += 1
        else:
            flush(run_char, run_length)
            run_char = char
            run_length = 1
    flush(run_char, run_length)
    return "".join(pieces)
