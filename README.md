# interview-sim

[![CI](https://github.com/chrisjacksonn/interview-sim/actions/workflows/qa.yml/badge.svg)](https://github.com/chrisjacksonn/interview-sim/actions/workflows/qa.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

**Practice the screen a company actually runs, on a real clock, in your own editor.**

Paste a job posting. It researches what that company's technical screen is,
writes an original question in that shape, proves the question can grade, and
starts the clock. Real files, hidden tests, and a deadline that does not
negotiate.

![A session: research runs, real files appear, submitting reports how many hidden tests passed](demo.gif)

- **Researches, never guesses.** Live candidate reports, dated and sourced,
  every session. No stored company data to go stale
- **Writes the question for the round.** An original problem shaped by what
  the company reportedly asks, never a reused or real assessment item
- **Proves it can grade before you sit it.** Every question ships
  deliberately-wrong solutions; if the hidden tests miss one, the question is
  refused before the clock starts
- **A clock that cannot be argued with.** A script owns the time and the
  grades; a correct answer submitted one second late is refused
- **Teaches after.** `report` shows where the time went per question;
  `debrief` names what each failed hidden test was checking, with a reference
  solution on request

## Install

Claude Code:

```
/plugin marketplace add chrisjacksonn/interview-sim
/plugin install interview-sim@interview-sim
```

Any agent that reads the Agent Skills convention:

```
npx skills add chrisjacksonn/interview-sim
```

Requirements: Python 3 (3.9+, stdlib only, nothing to pip install). For the
fastest sitting (~2 minutes to the clock): `/model sonnet`, then `/effort low`.

## Use

```
/interview-sim:sim https://jobs.example.com/some-posting
```

Or in plain words: "prep me for Ramp", "give me a GCA mock", "interview me".
The agent researches, briefs you on what it found and how well sourced it is,
writes the question, and the clock starts. Work in your own editor; `submit`
tells you how many hidden tests passed and nothing else. Which ones failed is
the exercise.

While you work: split your terminal and run `sim watch` for a live countdown.
When it ends (or you `end` it): `report` breaks the clock down per question,
and `debrief` turns the hidden tests into the lesson:

```
q1  Bracket Check   25/28   55:00 (79% of the sitting)
  - long unbalanced
  - one unclosed at the end
  - opener never closed
```

Three shapes, parameters yours to set:

| Shape | Looks like | Flags |
| --- | --- | --- |
| The exam | 4 questions, 70 min, all open, silent proctor | `--format gca` |
| The project | 1 project, 4 gated levels, 90 min, levels re-test earlier ones | `--format ica` |
| The interview | 1 question, 45 min, an interviewer who counts hints | `--mode interview` |

## How it stays honest

**Every question must prove its tests can tell right from wrong.** Questions
ship with deliberately-wrong solutions, and each one must be caught by at
least one hidden test. Shipped questions clear this in CI on every commit;
questions written live clear the identical gate before the clock starts. A
suite that passes everything grades nothing, and grading against one is worse
than not grading at all.

**There is no score.** The scales real platforms report are proprietary and
cannot be reproduced, so the report gives what was measured: questions solved,
hidden tests passed, and where the time went. A question that timed out counts
as zero rather than vanishing from the average.

**Nothing is cached.** A second session for the same company searches again,
because hiring processes change between cycles and stored answers rot
invisibly. Your own knowledge is the exception: notes in the practice
directory, or a pasted invite email, are ground truth and skip the search.

**Every question is original.** Written to public format descriptions; found
question text is only ever a signal about format and topics. PRs containing
real assessment items are rejected.

The fine print, deliberately public: [METHODOLOGY.md](METHODOLOGY.md) states
exactly what is and is not measured, [ETHICS.md](ETHICS.md) covers what this
tool refuses to be (the hidden tests are readable in this repo; they are
hidden from the session, not from you), and
[skills/sim/references/formats.md](skills/sim/references/formats.md) documents
the format specs questions are written to.

<details>
<summary><b>Running the engine directly (no agent)</b></summary>

The clock, grading, and reports are plain Python; the agent is only needed for
research and question-writing. `sim` is the shell function every session
workspace README defines.

```
sim start --format gca          # a 4-question exam from the shipped set
sim status                      # time remaining
sim submit --question q1        # grade against the hidden suite
sim watch                       # live countdown, for a second pane
sim end                         # give up on purpose; opens the debrief
sim report                      # per-question results and time breakdown
sim debrief --question q1       # failed tests explained + reference solution
sim list / sim progress         # history, and what it adds up to
sim check                       # is this machine set up
```

Sessions are real directories under `./interview-sim-sessions/`, one folder
per company and round, each self-gitignored. ICA runs put four gated levels on
one `solution.py`; every level re-runs the ones below it, so breaking level 1
while adding level 4 costs you.

</details>

<details>
<summary><b>Permissions: running without interruptions</b></summary>

A timed sitting stops being timed if every file read asks permission.
Shift+tab toggles auto mode for a session, or scope it to your practice
directory with `.claude/settings.json`:

```json
{"permissions": {"defaultMode": "auto"}}
```

The skill mentions this once per session and cannot change permissions itself,
deliberately.

</details>

<details>
<summary><b>Platforms and caveats</b></summary>

Developed and tested in Claude Code on macOS; Linux works the same way.
Windows falls back from process-group kills in the grader; `check` first.
Codex, Cursor, and other Agent Skills hosts should run the same scripts, but
no full session has been sat in one: treat as untested, and an issue saying
whether it worked is genuinely useful.

Python is the graded language today. The engine opens no network connection;
the agent driving it does, for research, exactly as if you searched yourself.

</details>

## Contributing

Bug reports, platform reports, and feature PRs (issue first) are welcome;
question PRs are not, since questions are written live per sitting. See
[CONTRIBUTING.md](CONTRIBUTING.md).

MIT. Not affiliated with any assessment platform or employer.
