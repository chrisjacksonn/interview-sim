# Shared Route

Two delivery vans each drive a route, recorded as the list of stop codes they
visited in order.

Write `solve(first, second)` that returns the length of the longest sequence of
stops that both vans visited **in the same relative order**. The stops do not
have to be next to each other in either route.

## Examples

```python
solve(["a", "b", "c", "d"], ["b", "d"])
# 2
# b then d appears in both.

solve(["a", "b", "c"], ["c", "b", "a"])
# 1
# Any single stop is shared, but no pair is in the same order in both.

solve(["x", "y", "x", "z", "y"], ["x", "y", "y"])
# 3
# x, y, y: take the first x, the second y is matched from the trailing y.

solve(["a", "b"], [])
# 0
```

## Constraints

- `0 <= len(first) <= 1500`
- `0 <= len(second) <= 1500`
- Stop codes are non-empty, case-sensitive strings and may repeat within a route.

Checking every possible subsequence will not finish in time.
