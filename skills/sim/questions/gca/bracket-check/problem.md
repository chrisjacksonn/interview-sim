# Bracket Check

A config format uses three kinds of bracket: `()`, `[]`, and `{}`.

Write `solve(text)` returning `True` if every bracket in `text` is closed by a
matching bracket in the right order, and `False` otherwise.

- Characters that are not brackets are ignored entirely.
- A string with no brackets at all is balanced.
- Brackets must close in the order they were opened, so `([)]` is not balanced.

## Examples

```python
solve("a(b[c]d)e")
# True

solve("([)]")
# False
# The square bracket closes while the round one is still open.

solve("(((")
# False

solve("no brackets here")
# True

solve("")
# True
```

## Constraints

- `0 <= len(text) <= 200_000`
- Any characters may appear.
