# Rolling Median

A sensor reports a reading every second. Write `solve(readings, width)`
returning the median of every window of `width` consecutive readings, in order.

The median of an even-sized window is the average of the two middle values, as a
float. For an odd-sized window it is the middle value, also as a float.

- Return an empty list if `width` is zero or negative, or larger than the number
  of readings.

## Examples

```python
solve([1, 3, 2, 5, 4], 3)
# [2.0, 3.0, 4.0]

solve([1, 2, 3, 4], 2)
# [1.5, 2.5, 3.5]

solve([5], 1)
# [5.0]

solve([1, 2], 5)
# []
```

## Constraints

- `0 <= len(readings) <= 50_000`
- Readings are integers and may be negative.
- The input you are given must be left as it was. Do not modify or consume it.

Re-sorting each window from scratch is acceptable here but will be slow on the
largest inputs.
