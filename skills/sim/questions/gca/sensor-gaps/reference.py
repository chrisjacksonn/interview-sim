"""Reference solution for Sensor Gaps.

Never copied into a session workspace.
"""


def solve(readings):
    by_sensor = {}
    for sensor, timestamp in readings:
        by_sensor.setdefault(sensor, []).append(timestamp)

    longest = {}
    for sensor, stamps in by_sensor.items():
        if len(stamps) < 2:
            continue
        stamps.sort()
        widest = 0
        for index in range(1, len(stamps)):
            gap = stamps[index] - stamps[index - 1]
            if gap > widest:
                widest = gap
        longest[sensor] = widest
    return longest
