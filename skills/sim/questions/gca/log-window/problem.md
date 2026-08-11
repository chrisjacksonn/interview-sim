# Log Window

A service records how many errors it saw in each one-minute bucket.

Write `solve(counts, width)` that returns the largest total errors in any run of
`width` consecutive buckets.

- Return `0` if `width` is zero or negative.
- Return `0` if there are fewer than `width` buckets.
- Counts are non-negative.

## Examples

```python
solve([1, 4, 2, 10, 2, 3, 1, 0, 20], 4)
# 24
# Buckets 10, 2, 3, 1 total 16; buckets 3, 1, 0, 20 total 24.

solve([5], 1)
# 5

solve([1, 2], 5)
# 0

solve([], 3)
# 0
```

## Constraints

- `0 <= len(counts) <= 300_000`
- `0 <= counts[i] <= 10_000`
- Recomputing each window from scratch will not finish in time.
