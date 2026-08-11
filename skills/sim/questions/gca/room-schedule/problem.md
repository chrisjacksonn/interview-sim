# Room Schedule

Meetings are booked as `(start, end)` pairs, where a meeting occupies the room
from `start` up to but not including `end`.

Write `solve(meetings)` returning the smallest number of rooms needed so that no
two meetings share a room at the same moment.

- A meeting ending exactly when another starts does not need a second room.
- A meeting with `start >= end` occupies nothing and is ignored.
- Meetings arrive in no particular order and may be duplicated.

## Examples

```python
solve([(0, 30), (5, 10), (15, 20)])
# 2
# The long meeting overlaps both short ones, but the short ones do not overlap
# each other.

solve([(0, 5), (5, 10), (10, 15)])
# 1
# Each ends exactly as the next begins.

solve([(1, 4), (1, 4), (1, 4)])
# 3

solve([])
# 0
```

## Constraints

- `0 <= len(meetings) <= 200_000`
- Times are integers and may be negative.
