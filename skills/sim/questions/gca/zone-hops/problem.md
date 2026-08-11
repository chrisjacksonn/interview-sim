# Zone Hops

A sorting facility moves parcels between zones on one-way conveyors. You are
given the conveyors as `(from_zone, to_zone)` pairs and a starting zone.

```python
conveyors = [("A", "B"), ("B", "C"), ("A", "C"), ("C", "D")]
start = "A"
```

Write `solve(conveyors, start)` that returns a dictionary mapping every zone
reachable from `start` to the **fewest conveyors** needed to get there.

Rules:

- Conveyors are one-way. `("A", "B")` does not let you travel from B to A.
- The start zone is reachable in `0` hops and is always in the result, even if no
  conveyor touches it.
- Zones that cannot be reached from `start` must not appear.
- The input may contain duplicate conveyors, self-loops such as `("A", "A")`, and
  cycles.

## Examples

```python
solve([("A", "B"), ("B", "C"), ("A", "C"), ("C", "D")], "A")
# {"A": 0, "B": 1, "C": 1, "D": 2}
# C is reachable directly from A, so it is 1 hop and not 2.

solve([("A", "B"), ("C", "D")], "A")
# {"A": 0, "B": 1}
# C and D exist but nothing reaches them from A.

solve([], "solo")
# {"solo": 0}

solve([("A", "B"), ("B", "A")], "B")
# {"B": 0, "A": 1}
```

## Constraints

- `0 <= len(conveyors) <= 100_000`
- Zone names are non-empty, case-sensitive strings.
- `start` may be a zone that appears in no conveyor.
