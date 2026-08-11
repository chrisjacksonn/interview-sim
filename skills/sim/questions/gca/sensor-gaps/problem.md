# Sensor Gaps

A fleet of sensors reports in at irregular times. You are given a list of
readings, each a `(sensor_id, timestamp)` pair:

```python
[("s1", 100), ("s2", 40), ("s1", 250), ("s1", 130)]
```

For each sensor, the **gap** between two consecutive reports is the difference
between their timestamps once that sensor's reports are put in time order.

Write `solve(readings)` that returns a dictionary mapping each sensor to its
longest gap.

Rules:

- Readings arrive in no particular order, and different sensors are interleaved.
- A sensor with fewer than two readings has no gap at all and must not appear in
  the result.
- Two readings at the same timestamp are a gap of `0`, which is a real gap.
- Timestamps may be negative.

## Examples

```python
solve([("s1", 100), ("s2", 40), ("s1", 250), ("s1", 130)])
# {"s1": 120}
# s1 sorted is 100, 130, 250 -> gaps of 30 and 120. s2 has one reading, so it is
# left out.

solve([("a", 5), ("a", 5)])
# {"a": 0}

solve([("x", 10), ("x", -10), ("y", 3), ("y", 8), ("y", 4)])
# {"x": 20, "y": 4}

solve([])
# {}
```

## Constraints

- `0 <= len(readings) <= 50_000`
- Sensor ids are non-empty strings and are case-sensitive.
- Timestamps are integers, possibly negative, and fit in a machine word.
