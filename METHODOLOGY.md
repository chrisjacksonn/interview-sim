# Methodology

What this tool measures, what it does not, and why it reports things the way it
does.

## There is no score

CodeSignal's General Coding Assessment reports on a 200 to 600 scale. That scale
is proprietary. The calibration behind it is not published, and no third party
has the data to reproduce it.

So this tool does not try. It reports what it actually observed: which questions
you solved, how many hidden tests passed, and how the time went. Producing a
number in the right range would be easy and would be a lie, and people would plan
around it.

If run-history data ever makes a defensible band possible, it will be labelled as
what it is: a comparison against your own previous sittings, not against a
candidate pool.

## What the timer measures

`start` computes an absolute deadline once and writes it to `state.json`. Every
later check is `deadline - now`. Nothing accumulates elapsed time.

This means quitting the process, closing your laptop, or running the command from
another directory cannot drift the clock, and the number you see is always the
real remaining time rather than a running total that could fall behind.

It also means the clock is wall-clock time. If you change your system clock, the
timer changes. There is no defence against that and there should not be: this is
practice equipment, not a proctor, and the only person affected is you.

When the deadline passes, the first command to notice it stamps the ending **at
the deadline**, not at the moment it noticed. So checking twice after the buzzer
gives the same answer twice, and a session you abandoned for an hour does not
report an hour of overtime.

## What grading measures

Each question ships a hidden test suite. `submit` runs your solution against it
in a throwaway directory, with a timeout, and reports how many tests passed.

**Partial credit is per test.** Passing 15 of 20 is 75 percent for that question.
There is no weighting: every test counts once. Weighting would need a defensible
basis for saying one edge case is worth more than another, and there isn't one.

**You are told counts, not names.** A failing test's name describes the case it
guards, so listing them would hand over the answer. Working out what you missed
is the exercise.

**Outcomes are distinguished**, because they mean different things:

| Outcome | Meaning |
| --- | --- |
| pass | every hidden test passed |
| partial | some passed, some did not |
| fail | none passed, but the tests did run |
| import error | the file does not parse or import, so nothing could run |
| timeout | the solution did not finish |
| crashed | the run stopped before a result could be read |
| missing | there is no solution file |

The last four mean the tests never ran, which is not the same as scoring zero on
them. They exit non-zero so the difference is visible.

A timeout is a real result, not a technical failure. A quadratic solution that
cannot finish on the largest input has not solved the problem, and a real
assessment would score it the same way.

## How the overall figure is computed

**GCA:** the average of the per-question credits. A question you never attempted,
or that timed out, counts as zero rather than being left out of the average.
Dropping it would report three quarters of a session as if it were all of it.

**ICA:** levels are graded cumulatively, so each level's score already contains
every level below it. The hidden-test counts shown are the deepest level reached
rather than the sum of the levels, which would count level 1 four times.

The overall percentage is the mean of the levels' credits, so a level never
reached is a zero and passing two of four is 50 percent. A level that timed out
or crashed is also a zero, whatever the levels below it scored.

## How questions are validated

Every question in the bank has passed `tools/qa.py`, which CI runs on every
commit. Three checks:

1. **The reference solution passes the hidden suite.** Otherwise the question is
   unanswerable.
2. **The untouched starter does not.** Otherwise the question asks for nothing.
3. **Every deliberately-wrong solution in the question's `mutants/` directory is
   caught by at least one hidden test.**

The third is the one that matters. A suite that passes everything discriminates
nothing, and grading against it is worse than not grading, because it tells you
that you got it right when you did not. Checking that wrong answers actually fail
is mutation testing pointed at the test suites themselves.

This is not theoretical. It has caught two suites in this repo that looked
thorough and were not: a shortest-path suite that a depth-first traversal passed
outright, and a performance test sized just small enough that a quadratic
solution squeaked under the timeout.

## Limitations worth stating

- **The questions are not real assessment items.** They are written to published
  format descriptions. The shape, timing, and difficulty ramp are imitated; the
  specific problems are not, and cannot be.
- **Difficulty calibration is a judgement call.** Slots are assigned by the
  author against the public difficulty descriptions. There is no candidate data
  behind them.
- **The bank is small.** Fifteen questions and three projects is three or four
  sittings of each format. Recently served questions are tracked and avoided, but
  once the bank is exhausted it starts over, and a remembered question measures
  memory rather than ability.
- **Hidden tests are readable in this repository.** They are hidden from the
  session, not from you. See [ETHICS.md](ETHICS.md).
- **Company presets are reported behaviour, not guarantees.** Every entry carries
  a source, a confidence tier, and the date it was last confirmed, and formats
  change every hiring cycle. Your actual invite email is better evidence than
  this table.
