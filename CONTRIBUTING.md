# Contributing

Contributions are welcome, particularly questions. There is one rule that is not
negotiable and a quality gate that runs automatically.

## The rule: original questions only

**Never contribute a real assessment question.** Not copied, not paraphrased, not
reconstructed from memory, not "the same idea with different variable names".
This applies to items from any assessment platform or company, whether you found
them on Reddit, in a leaked set, in a prep course, or by sitting the assessment
yourself.

If you have seen a real question and want to contribute something in the same
*shape*, that is fine: the format, the topic area, and the difficulty are
signals. The problem itself has to be yours.

If anything in this repository is identified as a real assessment item, it is
replaced the same day. Open an issue and it will be treated as urgent.

Contributions are also refused if they add any capability for interacting with a
live assessment, a proctoring system, or a browser session. See
[ETHICS.md](ETHICS.md).

## Adding a GCA question

One directory per question, under `skills/sim/questions/gca/<your-slug>/`:

```
meta.json          id, slot, difficulty, title, time_hint_minutes, topics
problem.md         the statement, with worked examples and constraints
starter.py         the signature and a docstring, raising NotImplementedError
tests_public.py    four or five samples the candidate can see
tests_hidden.py    the real suite, twenty or so tests
reference.py       a solution that passes tests_hidden.py
mutants/*.py       at least three plausible wrong answers
```

`meta.json` `id` must match the directory name. `slot` is the difficulty position
and drives selection:

| Slot | Difficulty | Typical shape |
| --- | --- | --- |
| 1 | warmup | strings, loops, a dictionary |
| 2 | medium | hash maps, sorting, binary search |
| 3 | medium | graphs, basic dynamic programming |
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

**Check three is the point of the whole exercise.** Your mutants are plausible
wrong answers: the off-by-one, the unsorted assumption, the missed edge case, the
approach that is correct but too slow. If a mutant survives, your hidden suite is
not discriminating and the fix is a better test, not a different mutant.

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

## Adding a company preset

`skills/sim/presets.json`. Every entry must carry:

- `sources`: at least one real URL
- `confidence`: how sure you are the company uses CodeSignal at all. `high` for
  first-party evidence or several independent recent reports, `medium` otherwise
- `last_confirmed`: `YYYY-MM-DD`
- `format`: `gca`, `ica`, or `null`

**`null` is the expected answer for most companies, and it is not a gap.**
CodeSignal publishes its customer list, so the platform is usually knowable; it
publishes nothing about which assessment each customer chooses. Seventeen of the
eighteen shipped presets say `null`, and the tool then asks the user which format
they want instead of guessing for them.

If and only if you state a format, you must also give:

- `format_confidence`: `high` or `medium`, kept separate from `confidence`
  because they are different claims and conflating them is how a guess becomes
  received wisdom
- `minutes`: the time limit

`questions` is optional. Adding `format_confidence` without a format is rejected.

`tools/qa.py` rejects entries missing any of these, and CI runs it. A preset is a
factual claim about what a company currently does to candidates and people plan
their preparation around it, so an unsourced one is a guess wearing a fact's
clothing. If you cannot source it, do not add it.

## Running the tests

```
python3 -m unittest discover -s tests
python3 tools/qa.py
```

## Style

- **Python 3.9 syntax, standard library only.** No `match`, no runtime `X | Y`
  annotations, no `tomllib`, no third-party imports anywhere, including tests.
  The floor is set by the machines people actually have: Apple Command Line Tools
  still ships 3.9.6 and some machines have no Python until it is installed.
- **No em dashes in files.** A comma, colon, or full stop instead.
- Comments explain why, not what.

## What to expect

This is a side project with a small time budget. Question PRs that pass the gate
are the easiest thing to review and will move fastest. Large refactors of the
engine are unlikely to be merged without discussion first, so open an issue.
