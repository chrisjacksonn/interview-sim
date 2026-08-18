# Question anatomy (maintainer notes)

How corpus questions are built and gated. Question PRs are not accepted
(see CONTRIBUTING.md); this documents the conventions for maintaining the
shipped set.

## Adding a GCA question

One directory per question, under `skills/sim/questions/gca/<your-slug>/`:

```
meta.json          id, slot, difficulty, title, time_hint_minutes, topics
problem.md         the statement, with worked examples and constraints
starter.py         the signature and a docstring, raising NotImplementedError
tests_public.py    a few samples the candidate can see
tests_hidden.py    the real suite, fifteen to twenty-five tests
reference.py       a solution that passes tests_hidden.py
mutants/*.py       at least three plausible wrong answers (two forms, below)
```

`meta.json` `id` must match the directory name. `slot` is the difficulty position
and drives selection:

| Slot | Difficulty | Typical shape |
| --- | --- | --- |
| 1 | warmup | strings, loops, a dictionary |
| 2 | medium | hash maps, sliding windows, sorting |
| 3 | medium | graphs, object design, simulation, basic DP |
| 4 | hard | advanced DP, graph algorithms, optimisation |

A session takes one question per slot, so slots need roughly even coverage. Check
what is thin before writing.

## Adding an ICA project

Under `skills/sim/questions/ica/<your-slug>/`, one evolving file across four
gated levels:

```
meta.json          id, levels, title, time_hint_minutes
starter.py         the class skeleton
reference.py       one solution satisfying ALL FOUR levels at once
mutants/*.py
level1/            problem.md, tests_public.py, tests_hidden.py
level2/  level3/  level4/
```

The shape that makes an ICA project work: level 1 is basic operations with corner
cases, level 2 is reporting over that data, level 3 adds a feature without
disturbing any existing call, by an optional argument or by new methods over the
same data, and **level 4 invalidates a design decision from level 1** while requiring everything before it to keep
working.

Level 4 is where the marks are. Weight its hidden suite toward re-checking the
earlier levels under the new model, because the usual way to fail is to get the
new feature working while quietly breaking the old behaviour.

## The gate

```
python3 tools/qa.py
```

CI runs this on every commit and a PR does not merge until it passes. It checks:

1. The reference solution passes the hidden suite. For ICA, every level.
2. The untouched starter does not.
3. Every file in `mutants/` fails at least one hidden test.
4. Any test promising the input came back untouched uses a fixture that sorting
   would disturb. This has been the same bug in four different questions: the
   test looks right, asserts the right thing, and passes for a solution that
   sorts the caller's list in place, because the fixture was already in order.

A mutant is either a full standalone solution, or a **patch**: a comment
naming the break plus two strings, `OLD` quoting a unique verbatim snippet of
`reference.py` and `NEW` the broken version. The gate composes patches against
the reference before grading, and one lives in `gca/bracket-check/mutants/` as
the working example.

**Check three is the point of the whole exercise.** Your mutants are plausible
wrong answers: the off-by-one, the unsorted assumption, the missed edge case, the
approach that is correct but too slow. If a mutant survives, your hidden suite is
not discriminating and the fix is a better test, not a different mutant.

### Two tiers

Writing mutants is the expensive part, so a question may ship without them:

```json
"validated": "basic"
```

A basic question still has to be answerable and non-trivial, because the
reference must pass and the untouched starter must fail. What it does not have
is any proof that its hidden suite can tell a wrong answer from a right one, so
it can mark something correct that is not. The gate says so, the README says so,
and `--json` reports it.

Full is the default and what every question in this bank is today. Prefer it.
Basic exists so the bank can grow faster than mutants can be written, and
upgrading later is just adding the `mutants/` directory.

Expect to fail this on the first attempt. Two of the questions in this repository
had suites that looked thorough and let a wrong answer through, and both were
caught here rather than by review.

If the gate rejects a mutant as *passing*, consider that it may not actually be
wrong. One "mutant" here turned out to be a correct if wasteful implementation.

And if the gate says your **reference** fails, check the test before the code.
Every time that has happened in this repository the expected value was wrong, not
the solution. Work out expected values with a throwaway brute-force
implementation rather than in your head:

```python
def brute(items):
    """Obviously correct, far too slow, only used to check the real answers."""
```

Hand-computed answers for anything with an off-by-one or a window in it are how
you end up asserting that a wrong solution is right.

