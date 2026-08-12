# interview-sim

Timed technical-assessment practice that runs in your terminal, as an Agent Skill.

CodeSignal-style and LeetCode-style practice, simulated in your IDE. Not
affiliated with or endorsed by CodeSignal or LeetCode.

## Status

The engine is complete. Both formats run end to end.

- **GCA-style**: four questions, seventy minutes, all unlocked at once
- **ICA-style**: one project, four levels, ninety minutes, levels gated by hidden
  tests, with every level re-running the ones below it
- **Interview mode**: one question, forty-five minutes, with an interviewer who
  asks about your approach first and whose hints are counted
- `start`, `status`, `submit`, `hint`, `unlock`, `report`, and `list`
- hidden-test grading with partial credit
- deterministic timing, and submissions refused once the clock runs out

The bank is **nineteen GCA questions and four ICA projects**, four or five in
every difficulty slot. A session takes one question per slot, and it remembers
what it has already served you, so consecutive sittings do not repeat a question
until the bank runs out.

Company presets cover nineteen companies. Each records two separate claims: that
the company uses CodeSignal, and which assessment they give. The first is usually
first-party and solid, because CodeSignal publishes its customer list. The second
usually is not, because CodeSignal publishes nothing about which format any
customer chooses, so most entries record the format as unknown and ask you which
one you want rather than guessing.

## What it looks like

![A GCA session: naming a company starts the clock, real files appear, submitting reports how many hidden tests passed, and three questions are still waiting](demo.gif)

`sim` is the shell function the tool writes into every session workspace:

```
sim() { python3 ~/interview-sim/skills/sim/scripts/session.py "$@"; }
```

<details>
<summary>The same thing as text</summary>

```console
$ sim start --preset capital-one
Session started: gca-20260812T013654Z

capital-one preset: uses CodeSignal (high confidence).
Format GCA, medium confidence.
A community-maintained OA repo records Capital One moving to the CodeSignal GCA around
the 2021-22 season. Not first-party, and several seasons old.
Formats change every hiring cycle. Your actual invite email names the platform and the
format; trust that over this.

4 question(s), 1:10:00 on the clock.
Deadline 2026-08-12T02:46:54Z UTC.

Work here:
  ~/interview-sim-sessions/gca-20260812T013654Z
    q1/solution.py   Bracket Check
    q2/solution.py   Build Order
    q3/solution.py   Merge Feeds
    q4/solution.py   Route Fuel

$ ls ~/interview-sim-sessions/gca-20260812T013654Z/q1
problem.md   solution.py   tests_public.py

$ sim submit --question q1
q1  27 of 28 hidden tests passed (96%).

attempt 1, 1:09:36 left on the clock.

$ sim status
1:09:24 remaining

session   gca-20260812T013654Z  (gca, exam mode)
elapsed   0:35
deadline  2026-08-12T02:46:54Z UTC
workspace ~/interview-sim-sessions/gca-20260812T013654Z

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
ok    bank      23 questions under .../skills/sim/questions
ok    sessions  ~/interview-sim-sessions
ok    editor    code, so --open will use it
```

If `python3` is missing, run `xcode-select --install` on macOS or install it from
python.org.

Developed on macOS, and Linux works the same way. Windows is not something I have
run it on: the timeout in the grader kills a whole process group there, which is
POSIX only, so it falls back to killing the direct child. Everything else is
plain Python. If you try it, `check` first, and an issue either way is useful.

## Using it

Ask for a session in whatever words you like ("start a GCA mock", "give me an OA
practice run"), or run the engine directly:

```
python3 skills/sim/scripts/session.py start --format gca
python3 skills/sim/scripts/session.py status
python3 skills/sim/scripts/session.py submit --question q1
python3 skills/sim/scripts/session.py report
```

Add `--open` to any `start` and it opens the workspace in your editor as soon as
it is ready.

`start` builds a workspace under `~/interview-sim-sessions/` with a real
directory per question:

```
q1/problem.md        the question
q1/solution.py       yours to write
q1/tests_public.py   samples, not the grade
```

Open it in your editor and work normally. `status` tells you how much time is
left. `submit` runs your solution against the hidden suite and tells you how many
of its tests passed, and nothing else: which ones failed is the part you are
meant to work out. Resubmit as often as you like, it only costs time.

Once the deadline passes the session is over, and a submission after that is
refused even if it is correct. `report` then summarises the sitting.

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
python3 skills/sim/scripts/session.py report --session gca-20260811T193740Z
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

### Company presets

```
python3 skills/sim/scripts/session.py start --preset capital-one
```

```
capital-one preset: uses CodeSignal (high confidence).
Format GCA, medium confidence.
A community-maintained OA repo records Capital One moving to the CodeSignal GCA
around the 2021-22 season. Not first-party, and several seasons old.
```

For most companies the format is not confirmed and the tool says so rather than
picking one:

```
$ ... start --preset ramp
ramp is a confirmed CodeSignal customer, but which assessment they use is not
confirmed. Pick one: --preset ramp --format gca, or --format ica.
```

A company that is not in the table at all is not a dead end either. Name a format
and it runs, and says what it is doing:

```
$ ... start --preset stripe --format gca
stripe is not in the preset table, so nothing here knows what they actually use.
Running GCA because you asked for it. Your invite email names the platform and
the format.
```

Every entry carries source URLs, a confidence tier, and the date it was last
confirmed, and `tools/qa.py` rejects entries missing any of them. Formats change
every hiring cycle and your actual invite email beats this table.

```
python3 skills/sim/scripts/session.py presets            # the whole table
python3 skills/sim/scripts/session.py presets capital-one
```

### Paste a job posting

The engine never looks anything up. The agent running it can, when you ask.

Paste a posting and it fetches that page, works out the company and the role,
and takes the name to the table above. If the company is not in the table, it can
go and search for what their current screen is, and then write down what it
found:

```
python3 skills/sim/scripts/session.py learn stripe \
    --confidence medium --format gca --format-confidence low \
    --round "60 minute async assessment, 2 problems" \
    --source https://... --source https://...
```

That lands in `presets.local.json` next to your sessions, never in this
repository. `learn` refuses without a source and refuses to overwrite a reviewed
entry, and every session started from one repeats where it came from, with the
links, before the clock starts:

```
$ ... start --preset stripe
stripe comes from research done on this machine, not from the reviewed table.
Nobody has checked it but you, and it is as good as the sources it was built
from.
  https://...
```

A company that runs a **live** round rather than an asynchronous assessment is
recorded with `--mode interview`, and `start --preset <company>` then runs the
closest thing this tool has: one problem, forty-five minutes, a conversation, and
hints that get counted.

What research will never do is come back with the company's actual questions.
Question text found while looking is a signal about format and topic and nothing
else. Copying it would be someone else's property, and it would also make this a
tool for memorising answers instead of practising.

If the bank has nothing shaped like the role, the agent can write questions for
it and run a session on those:

```
python3 skills/sim/scripts/session.py start --format gca --questions 1 \
    --generated /tmp/my-questions
```

They are original problems, never real assessment items, and they are checked
before the clock starts: the reference solution must pass its own hidden suite,
and the untouched starter must fail it. What they have not had is the mutation
gate, so nothing has proved their tests can tell a wrong answer from a right one.
The session says so when it starts. Prefer the bank when the bank has something
close.

## What leaves your machine

Nothing, from the engine. It opens no network connection and the scripts import
nothing that could; the clock and the grading are entirely local.

If you run it through an AI coding agent, which is the usual way, that agent is
not local: the problem text and whatever you show it of your code go to that
provider, exactly as they would if you pasted them in yourself. The scripts work
with no agent at all if you would rather.

## On the score

There isn't one. CodeSignal's 200-600 scale is proprietary and calibrated against
data that is not public, so no third-party tool can reproduce it, and this one does
not pretend to. `report` tells you which questions you solved, how many hidden
tests passed, and a qualitative band. A question that timed out or was never
attempted counts as a zero rather than being quietly dropped from the average.

That is less satisfying than a number and considerably more useful for working out
what to practise.

## How questions are validated

Every question has to pass `tools/qa.py`, which CI runs on every commit. The
reference solution must pass the hidden suite, the untouched starter must not,
and every deliberately-wrong solution in the question's `mutants/` directory must
be caught by at least one hidden test.

Fifteen of the nineteen GCA questions and all four ICA projects clear all
three. A question may also be
marked `"validated": "basic"`, which skips the third check: it is still
answerable and non-trivial, but nothing has proved its hidden suite can tell a
wrong answer from a right one, so it can mark something correct that is not. Any
such question says so.

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
