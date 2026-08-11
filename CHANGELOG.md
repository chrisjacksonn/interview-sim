# Changelog

## 0.3.0

**Company presets, eighteen of them.** Each records two separate claims: that the
company uses CodeSignal, and which assessment they give. CodeSignal publishes its
customer list so the first is usually first-party; it publishes nothing about
format, so most entries record the format as unknown and ask you to choose rather
than repeating a claim that only content farms make.

**Three more GCA questions**, fifteen in total: Log Window, Room Schedule, and
Token Budget.

**`references/formats.md`** records the difficulty ramp, target times, ICA level
shapes, and the calibration rules the questions are written against, along with
what is deliberately not modelled.

Launch post drafts in `docs/`.

## 0.2.0

**Interview mode.** One question, forty-five minutes, and an interviewer rather
than a proctor. Hints are allowed here and every one is recorded with its
wording, because a real interviewer gives them and a debrief that hides them is
flattering and useless. `report` prints the count. `hint` is refused in exam
mode.

**Session history.** `list` shows past sessions newest first, and `--session
<id>` reaches any of them. Before this the only reachable session was whatever
the pointer file named, so yesterday's sitting was on disk but effectively lost.

**Difficulty selection.** `--slot N` draws from one difficulty, which is what an
interview is: a single question at a chosen level rather than a ramp.

`--version` added.

Fixed: a session abandoned long after its deadline reported more time used than
it ever had, because the ending of an abandoned session is the moment it was
abandoned. Time used is now clamped to the time available.

## 0.1.0

First working version.

**Two exam formats.** GCA-style is four questions in seventy minutes, all
unlocked at once, one drawn from each difficulty slot. ICA-style is one project
across four levels in ninety minutes, where each level unlocks by passing the one
before it and every submission re-runs the levels below, so adding level 4 by
breaking level 1 reads as a regression rather than as progress.

**Deterministic timing.** The deadline is computed once and written down; every
later check is that deadline minus now, so quitting, sleeping, or moving
directories cannot drift the clock. The ending is stamped at the deadline rather
than at the moment it was noticed, so checking twice after the buzzer gives the
same answer twice. Submissions after time are refused even when correct.

**Hidden-test grading with partial credit**, reporting counts only. Test names
and assertion messages never reach the candidate, because a failing test's name
describes the case it guards.

**No score.** The 200-600 scale is proprietary and cannot be reproduced honestly,
so `report` gives per-question results and a qualitative band instead. A question
that timed out or was never attempted counts as zero rather than being dropped
from the average.

**Twelve GCA questions and three ICA projects**, all original, all validated by
`tools/qa.py` in CI: the reference passes the hidden suite, the untouched starter
does not, and every deliberately-wrong solution in `mutants/` is caught by at
least one hidden test.

**Company presets** are wired up with an empty table. Every entry needs a real
source, a confidence tier, and a confirmation date, and the validator refuses
anything without them.

Python 3.9, standard library only, no dependencies.
