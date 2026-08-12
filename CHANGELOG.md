# Changelog

## 0.5.1

The last of the audit findings.

**Interview mode always served a warm-up.** Selection takes `slots[:count]`,
which for one question is always slot 1, so the headline mode gave an
eight-minute question with forty-five minutes on the clock and drew from three
questions forever. It defaults to the slot-3 band now, degrading to the nearest
available slot rather than failing on a thinner bank.

**Forcing over an expired session recorded it as abandoned at the moment of the
force**, so `status` reported eleven hours elapsed on a seventy-minute session.
It ended when the clock ran out, and it now says so.

**Exit 1 with a raw traceback was reachable from three paths** and is not in the
documented exit-code contract: a state file holding valid JSON that is not a
session, a deleted working directory, and an unreadable project meta.json. One
corrupt session also took the whole `list` down. All three now raise the proper
error, and SKILL.md says a traceback means the tool is broken.

**Grading counted successes by subtraction.** unittest records one entry per
failed assertion rather than per test, so a `subTest` suite could produce a
negative score and a `setUpClass` error could score a whole class as passed
without running anything. Successes are counted directly now.

`run_grader` also waited on the grader with no bound, so a wedged child could
hang the session with the clock running.

## 0.5.0

The rest of the audit findings.

**Questions no longer repeat between sittings.** Selection drew independently
each time, which measured at 98.7% of three-sitting runs repeating a question
and the warm-up repeating back to back a third of the time. The tool now
remembers what it has served and prefers what it has not, so three consecutive
sittings use twelve distinct questions. `--seed` is unaffected and still
reproduces exactly, since history would otherwise make it depend on what the
machine had run.

**`--workspace` bypassed the one-session-at-a-time guard**, so naming a fresh
directory started a second clock alongside a live session and moved the pointer
to it. **`--minutes nan`** and friends crashed with a traceback after creating
the workspace; they are rejected now, along with values large enough to overflow
the platform time type.

`zone-hops` had no complexity pressure: its largest test was small enough that
an O(V*E) relaxation scored full marks. Added a 40k-edge test listed against the
traversal order, where the reference takes 0.011s and relaxation does not
finish, plus that solution as a mutant so the gate proves it bites.

Grading directories left behind by a hard kill are now swept.

Documentation corrections, all of them cases where the docs claimed something
the code did not do: METHODOLOGY listed four grading outcomes where there are
seven and described the ICA overall figure wrongly; CONTRIBUTING's preset rules
contradicted the validator after the schema change; ETHICS said "runs entirely
offline" without noting that the agent you run it through is not; six question
statements never mentioned that their suites forbid mutating the input; the
README transcript used a shell function it defined nowhere; and interview mode
appeared to be exempt from the after-time rule.

## 0.4.0

Fixes from a six-lens audit of the project. Four of these produced a wrong
result, which for a grading tool is the only category that really matters.

**A `print()` in a correct solution scored zero.** Results came back on the
child process's stdout, so anything the candidate printed landed in the middle
of the JSON and the whole run was reported as "0 of 0 hidden tests passed (0%)".
A stray debug print is the most likely thing to be left in a file under time
pressure. Results now come back through a file the candidate's code never sees.
The same change closed a leak: the old crashed-path echoed the child's last
output line, which after a partial write was the grader's own JSON, hidden test
names included.

**An ICA level that timed out was reported as a 100% pass** and unlocked the next
level. A level whose tests never ran reports 0 of 0, which cannot move
`passed == total`, so the earlier levels' counts declared a pass on their own.
Exit 8 was unreachable for every ICA session. Outcomes where nothing ran now
propagate instead of being averaged away, and such a level scores zero.

**`report` scored ICA levels from stale results**, so a level broken by level 4
still counted as passed: `submit` said regression and `report` said "reached and
passed 3 of 4 levels". Every re-graded level now writes its fresh figures back.

**Concurrent commands silently discarded graded results.** Two overlapping
submits both graded, both printed a real score, and the second clobbered the
first. Mutating commands now take an exclusive lock and re-read state inside it.

Also: a new exit code 9 for "nothing could be graded", distinct from 2; the
grader kills the whole process group so a leaked grandchild cannot outlive the
timeout; SKILL.md rule 3 now covers the entire question bank rather than only
`tests_hidden.py` (reference solutions, mutants and locked levels were one Read
away); rule 6 forbids passing `--now`, which defeated the late-submission
lockout; and SKILL.md's commands now work under all three install methods
instead of only the plugin loader.

Question fixes: file-store level 1's notes contradicted its own spec, and
shift-coverage stated a bound of 100k while grading at 200k.

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
