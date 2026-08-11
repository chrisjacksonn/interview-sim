# Shelf Tally

A warehouse logs restock events as strings. Each well-formed entry looks like:

```
A12-3:40
```

which means aisle `A12`, shelf `3`, and `40` units added.

Write `solve(entries)` that takes a list of strings and returns a dictionary
mapping each aisle to the total units added across all of its shelves.

Entries that do not match the format are logged by faulty scanners and must be
skipped rather than raising. An entry is malformed if any of the following hold:

- it does not contain exactly one `-` and exactly one `:`, in that order
- the aisle part is empty
- the shelf part is not a non-negative integer
- the count part is not an integer
- the count is negative

Aisles that end up with no valid entries must not appear in the result. Leading
and trailing whitespace around a whole entry is not an error and should be
ignored.

## Examples

```python
solve(["A12-3:40", "A12-1:5", "B7-2:12"])
# {"A12": 45, "B7": 12}

solve(["A1-0:0", "A1-1:7"])
# {"A1": 7}

solve(["Q9-2:15", "broken", "Q9-x:4", "Q9-2:-3", "", "Q9-1:5"])
# {"Q9": 20}

solve([])
# {}
```

In the third example, `"broken"` has no separators, `"Q9-x:4"` has a
non-integer shelf, and `"Q9-2:-3"` has a negative count, so all three are
skipped. A count of `0` is valid and contributes nothing, which is why `"A1-0:0"`
does not stop `A1` from appearing.

## Constraints

- `0 <= len(entries) <= 10_000`
- Each entry is at most 50 characters.
- Aisle labels are case-sensitive: `a1` and `A1` are different aisles.
