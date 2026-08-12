# Unique Run

A machine emits a stream of part codes. A **clean run** is a stretch of
consecutive codes with no repeats.

Write `solve(codes)` returning the length of the longest clean run.

## Examples

```python
solve(["a", "b", "c", "a", "d"])
# 4
# The run b, c, a, d has no repeats. Starting from the first a gives only 3.

solve(["x", "x", "x"])
# 1

solve(["p", "q", "r", "s"])
# 4

solve([])
# 0
```

## Constraints

- `0 <= len(codes) <= 200_000`
- Codes are non-empty, case-sensitive strings.
- The input you are given must be left as it was. Do not modify or consume it.

Checking every stretch will not finish in time.
