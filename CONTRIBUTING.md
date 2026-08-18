# Contributing

Welcome, in this order:

1. **Platform reports.** Windows, Codex, Cursor: did it work? An issue saying
   what happened is the most valuable thing a stranger can send.
2. **Bug reports**, ideally with the session transcript or the exact command
   and output.
3. **Bug fixes and features.** Open an issue before writing anything large:
   this is a side project with a small time budget, and agreeing on the shape
   first is what gets a PR merged fast.

**Question PRs are not accepted.** Sessions for a researched company write
their question live, and the small shipped corpus (instant no-company mocks,
plus the fixtures CI proves the gate against) is maintained here. A PR adding
questions will be closed with thanks.

## The rule that covers everything

**Nothing real, nothing cheat-adjacent.** No real assessment items or
recognisable derivatives, from any source, in any file. No capability for
interacting with a live assessment, a proctoring system, or a browser
session. See [ETHICS.md](ETHICS.md). If anything in this repository is ever
identified as a real assessment item, open an issue; it is treated as urgent
and replaced the same day.

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
- **No em dashes in files.** A comma, colon, or full stop instead.
- Comments explain why, not what.
