# Route Fuel

A van drives a straight route of `distance` kilometres. It burns one litre per
kilometre and starts with `start_fuel` litres.

Along the way are depots, each `(position, litres)`, where `position` is the
distance from the start. The van may stop at any depot it can reach and take all
of its fuel. The tank has no limit.

Write `solve(distance, start_fuel, depots)` returning the smallest number of
stops needed to reach the end, or `-1` if it cannot be done.

## Examples

```python
solve(100, 10, [(10, 60), (20, 30), (30, 30), (60, 40)])
# 2
# Stop at 10 for 60, then at 60 for 40.

solve(100, 100, [])
# 0

solve(100, 1, [(10, 100)])
# -1
# It runs dry before the first depot.

solve(100, 50, [(25, 25), (50, 25)])
# 2
```

## Constraints

- `1 <= distance <= 1_000_000_000`
- `0 <= start_fuel <= 1_000_000_000`
- `0 <= len(depots) <= 100_000`
- Depots arrive in no particular order and may share a position.
- A depot exactly at `distance` is useless: arriving there is finishing.
- The input you are given must be left as it was. Do not modify or consume it.

Trying every combination of stops will not finish in time.
