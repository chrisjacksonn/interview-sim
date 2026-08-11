"""Reference solution for Room Schedule.

Never copied into a session workspace.

A sweep over the endpoints. Every start is +1 and every end is -1, and ends are
processed before starts at the same instant, which is what makes a meeting
ending at 10 free the room for one starting at 10.
"""


def solve(meetings):
    events = []
    for start, end in meetings:
        if start >= end:
            continue
        events.append((start, 1))
        events.append((end, -1))

    # Sorting by (time, delta) puts -1 before +1 at the same time, since -1 < 1.
    events.sort()

    rooms = 0
    most = 0
    for _, delta in events:
        rooms += delta
        if rooms > most:
            most = rooms
    return most
