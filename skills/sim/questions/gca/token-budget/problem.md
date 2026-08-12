# Token Budget

A batch job can run any subset of the available tasks. Each task costs some
tokens and returns some value. You have a fixed budget and each task may be run
at most once.

Write `solve(tasks, budget)` returning the greatest total value obtainable
without exceeding the budget.

`tasks` is a list of `(cost, value)` pairs.

## Examples

```python
solve([(3, 4), (4, 5), (2, 3)], 6)
# 8
# Costs 4 and 2, values 5 and 3. Taking 3 and 2 gives only 7.

solve([(5, 10)], 4)
# 0
# Nothing affordable.

solve([(0, 7)], 0)
# 7
# A free task is worth taking even on a zero budget.

solve([], 10)
# 0
```

## Constraints

- `0 <= len(tasks) <= 500`
- `0 <= budget <= 20_000`
- `0 <= cost <= 20_000`, `0 <= value <= 1_000_000`
- Each task may be used at most once. This is the whole difficulty.
- The input you are given must be left as it was. Do not modify or consume it.

Trying every subset will not finish in time.
