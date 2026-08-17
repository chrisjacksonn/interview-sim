# interview-sim

Practice the screen a company actually runs, on a real clock, in your own editor.

Paste a job posting and it finds out what that company's technical screen is,
then sits you down in front of one: real files, hidden tests, and a deadline that
does not negotiate.

## Status

The engine is complete. Three shapes of sitting, and the parameters are yours to
set, because companies do not all run the same thing.

- **The exam**: four questions, seventy minutes, all unlocked at once, silent
  proctor. The shape of a standard online assessment
- **The project**: one project, four levels, ninety minutes, levels gated by
  hidden tests, with every level re-running the ones below it. Level 4 exists to
  invalidate a decision you made at level 1
- **The interview**: one question, forty-five minutes, with an interviewer who
  asks about your approach first and whose hints are counted. The shape of a live
  pairing round

If your invite email uses the platform's own names for the first two, they are
`--format gca` and `--format ica`.
- `start`, `status`, `submit`, `hint`, `unlock`, `report`, `debrief`, `watch`, and `list`
- hidden-test grading with partial credit
- deterministic timing, and submissions refused once the clock runs out
- a per-question time breakdown, so a sitting lost to bad triage says so

The bank is **twenty-two questions and four projects**, four or five in
every difficulty slot. A session takes one question per slot, and it remembers
what it has already served you, so consecutive sittings do not repeat a question
until the bank runs out.

There is no table of companies and nothing is cached. Paste a job posting and the
agent running the skill goes and finds out what that company currently runs,
every time, rather than reading you something that was true last season. The
second session for a company searches again exactly like the first.

## What it looks like

![A GCA session: naming a company starts the clock, real files appear, submitting reports how many hidden tests passed, and three questions are still waiting](demo.gif)

`sim` is the shell function the tool writes into every session workspace:

```
sim() { python3 ~/interview-sim/skills/sim/scripts/session.py "$@"; }
```

<details>
<summary>The same thing as text</summary>

```console
checkout-service $ sim start --company capital-one --format gca
Session started: capital-one-gca/20260812T013654Z

capital-one. GCA-style exam.

4 question(s), 1:10:00 on the clock.
Deadline 2026-08-12T02:46:54Z UTC.

Work here:
  ./interview-sim-sessions/capital-one-gca/20260812T013654Z
    q1/problem.md   Bracket Check
    q2/problem.md   Build Order
    q3/problem.md   Merge Feeds
    q4/problem.md   Route Fuel

Read a problem.md first, then write your answer in the solution.py beside it.
The clock is running.

$ ls ./interview-sim-sessions/capital-one-gca/20260812T013654Z/q1
problem.md   solution.py   tests_public.py

$ sim submit --question q1
q1  27 of 28 hidden tests passed (96%).

attempt 1, 1:09:36 left on the clock.

$ sim status
1:09:24 remaining

session   capital-one-gca/20260812T013654Z  (gca, exam mode)
elapsed   0:35
deadline  2026-08-12T02:46:54Z UTC
workspace ./interview-sim-sessions/capital-one-gca/20260812T013654Z

  q1   27/28          Bracket Check
  q2   not submitted  Build Order
  q3   not submitted  Merge Feeds
  q4   not submitted  Route Fuel
```

</details>

Which failed is not shown, and working that out is the exercise.

## Why it exists

The format is the part that surprises people. Four questions and seventy minutes
is a different problem from four questions, and you cannot practise the
difference on a site that lets you take as long as you like. This runs the clock
honestly, in real files, in your own editor, against tests you cannot see.

## Install

Claude Code, as a plugin:

```
/plugin marketplace add chrisjacksonn/interview-sim
/plugin install interview-sim@interview-sim
```

The skill is then `/interview-sim:sim`, and plain `/sim` also works when no other
command has claimed that name. You do not have to remember either: asking for
what you want in plain words ("run a GCA mock", "give me an OA practice session")
fires it too.

Any agent that reads the Agent Skills convention:

```
npx skills add chrisjacksonn/interview-sim
```

By hand:

```
git clone https://github.com/chrisjacksonn/interview-sim
cp -r interview-sim/skills/sim ~/.claude/skills/
```

Claude Code is where this is developed and tested. Codex, Cursor, and anything
else that reads the Agent Skills convention should load it and run the same
scripts, since the engine is plain Python with no dependencies, but I have not
sat a full session in one, so treat that as untested rather than supported.
Slash commands and Claude-specific frontmatter do not apply there either. If you
try it somewhere else, an issue saying whether it worked is genuinely useful.

## Requirements

Python 3. That is the whole list: no pip install, no virtualenv, no
dependencies. The engine is standard library only and runs on 3.9, which is what
Apple's Command Line Tools still ship, so it works on a stock Mac.

To find out before you start a session rather than during one:

```
python3 skills/sim/scripts/session.py check
```

```
ok    python    3.9.6 at /usr/bin/python3
ok    bank      26 questions under .../skills/sim/questions
ok    sessions  ./interview-sim-sessions
ok    editor    /Applications/Visual Studio Code.app/..., so --open will open the problem in it
```

If `python3` is missing, run `xcode-select --install` on macOS or install it from
python.org.

Developed on macOS, and Linux works the same way. Windows is not something I have
run it on: the timeout in the grader kills a whole process group there, which is
POSIX only, so it falls back to killing the direct child. Everything else is
plain Python. If you try it, `check` first, and an issue either way is useful.

### Running without interruptions

A timed sitting stops being timed if it pauses to ask permission every time the
proctor checks your file or runs the grader.

The tidiest fix is a `.claude/settings.json` in whichever directory you practise
in, so sessions there start in auto mode and nowhere else changes:

```json
{
  "permissions": {
    "defaultMode": "auto"
  }
}
```

Project settings beat user settings, so this is scoped to that folder. If you
would rather keep confirmations on and only exempt this tool, allow its commands
instead:

```json
{
  "permissions": {
    "allow": ["Bash(python3:*)"]
  }
}
```

Or press shift+tab at the start of a session and change nothing on disk.

The skill mentions this once in its first reply, before it starts searching, and
then leaves it alone. It cannot turn any of it on itself, and that is deliberate
rather than an oversight: a plugin able to switch off its own permission prompts
would make those prompts worthless. There is even a `disableAutoMode` setting so an
administrator can forbid auto mode outright.

## Using it

Ask for a session in whatever words you like ("start a GCA mock", "give me an OA
practice run"), or run the engine directly:

```
python3 skills/sim/scripts/session.py start --format gca
python3 skills/sim/scripts/session.py status
python3 skills/sim/scripts/session.py submit --question q1
python3 skills/sim/scripts/session.py report
```

Add `--open` to any `start` and it navigates the editor you are already in to the
first problem statement, as soon as it is ready. It opens the problem rather than
the empty starter on purpose: the format punishes typing before reading.

`start` builds a workspace under `./interview-sim-sessions/` in whatever
directory you ran it from, so the files land beside the work rather than in a
corner of your home directory. Each session writes a `.gitignore` that ignores
itself, so a sitting inside a repository cannot be committed by accident. A
real directory per question:

```
q1/problem.md        the question
q1/solution.py       yours to write
q1/tests_public.py   samples, not the grade
```

Open it in your editor and work normally. `status` tells you how much time is
left. `submit` runs your solution against the hidden suite and tells you how many
of its tests passed, and nothing else: which ones failed is the part you are
meant to work out. Resubmit as often as you like, it only costs time.

### A clock on screen

Split your terminal and run `watch` in the other pane:

```
python3 skills/sim/scripts/session.py watch
```

```
  ┌─────────────────┐
  │      38:14      │
  └─────────────────┘
  capital-one-gca/20260815T091200Z

  q1         28/28
  q2         19/25
  q3         not submitted
  q4         not submitted
```

It redraws once a second, turns amber at ten minutes and red at two, and rings
the bell at thirty, ten and two along with a desktop notification. It also
writes the remaining time into the terminal's tab title, which is the surface
that survives the pane being hidden and needs no permission from anything.

A real assessment puts a countdown where you cannot avoid it, and coding with a
clock in your peripheral vision is a different skill from coding. Expect to do
slightly worse with it at first. That is the point.

The pane owns nothing. It re-reads `state.json` and draws `deadline - now`, so
it decides nothing and grades nothing, and late work is still refused by the
script alone. Leaving it running also improves the time breakdown below, because
a pane that is awake every second is a far better observer of your edits than a
command you happen to run twice an hour.

Once the deadline passes the session is over, and a submission after that is
refused even if it is correct. `report` then summarises the sitting, including
where the time actually went:

```console
$ sim report
capital-one-gca/20260812T013654Z  GCA
Finished (time). Used 1:10:00 of 1:10:00.

  q1   28/28         warmup     Bracket Check
  q2   19/25         medium     Build Order
  q3   not attempted medium     Merge Feeds
  q4   not attempted hard       Route Fuel

Where the time went

  q1 28/28              9:00   2 submits
  q2 19/25             46:40   7 submits   67% of the clock
  q3 not submitted      8:20   0 submits
  q4 not opened

  6:00 before the first edit, reading.
```

That last block is the one worth reading. Almost nobody fails a screen because
they cannot do binary search; they fail because two thirds of the clock went on
one question and the last one was never opened. The timings come from the
modification times on your own files, sampled whenever you run a command, so
they are measured rather than estimated. Nothing watches you in the background,
which means the resolution is however often you checked the clock.

### ICA runs work differently

```
python3 skills/sim/scripts/session.py start --format ica
```

You get one project and one `solution.py`. Only level 1's statement is on disk;
the next level appears when the current one passes. You cannot read ahead, which
is deliberate, because level 4 exists to invalidate a design decision you made at
level 1.

Every submission re-runs all the levels below the one you are on. Adding level 4
by breaking level 1 shows up as a regression rather than as a pass.

### Interview mode

```
python3 skills/sim/scripts/session.py start --mode interview
```

One question, forty-five minutes, and someone in the room with you. They ask how
you plan to approach it before you write anything, keep an eye on the clock out
loud, and follow up on complexity and edge cases when you finish.

The question comes from the slot-3 band by default, which is what a
forty-five minute technical screen actually looks like. `--slot 4` if you want
the hard one, `--slot 1` for a gentle start.

Hints are allowed here, unlike in exam mode, and every one is recorded. Solving
it with two nudges is a different result from solving it alone, and the debrief
says which happened rather than quietly rounding up.

The clock and the grading are the same scripts underneath. Only the person
changes.

### Coming back to an old session

```
python3 skills/sim/scripts/session.py list
python3 skills/sim/scripts/session.py report --session capital-one-gca/20260811T193740Z
```

Sessions are kept, so you can look at what you did last week.

### What it adds up to

```
python3 skills/sim/scripts/session.py progress
```

```
3 sessions since 2026-07-28. 2 GCA, 1 ICA.

  2026-08-12  gca   2/4 solved  38/48 tests    1:04:22 of 1:10:00
  2026-08-05  gca   1/4 solved  21/44 tests    1:10:00 of 1:10:00
  2026-07-28  ica   0/4 solved  12/20 tests    1:30:00 of 1:30:00

Hidden tests passed, by difficulty:
  warmup      92%   (24 of 26, across 3 questions)
  medium      61%   (28 of 46, across 4 questions)
  hard        18%   (7 of 40, across 2 questions)

Never submitted: 5 of 16 questions. Running out of time is a result too, and it
is the one a pass rate hides.
```

The difficulty rows are the ones worth reading, and so is the count of questions
you never reached. There is deliberately no single improvement number: questions
differ in difficulty and the draw is random, so across a bank this size a rising
percentage can just mean an easier session.

### Paste a job posting

```
/interview-sim:sim https://jobs.example.com/shopify-swe-intern
```

The agent fetches that page, works out the company and the role, and searches for
what their screen currently is: candidate reports with dates on them, not the
company's own careers page and not the prep sites that rank for "interview
questions". It tells you what it found and how well sourced it is, then builds
the sitting out of it:

```
sim start --company shopify --round pairing \
    --format gca --mode interview --minutes 45 \
    --topic "rate limiting" --topic "object oriented design" --open
```

Nothing is looked up by the engine. It does not know who any company is, and
naming one without a format is refused rather than guessed at, because naming a
company is a claim about what they run.

**Nothing is remembered, either.** There is no log and no cache, so the second
session for a company searches again exactly like the first. That is not an
oversight. A hiring process gets rebuilt between cycles and has no way of
telling a saved note about it, so a stored answer would quietly get worse while
looking more authoritative every time it was read back.

What research will never come back with is the company's actual questions. What
it does come back with is the **topics and the round style**, which is the part
that transfers, and that is what the question is then written from. A researched
sitting runs on an original question authored for it, not on something drawn
from a fixed pool:

```
python3 skills/sim/scripts/session.py start --format gca --questions 1 \
    --generated /tmp/ramp-screen --company ramp --topic "formula parsing"
```

Written questions are original problems, never real assessment items, and they
pass **the same gate the shipped corpus passes in CI, before the clock starts**:
the reference solution must pass its own hidden suite, the untouched starter
must fail it, and every deliberately-wrong solution written alongside must be
caught by at least one hidden test. A question whose suite lets a wrong answer
survive is refused, and the refusal happens while rewriting is still free.

Every sitting also states its topic match (`on`, `partial` or `off`) on screen
and in the report, so a question that is not on the subject you asked for says
so before you spend an hour on it.

The pre-written questions still ship, for two jobs: they are what CI proves the
gate works on, and they are the instant path when no company is involved and
you just want reps. `--topic graphs` draws from them for drilling something
specific.

## What leaves your machine

Nothing, from the engine. It opens no network connection and the scripts import
nothing that could; the clock and the grading are entirely local.

If you run it through an AI coding agent, which is the usual way, that agent is
not local: the problem text and whatever you show it of your code go to that
provider, exactly as they would if you pasted them in yourself.

The engine itself runs with no agent at all: `start --format gca` on the shipped
questions, the clock, grading, `watch`, `report` and `debrief` are all plain
scripts. What needs an agent is the researched sitting, because researching a
company and writing an original question for it are the agent's work, not the
engine's.

## Prepping one company repeatedly

The agent researches a company fresh every session, deliberately: the tool
keeps no notes, because stored answers about hiring processes go stale
invisibly. Your own knowledge is different. If you already know the round, say
so and the search is skipped: paste the invite or recruiter email, or put what
you know in the practice directory's `CLAUDE.md`:

```markdown
Prepping Ramp, Software Engineer (Frontend).
Their screen: live pairing, ~50 minutes, practical React, Google allowed.
```

Sessions in that directory then start from your notes rather than a sweep,
which takes the setup from minutes to seconds. The sitting says the shape came
from your material, not from research, so the provenance stays honest.

## The debrief

The hidden tests are hidden for exactly as long as the clock is running. The
moment it stops they have no reason to stay secret, and keeping them secret is
what makes a failed sitting useless: you are told you passed 25 of 28 and left
to guess which three cases you never thought of.

```
$ sim debrief

q1  Bracket Check   25/28   55:00 (79% of the sitting)
  - long unbalanced
  - one unclosed at the end
  - opener never closed

q2  Build Order
  never opened. Nothing to name: it was the clock, not the question
```

Questions are ordered by time spent, so the one that cost you the sitting is the
one you read first. `debrief --question q1` prints a reference solution beside
what you wrote.

It refuses while a session is live, and the gate is a timestamp rather than a
judgement, the same rule `submit` follows. A question you never opened is
reported as exactly that instead of as a list of twenty-six things you got
wrong, because never reaching it is a triage result and not a knowledge one.

## On the score

There isn't one. The scales real assessment platforms report are proprietary and
calibrated against data that is not public, so no third-party tool can reproduce it, and this one does
not pretend to. `report` tells you which questions you solved, how many hidden
tests passed, a qualitative band, and where your time went. A question that timed
out or was never attempted counts as a zero rather than being quietly dropped
from the average.

That is less satisfying than a number and considerably more useful for working out
what to practise. The time breakdown in particular measures the thing the format
is actually testing, which no amount of untimed practice can tell you.

## How questions are validated

Every question has to pass `tools/qa.py`, which CI runs on every commit. The
reference solution must pass the hidden suite, the untouched starter must not,
and every deliberately-wrong solution in the question's `mutants/` directory must
be caught by at least one hidden test.

Every question in the bank clears all three, and CI will not let one in that
does not. A question may be marked `"validated": "basic"` to skip the third
check while it is being written: it is still answerable and non-trivial, but
nothing has proved its hidden suite can tell a wrong answer from a right one, so
it can mark something correct that is not. Any such question says so at the top
of the session. Nothing in the bank carries that marker today.

That last check is the one that matters. A test suite that passes everything
discriminates nothing, and grading against one is worse than not grading at all,
because it tells you that you got it right when you did not.

## How the timing works

`start` records an absolute deadline once. Every later check is that deadline
minus now, so nothing drifts if you quit the process, close the laptop, or run
the command from somewhere else. The ending is stamped at the deadline rather
than at the moment it was noticed, so checking twice after the buzzer gives the
same answer twice.

Your system clock can obviously be changed. This is practice equipment, not a
proctor, and it does not pretend otherwise.

## About the hidden tests

They are in this repository. Anyone can read them, and encrypting them with a key
shipped alongside would be theatre.

So they are hidden from the session, not from you. They are never copied into a
workspace and the agent proctoring you will not read or describe them. Going and
looking anyway only costs you the practice you came for.

## Questions are original

Every question here is written from scratch against a public format description.
Real assessment items are not copied, paraphrased, or reconstructed. If you
recognise one as real, open an issue and it gets replaced.

See [ETHICS.md](ETHICS.md) for what this tool will and will not do,
[METHODOLOGY.md](METHODOLOGY.md) for exactly what is being measured, and
[skills/sim/references/formats.md](skills/sim/references/formats.md) for the
format specs the questions are calibrated against.

## Contributing

Questions especially. The quality gate is automated, so a question PR either
passes or tells you why it did not. Read [CONTRIBUTING.md](CONTRIBUTING.md)
first, in particular the rule about original questions only.

## Licence

MIT. See [LICENSE](LICENSE).
