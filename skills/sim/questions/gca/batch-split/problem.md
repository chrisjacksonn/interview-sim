# Batch Split

A packing line receives parcels in a fixed order and must divide them across
exactly `crews` shifts. A shift takes a **contiguous** run of parcels, the order
cannot be changed, and every shift must get at least one parcel.

A shift's load is the total weight of its parcels. The day finishes when the
slowest shift finishes, so the cost of a split is the **largest** shift load.

Write `solve(weights, crews)` returning the smallest possible largest load.

## Examples

```python
solve([7, 2, 5, 10, 8], 2)
# 18
# Split as [7, 2, 5] and [10, 8]: loads 14 and 18. Every other split is worse.

solve([1, 2, 3, 4, 5], 2)
# 9
# [1, 2, 3, 4] and [5] gives 10. [1, 2, 3] and [4, 5] gives 9.

solve([5, 5, 5, 5], 4)
# 5

solve([10], 1)
# 10
```

## Constraints

- `1 <= len(weights) <= 200_000`
- `1 <= crews <= len(weights)`
- `0 <= weights[i] <= 1_000_000`
- The input you are given must be left as it was. Do not modify or consume it.

Trying every split will not finish in time.
