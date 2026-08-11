# Run Compression

A logging system squashes repeated characters, but only when squashing actually
saves space.

Write `solve(text)` that returns a compressed version of `text`:

- A run of **three or more** identical characters becomes the character followed
  by the run length, so `"aaaa"` becomes `"a4"`.
- A run of one or two characters is left exactly as it is, because `"aa"` is no
  longer than `"a2"`.

## Examples

```python
solve("aaabbc")
# "a3bbc"
# The run of three a's compresses. The two b's and single c do not.

solve("aaaaaaaaaaaa")
# "a12"

solve("abc")
# "abc"

solve("aabbbaa")
# "aab3aa"
# Runs are counted separately even when the character comes back later.

solve("")
# ""
```

## Constraints

- `0 <= len(text) <= 100_000`
- Any characters may appear, including digits, spaces, and punctuation.
- The result is a string, and it is not required to be shorter than the input.
