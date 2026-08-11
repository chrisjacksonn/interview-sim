# Build Order

A build system runs tasks, some of which must wait for others. You are given the
task names and a list of `(before, after)` pairs meaning `before` must run at
some point before `after`.

Write `solve(tasks, requirements)` that returns a list containing every task in a
valid order, or an empty list if no such order exists.

## Ties

Several orders are usually valid, so the answer must be pinned down: whenever
more than one task is ready to run, take the one that sorts first
alphabetically.

## Rules

- Every task in `tasks` appears exactly once in the result.
- A requirement mentioning a task not in `tasks` is ignored.
- Duplicate requirements are allowed and mean nothing extra.
- If the requirements contain a cycle, return `[]`.
- A task that requires itself is a cycle.

## Examples

```python
solve(["a", "b", "c"], [("a", "b"), ("b", "c")])
# ["a", "b", "c"]

solve(["a", "b", "c"], [])
# ["a", "b", "c"]
# Nothing is blocked, so it is purely alphabetical.

solve(["build", "test", "lint"], [("build", "test")])
# ["build", "lint", "test"]
# At the start, build and lint are both ready. "build" sorts first. Then lint
# and test are both ready, and "lint" sorts first.

solve(["a", "b"], [("a", "b"), ("b", "a")])
# []

solve([], [])
# []
```

## Constraints

- `0 <= len(tasks) <= 20_000`
- `0 <= len(requirements) <= 100_000`
- Task names are non-empty, case-sensitive strings, and `tasks` has no duplicates.
