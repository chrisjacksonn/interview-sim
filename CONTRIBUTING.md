# Contributing

Welcome, in this order:

1. **Platform reports.** Windows, Codex, Cursor: did it work? An issue saying
   what happened is the most valuable thing a stranger can send.
2. **Bug reports**, ideally with the session transcript or the exact command
   and output.
3. **Bug fixes and features.** Open an issue before writing anything large:
   this is a side project with a small time budget, and agreeing on the shape
   first is what gets a PR merged fast.

## Before a PR

Everything must stay green:

```
python3 -m unittest discover -s tests
python3 tools/qa.py                  # every question passes the grading gate
python3 tools/check_repo.py          # nothing tracked belongs to one machine
python3 tools/check_symbols.py       # no top-level name defined twice
```

CI runs all of it on every commit, plus a fresh-clone job that uses the repo
as a stranger would.

## Style

- **Python 3.9 syntax, standard library only.** No `match`, no runtime
  `X | Y` annotations, no `tomllib`, no third-party imports anywhere,
  including tests. The floor is what machines actually have: Apple Command
  Line Tools still ships 3.9.6.
- Comments explain why, not what.
