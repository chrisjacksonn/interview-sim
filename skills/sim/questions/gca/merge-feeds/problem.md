# Merge Feeds

Several sensors each write a feed of readings, and each feed is already sorted
from smallest to largest.

Write `solve(feeds, limit)` that returns the `limit` smallest readings across all
feeds, in sorted order.

- `feeds` is a list of lists. Each inner list is already sorted ascending.
- Duplicates are real readings and each one counts separately.
- Return fewer than `limit` if there are not that many readings in total.
- Return an empty list if `limit` is zero or negative.

## Examples

```python
solve([[1, 4, 9], [2, 3], [5]], 4)
# [1, 2, 3, 4]

solve([[1, 1, 1], [1]], 3)
# [1, 1, 1]

solve([[7], [8]], 10)
# [7, 8]

solve([[1, 2, 3]], 0)
# []

solve([], 5)
# []
```

## Constraints

- `0 <= len(feeds) <= 10_000`
- Total readings across all feeds is at most `500_000`.
- Readings are integers and may be negative.
- Some feeds may be empty.
- The input you are given must be left as it was. Do not modify or consume it.

`limit` is often far smaller than the total number of readings.
