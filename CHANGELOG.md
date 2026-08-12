# Changelog

## 0.7.0

**A company's process, not just one assessment.** An assessment followed by a
live round is two sittings with two shapes, and a preset could only hold one.
Calling `learn` again with a different `--round` now adds a round rather than
replacing what was there, because a process is learned in pieces: the assessment
turns up in one thread and the pairing round in another.

`start --preset shopify` refuses when several are recorded and lists them.
Choosing which round somebody should sit is the same guess as choosing a format,
and this tool does not make that one either. `--round oa` and `--round pairing`
each run their own shape, and a round recorded as live runs as an interview.

**Topics, which is the part of someone else's assessment that transfers.**
Research comes back with what candidates report being asked about, `learn
--topic` records it, and sessions for that company draw on those subjects. Spread
across them rather than stacked on whichever the bank has most of, since four
sliding-window questions should not crowd out the one graph question when both
were asked for. `--topic` works without a preset too.

The start output says which topics it covered and which it could not:

```
Topics asked for:
  graphs                   Build Order
  sliding window           Rolling Median
  rate limiting            nothing in the bank covers this
```

A topic in the bank but not drawn says so instead, because claiming the bank
cannot cover something it can would send the agent writing a question that
already exists. Topic is a preference and never a filter: a subject nothing
matches still yields a full session rather than a short one.

**Paste a posting for a company nobody has heard of, and it can go and find
out.** The skill could already read a posting and take the company name to the
preset table. The table has nineteen rows, so for most postings that ended in a
shrug and a question.

The agent may now search for what a company's current screen is, and `learn`
writes down what it found:

```
session.py learn stripe --round oa --confidence medium --format gca \
    --questions 2 --minutes 60 \
    --source https://... --source https://...
```

It lands in `presets.local.json` beside your sessions, never in the repository.
The same discipline the shipped table is held to applies: no source, no entry.
It refuses to overwrite a reviewed row, and every session started from one
reprints where it came from, with the links and the date, before the clock
starts. A reviewed entry always wins over a researched one.

A company reported to run a **live** round instead of an asynchronous assessment
is recorded with `--mode interview`, and starting from that preset now runs the
closest thing this tool has to that round rather than a silent seventy-minute
exam. Presets can drive the shape of a session, not only its length.

The engine still opens no network connection. The searching is the agent's, the
grading is local, and research never returns a company's actual questions:
question text found while looking is a signal about format and topic, and
nothing else. ETHICS.md now says all of this explicitly rather than implying the
whole tool is offline.

**`check`, a preflight.** Python version and path, how many questions the bank
holds, whether the sessions directory is writable, and which editor `--open`
will reach for. Everything it looks at is knowable before a session exists, and
every one of those failures was otherwise found halfway through a `start`, which
is the worst moment to find it: the workspace is half built and the user is
deciding whether the tool is broken or they are. It exits 7 on a real problem,
and the skill now runs it whenever anything else exits 7.

**Windows no longer crashes the grader outright.** The timeout killed a whole
process group, which is POSIX only, so the run refused to start there at all.
It asks for a process group where there is one and kills the direct child where
there is not. Still untested on Windows, and the README says so rather than
implying support.

**`progress`, what your sessions add up to.** One sitting is a data point and
several are a shape. It prints the sittings in order, then hidden tests passed
by difficulty band, then the count of questions never submitted at all, which is
the number a pass rate hides: running out of time is a result too.

It stops deliberately short of a single improvement figure. Questions differ in
difficulty and the draw is random, so across a bank this size a rising percentage
is as likely to mean an easier session as a better one, and a trend line drawn
through that would be the same kind of invented number as a score estimate.

**A fourth ICA project, Payment Intents.** Idempotent intent creation, per
merchant reporting, refunds with a ceiling, and then a level 4 that replaces the
model the first three levels let you get away with: status stops being whatever
the last call set and becomes the product of processor callbacks that arrive at
least once, so duplicates and a late decline have to leave a capture alone.

**`start --open`** opens the workspace in your editor once it is ready, so the
session lands where the work happens rather than in a path you have to copy.

**Anthropic added to the preset table.** Nineteen companies now.

**Prose is wrapped to the terminal.** Preset notes run to two or three sentences
and a terminal was breaking them mid-word. Wrapped at 88 columns, or narrower if
the terminal is. Paths, tables, and scores are still printed as-is, because
those are read down a column and wrapping one would be worse.

**The demo tape pins its question.** Selection is random and one warm-up question
ships no mutants, so a quarter of recordings had nothing to stage as a
nearly-correct solution and the run died on camera.

## 0.6.0

**Questions can be written for a role rather than taken from the bank.**
`start --generated <dir>` runs a session on questions the agent wrote, for a
company or a posting the bank has nothing close to. They are original problems,
never real assessment items.

They skip the mutation gate, which is the deliberate trade: nothing has proved
their hidden tests can tell a wrong answer from a right one, so their grading is
less trustworthy and the session says so when it starts.

They do not skip the two checks that decide whether an hour is worth spending,
and those run **before the clock starts**, which is the only moment they are
free. The reference solution must pass its own hidden suite, or the question is
unanswerable. The untouched starter must fail it, or the question asks for
nothing. Either failure refuses the session with a message saying which.

**An unknown company is no longer a dead end.** `start --preset stripe --format
gca` runs, records the company, and says out loud that it ran that format
because it was asked to rather than because anything was researched.

**`presets`** lists the table or looks one company up, so the agent can answer
"do you know this company" without parsing JSON.

ETHICS.md and METHODOLOGY.md updated to match: both previously said every
question had been through the gate, which is no longer true of generated ones.

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
