# Methodology

What this tool measures, what it does not, and why it reports things the way it
does.

## There is no score

Real assessment platforms report a score on their own scale. That scale
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

## What the time breakdown measures

`report` splits the clock between the questions. This is measured rather than
estimated, but it is measured indirectly, and the difference matters.

There is no watcher process and nothing observes the filesystem in the
background. Every command invocation reads the modification time of each
solution file and records any value it has not already recorded. Those are real
timestamps written by your editor, so no moment in the timeline is invented.
What is limited is **resolution**: the engine only learns about an edit the next
time you run a command. Someone who works for forty minutes in silence and then
submits gives it two observations to work from, and the breakdown will be
correspondingly coarse. Someone who checks the clock every few minutes gets a
fine-grained one. A sitting that produced no observations at all prints no
breakdown rather than a fabricated one.

Time is attributed **forwards**: touching a question means it holds the clock
from that moment until something else is touched. This is a modelling choice,
not a measurement, and the alternative is defensible enough to be worth naming.
Attributing backwards, so that a save claims the stretch ending at it, credits
the work leading up to each save. It was rejected because it gives the opening
minutes of genuine work on the first question to whichever question was saved
second, and leaves the first owning only the time before anything had been
written. Neither model can see a switch you made between two saves.

The stretch before the first edit is reported on its own as reading, because
nothing had been written yet and it cannot honestly be charged to any question.

Gated sessions do not use file times at all, because every level shares one
solution file. They partition on level boundaries instead, which are exact: a
level runs from the moment it unlocked to the moment the next one did. The cost
is the reverse limitation, that time spent going back to revise an earlier level
is charged to whichever level was open at the time.

A question that was never edited and never submitted is reported as never opened,
separately from one that was opened and produced nothing. They are different
results and the distinction is not inferred, it is the presence or absence of any
observation at all.

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

Every question **in the bank** has passed `tools/qa.py`, which CI runs on every
commit, at one of two levels. A **fully validated** question passes all three
checks below. A question marked `"validated": "basic"` passes only the first two,
which means nothing has proved its hidden suite can distinguish a wrong answer
from a right one, and it may therefore mark something correct that is not. The
tool reports which a question is.

The three checks:

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
- **The question bank is small, and one slot is smaller than the rest.** Twenty-two
  questions and four projects sounds like more sittings than it is. An exam takes
  one question per difficulty slot, and those slots hold 4, 5, 8 and 5 questions,
  so there are 800 distinct four-question papers but only **four sittings before
  the warm-up slot has to repeat**. Interview mode draws from slot 3 alone, which
  is eight. Recently served questions are tracked and avoided until the pool is
  exhausted, after which a remembered question measures memory rather than
  ability. Generated questions are the way past this, and they carry their own
  caveat above.
- **Hidden tests are readable in this repository.** They are hidden from the
  session, not from you. See [ETHICS.md](ETHICS.md).
- **Generated questions have not been through the gate at all.** A session
  started with `--generated` uses questions written on the spot rather than from
  the bank. They are checked to be answerable, meaning the reference solution
  passes the hidden suite and the untouched starter does not, but nothing has
  proved their hidden tests can distinguish a wrong answer from a right one, so
  such a question can mark something correct that is not. The session says so
  when it starts. Prefer the bank when the bank has something suitable.
- **What a company runs is researched, never remembered.** This tool ships no
  table of companies and keeps no cache. When one is named, the agent searches,
  reports what it found and how well sourced it is, and builds the sitting from
  that. The second session for a company searches again exactly like the first,
  because a hiring process rebuilt between cycles has no way of telling a saved
  note about it, and a stored answer gets quietly worse while sounding more
  authoritative each time it is read back. Your actual invite email is better
  evidence than any of it.
