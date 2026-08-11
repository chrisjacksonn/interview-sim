# interview-sim

Timed technical-assessment practice that runs in your terminal, as an Agent Skill.

CodeSignal-style and LeetCode-style practice, simulated in your IDE. Not
affiliated with or endorsed by CodeSignal or LeetCode.

## Status: day one

Early. What works today:

- `start`, `status`, and `submit`
- hidden-test grading with partial credit
- deterministic timing, and submissions refused once the clock runs out
- one GCA-slot question, validated by the quality gate below

Not built yet: `unlock`, `report`, ICA mode, and company presets. The bank is one
question. If you want a finished tool, come back in a couple of weeks.

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

The skill is then `/interview-sim:sim`. Plain `/sim` also works when no other
command has claimed that name.

Any agent that reads the Agent Skills convention:

```
npx skills add chrisjacksonn/interview-sim
```

By hand:

```
git clone https://github.com/chrisjacksonn/interview-sim
cp -r interview-sim/skills/sim ~/.claude/skills/
```

Claude Code is first-class here. Codex, Cursor, and the rest load the skill and
run the same scripts, but slash commands and Claude-specific frontmatter do not
apply there.

## Requirements

Python 3. That is the whole list: no pip install, no virtualenv, no
dependencies. The engine is standard library only and runs on 3.9, which is what
Apple's Command Line Tools still ship, so it works on a stock Mac.

If `python3` is missing, run `xcode-select --install` on macOS or install it from
python.org.

## Using it

Ask for a session in whatever words you like ("start a GCA mock", "give me an OA
practice run"), or run the engine directly:

```
python3 skills/sim/scripts/session.py start --format gca --questions 1
python3 skills/sim/scripts/session.py status
python3 skills/sim/scripts/session.py submit --question q1
```

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
refused even if it is correct.

## How questions are validated

Every question in the bank has to pass `tools/qa.py`, which CI runs on every
commit. The reference solution must pass the hidden suite, the untouched starter
must not, and every deliberately-wrong solution in the question's `mutants/`
directory must be caught by at least one hidden test.

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

See [ETHICS.md](ETHICS.md) for what this tool will and will not do.

## Contributing

Not yet. The question quality gate needs to exist before contributions can be
accepted against it. Issues and bug reports are welcome now.

## Licence

MIT. See [LICENSE](LICENSE).
