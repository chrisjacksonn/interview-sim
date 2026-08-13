# Changelog

## 0.14.0

**The report now says where the time went.**

The claim this tool makes is that four questions in seventy minutes is a
different problem from four questions. Nothing in it measured that. Every figure
it printed was about whether the code was right, which is the part any untimed
judge already tells you. Almost nobody fails a screen because they cannot do
binary search. They fail because two thirds of the clock went on question two
and question four was never opened, and the tool watched that happen and said
nothing about it.

```
Where the time went

  q1 28/28              9:00   2 submits
  q2 19/25             46:40   7 submits   67% of the clock
  q3 not submitted      8:20   0 submits
  q4 not opened

  6:00 before the first edit, reading.
```

The timings are measured, not estimated. There is no watcher process, so the
engine only sees the filesystem when a command runs: every invocation samples
the modification time on each solution file and records any value it has not
seen before. That gives real timestamps and never invented ones, at whatever
resolution the candidate happened to check the clock at. A sitting where nothing
was ever observed prints no timeline at all rather than a guessed one.

Time is attributed forwards: touching a question means it holds the clock until
something else is touched. Attributing backwards instead, giving a question the
stretch that ends at its first save, reads just as plausibly and is wrong. It
hands the opening minutes of real work on question one to whatever got saved
next, and leaves question one owning only the time before anyone had written
anything.

Gated sessions cannot use file times, because all four levels share one solution
file. They partition on the level boundaries instead, which are exact: a level
runs from the moment it unlocked to the moment the next one did.

A question never opened is reported separately from one that was opened and got
nowhere. They are different mistakes and they have different fixes.

Also fixed on the way past: `session.py` carried three functions defined twice.
`age_phrase` and `record_research` were identical copies, but the live
`command_learn` was the stale one, still describing a shipped table of companies
that was deleted two versions ago, while the refactored version that shares
`record_research` with `start --source` sat shadowed and unreachable. 211 lines
removed.

## 0.13.0

**Every question in the bank now passes the mutation gate, and closing that gap
found two questions grading people wrongly.**

Four questions had been merged with `"validated": "basic"`, the marker for a
question whose hidden suite has never been shown to catch a wrong answer. There
was one of them in every difficulty slot, which is the worst possible place for
them to be: a four-question exam draws one from each slot, so 58% of sittings
included a question that could mark a wrong solution correct.

Writing the missing wrong-solutions turned up real holes in two suites that were
already considered finished.

Rolling Median could not detect the standard way of getting a sliding window
wrong: keeping the window sorted and then popping its front, which discards the
smallest value instead of the reading that actually left. Twenty tests, none of
which caught it, because in every case the departing reading was also the
smallest one in the window. `solve([9, 0, 9], 2)` tells them apart.

Repeat Alerts could not detect a solution that compared timestamps in arrival
order instead of sorting them first. A pair arriving out of order produces a
negative gap, and a negative gap is inside any window, so the wrong answer came
out right. It needed a case that is out of order and genuinely not noisy.

Two "the input must not be modified" tests were checking with fixtures that were
already sorted, so sorting the caller's list in place passed as leaving it
untouched.

**Two session files were being shipped in the repository.** `current` and
`history.json` were committed by accident when session workspaces moved into the
working directory. `current` held an absolute path from one machine. The more
damaging one was `history.json`, which told every fresh clone that four
questions had already been served, so a new user's first sitting quietly drew
around them. The whole session directory is ignored now.

Also: dropped the preset validation branch `tools/qa.py` had kept as dead code
since the company table was removed.

## 0.12.0

**It stopped introducing itself as somebody else's product.** The tagline, the
repository description, the plugin description and the first lines of the README
all led with being a simulation of one vendor's two formats. That was accurate
when the tool shipped nineteen of that vendor's customers in a table and could
run nothing else. It is not accurate now: the company table is gone, sessions
are built from whatever a company is actually researched to run, and three of
the questions added this week are pairing-round shaped rather than assessment
shaped.

So it leads with what it does. The three shapes are named for what they are, an
exam, a project and an interview, with a line noting which two your invite email
might call something else. The score note no longer names a platform to say it
is not reproducing that platform's scale, since the point holds for all of them.

Trademarked names are gone from the branding entirely. They survive in two
places on purpose: the words a candidate actually types, so the skill still fires
when somebody says they have a GCA next week, and citations in the internal
format reference, which is where naming a source is the honest thing to do.

## 0.11.0

**Recording and running are one command.** `start --source https://...` writes
down what the session ran and where that came from, so the note is a byproduct
of sitting the thing rather than a second command typed with the same
information. It cannot then describe a sitting nobody had. `learn` survives for
research nobody acted on: a round they are not sitting today, or a company they
were only asking about.

**Two more questions shaped like a live round.** `request-budget` was the only
one, so a second interview-mode session handed you the same problem.

`checkout-rules` is a till: unit prices, multibuy deals, and a basket, where the
leftover after the deals is where a working-looking answer goes wrong and a
price change has to reach items already scanned. `floor-robot` is a warehouse
robot on a blocked grid, taking a command string, counting what it could not
do, where a refused move stops that command and not the rest of the string.

Sixteen mutants between them, all caught, and the checkout totals were
cross-checked against a deliberately slow second implementation over eighteen
thousand random operations rather than worked out by hand. Slot 3 now holds
eight questions, three of which are build-a-class, which is what topic steering
draws on when research reports a pairing round.

## 0.10.0

**The company table is gone, and nothing replaces it.** `presets.json`, its
nineteen rows, the confidence tiers, the reviewed-versus-researched distinction,
the staleness thresholds: all removed. Every one of those existed to manage a
file that was out of date the moment a hiring cycle turned over, and a search
answers the same question better and more currently.

So a company is researched every time it is named. The engine has no idea who
any company is: `--company` and `--round` are labels for the record, and the
shape of the sitting arrives as `--format`, `--mode`, `--questions`, `--minutes`
and `--topic` from whoever just looked it up. **Naming a company without a format
is refused rather than guessed at**, because naming a company is a claim about
what they run.

`learn` still writes down what was found, with its sources and the date, and
`recall` reads it back saying plainly that it is not current. That is a log for
comparing this month's answer with last month's, and it is never consulted in
place of searching. `presets` is gone; `recall` replaces it.

This deletes more code than it adds, which is the correct direction for a
feature that was propping up a bad idea.

## 0.9.6

**New demo.** The old one showed output the tool no longer produces and paths in
a home directory it no longer uses. This one records from a project directory,
because that is where sessions are built now and seeing them land next to your
own work is half the point.

**The line that starts the clock stopped wrapping mid-word.** It repeated the
full workspace path, which is already two lines above it, and the result was
long enough to break across two lines in an ordinary terminal.

## 0.9.5

**The permanent version of "turn on auto mode".** `permissions.defaultMode` in a
`.claude/settings.json` makes sessions in that directory start in auto mode, so
a practice folder can be prompt-free without changing anything else on the
machine. Documented in the README, and the skill offers it if asked rather than
writing it for anyone.

Nothing a skill emits can change the permission mode: only shift+tab, or the
flag the session was launched with. That is by design, and Claude Code even
ships a `disableAutoMode` setting so an administrator can forbid it, so the
skill says the sentence and never pretends to hold the switch.

## 0.9.4

**One line about permission prompts, at the start, once.** A timed sitting stops
being timed if it pauses to ask permission every time the proctor reads your
file or runs the grader. The skill now says so before the clock starts and then
drops it.

It says it rather than asking it, because it cannot turn auto mode on and a yes
it cannot honour is worse than a sentence someone can act on. The README also
documents the narrower option, an allow rule for this one script, which is a
smaller thing to hand over than auto mode for everything.

## 0.9.3

**What you learn about a company follows you between projects.** Local research
was written next to the sessions, and the sessions moved into the working
directory, so researching Shopify from one repository left it forgotten from the
next one. Sessions belong to the project they were sat in; what a company asks
does not.

It lives in `~/.interview-sim/presets.local.json` now, and both older locations
are still read, so nothing already researched is lost.

## 0.9.2

**A cached company goes stale.** `last_confirmed` was written down and then
nothing ever read it, so research done while applying in one autumn would be
served silently during the next hiring cycle, after the company had rebuilt its
process. The date was there and meant nothing.

Anything older than six months is now flagged as stale in `start --json` and
said out loud by `presets`, and the proctor is told to search again and re-record
rather than serve it. A missing date counts as stale, because not knowing when
something was true is not the same as it being true now. The reviewed table is
dated the same way and gets the same treatment: nothing here is exempt.

Calling `learn` again for a round overwrites it and restamps the date, keeping
the sources from both passes.

## 0.9.1

**`--open` launched Finder on a machine with VS Code open in front of it.**
`shutil.which("code")` finds nothing unless somebody has run VS Code's optional
"install 'code' command in PATH" step, which most people never do. The next
candidate in the list was the platform file manager, so starting a session threw
the candidate out of their editor and into a directory listing at the moment
their clock started.

It now looks in the application bundles too, where the CLI actually lives, for
VS Code, VS Code Insiders, Cursor, Sublime and Zed, in `/Applications` and
`~/Applications`. And a file manager is no longer treated as a fallback for an
editor: it only runs when there is no editor at all, never in place of one that
was merely absent from PATH. `check` reports the editor it found, with its path.

## 0.9.0

**A question shaped like a live round.** Every candidate report of a pairing
round describes building something to a given API: a rate limiter, an inventory,
a small store. The bank had twenty of those and none of this, so research would
turn up "they ask you to build a class" and the session would serve a graph
traversal, which is a worse mismatch for going unmentioned than for being
announced.

`request-budget` is the first of the other kind. You are given a class API and
build it: a sliding-window rate limiter, half-open boundary, where a refused
request must leave no trace or a brief burst turns into a permanent ban. Eight
mutants, thirty-two hidden tests, and its expectations were cross-checked
against a second naive implementation over eighty thousand random calls rather
than worked out by hand.

**`--open` no longer throws you out of your editor.** It opened a second window
rooted at the session directory, so starting a session meant losing the window
you were working in and landing in a file tree. It reuses the window you already
have and navigates to your solution file, which is inside the project you have
open anyway now that sessions live in the working directory.

**The proctor stops talking about the preset table too.** "Shopify is not in the
table, so I will look it up" describes a filing system nobody asked about. It
says what it is doing and does it.

## 0.8.1

**`--open` puts you in the file, not in a file tree.** It opened the workspace
folder, which meant starting a timed assessment by looking at a directory
listing and going to find the file yourself, clock already running. It now opens
the workspace and focuses the first `solution.py`. SKILL.md tells the proctor to
pass it every time there is a person at the keyboard.

## 0.8.0

**Sessions land where you are working.** The workspace used to be built under
`~/interview-sim-sessions` regardless of where you invoked it, so the tool
announced a path somewhere else and expected you to go and find it. That home
directory was chosen to keep session files out of *this* repository, and it got
over-applied to every project anyone might be standing in.

It now builds `./interview-sim-sessions/<id>` in the working directory, and each
session writes a `.gitignore` containing `*`, so a sitting inside a repository
ignores itself and cannot be committed by accident. `list` and `progress` read
the old home directory as well, so nothing already sat disappears.

**The start of a session stopped explaining itself.** It used to print where a
format came from, how confident anyone was in it, whether the questions were
generated, and which requested topics the bank could not match. All of that is
true and none of it is something a candidate can act on with forty-five minutes
to spend. "The bank had nothing on rate limiting so it drew a scheduling problem
instead" is a sentence that costs someone their confidence in the hour they are
about to sit.

`start` now names the company, the round and the shape, and stops. Everything
removed moved to `start --json`, under `briefing`, where the proctor reads it,
and to `presets`, where the evidence belongs. The agent is told to say the
sourcing once, in its own words, before the session, and never to mention the
bank at all. An uncovered topic is its cue to write a question for that subject
before starting, not to run a mismatched one and apologise.

**Forcing over a session that has already ended no longer needs confirming.**
Its results are already banked and nothing is at stake. The confirmation is
reserved for a session that is genuinely still running.

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
