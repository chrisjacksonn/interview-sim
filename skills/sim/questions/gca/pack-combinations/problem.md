# Pack Combinations

A warehouse ships orders using boxes of fixed sizes. Every box size is available
in unlimited quantity.

Write `solve(sizes, target)` returning how many **distinct combinations** of
boxes hold exactly `target` units.

Two combinations are the same if they use the same number of each size. Order
does not matter, so `2 + 3` and `3 + 2` are one combination, not two.

## Examples

```python
solve([1, 2, 5], 5)
# 4
# 1+1+1+1+1, 1+1+1+2, 1+2+2, 5

solve([2], 3)
# 0

solve([3], 0)
# 1
# Exactly one way to hold nothing: use no boxes at all.

solve([], 0)
# 1

solve([], 7)
# 0
```

## Constraints

- `0 <= len(sizes) <= 200`
- `0 <= target <= 20_000`
- Box sizes are positive integers. `sizes` may contain duplicates, and a repeated
  size does not create extra combinations.

Enumerating every combination will not finish in time. The answer can be very
large; return it exactly, not modulo anything.
