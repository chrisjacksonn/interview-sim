# Quiet Streaks

A monitor records one error count per minute. A **quiet streak** is a run of
consecutive minutes with a count of exactly zero.

Write `solve(counts)` returning the length of the longest quiet streak.

## Examples

```python
solve([3, 0, 0, 1, 0, 0, 0, 2])
# 3

solve([0, 0, 0])
# 3

solve([1, 2, 3])
# 0

solve([])
# 0
```

## Constraints

- `0 <= len(counts) <= 200_000`
- Counts are non-negative integers.
- The input you are given must be left as it was. Do not modify or consume it.
