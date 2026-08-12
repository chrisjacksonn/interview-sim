# Shift Coverage

A depot must be staffed continuously from minute `0` to minute `horizon`. Staff
offer shifts as `(start, end)` pairs, meaning they can work from `start` up to
`end`.

Write `solve(shifts, horizon)` that returns the **smallest number of shifts**
needed to cover every moment from `0` to `horizon`, or `-1` if it cannot be done.

Coverage rules:

- A shift `(s, e)` covers the stretch from `s` to `e`. Two shifts that meet
  exactly, such as `(0, 5)` and `(5, 9)`, leave no gap.
- The whole of `0` to `horizon` must be covered. Coverage beyond `horizon` is
  allowed and wasted.
- Shifts arrive in no particular order and may overlap, nest, or duplicate.
- A shift with `start >= end` covers nothing and is useless.
- If `horizon` is `0`, nothing needs covering and the answer is `0`.

## Examples

```python
solve([(0, 4), (2, 8), (7, 10)], 10)
# 3
# Every one of them is needed.

solve([(0, 5), (1, 9), (4, 6)], 9)
# 2
# (0, 5) then (1, 9). Picking (4, 6) second would strand the gap after 6.

solve([(0, 3), (5, 9)], 9)
# -1
# Nothing covers the stretch from 3 to 5.

solve([(2, 9)], 9)
# -1
# Coverage has to start at 0.

solve([], 0)
# 0
```

## Constraints

- `0 <= len(shifts) <= 200_000`
- `0 <= horizon <= 1_000_000_000`
- Shift bounds are integers and may exceed `horizon`.

A solution that tries every combination of shifts will not finish in time.
