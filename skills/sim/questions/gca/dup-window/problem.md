# Repeat Alerts

An alerting system fires alerts, each with a name and a timestamp. An alert is
**noisy** if the same name fires twice within `window` minutes of each other,
counting the gap inclusively.

Write `solve(alerts, window)` returning the sorted list of noisy alert names.

`alerts` is a list of `(name, timestamp)` pairs in no particular order.

## Examples

```python
solve([("disk", 1), ("cpu", 3), ("disk", 4)], 5)
# ["disk"]
# The two disk alerts are 3 apart, within the window of 5.

solve([("disk", 1), ("disk", 40)], 5)
# []

solve([("a", 1), ("a", 6), ("b", 2), ("b", 3)], 5)
# ["a", "b"]
# Exactly 5 apart counts, because the gap is inclusive.

solve([], 10)
# []
```

## Constraints

- `0 <= len(alerts) <= 200_000`
- `window` may be zero or negative, in which case only alerts sharing a
  timestamp exactly are noisy, and a negative window makes nothing noisy.
- Names are case-sensitive. Timestamps are integers and may be negative.
- The input you are given must be left as it was. Do not modify or consume it.
