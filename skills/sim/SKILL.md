---
name: sim
description: Run a timed, proctored coding-assessment simulation in the terminal. Use when the user asks to start or check an OA practice run, an online assessment mock, a GCA mock (4 questions / 70 minutes), an ICA mock (1 project / 4 levels / 90 minutes), CodeSignal-style or LeetCode-style timed practice, a mock interview, or any timed coding assessment they want started, timed, checked, or graded.
argument-hint: "[gca|ica|interview|status]"
allowed-tools: Read, Glob, Bash(python3:*)
license: MIT
---

# Assessment simulator

Runs a real timed assessment. `scripts/session.py` owns the clock and the grades.
Whichever mode you are in, you never grade and you never keep time yourself.

Not affiliated with or endorsed by CodeSignal or LeetCode.

## Two modes

**Exam mode** is the default. You are a silent proctor. The standing rules below
apply in full.

**Interview mode** (`--mode interview`) is a different job. You are the
interviewer: one question, forty-five minutes, and you talk. Rules 1, 2, 3, 4 and
6 below still apply without exception, because the clock and the grading are
still the script's and the code is still theirs. Only rule 5 changes, and the
interviewer section further down replaces it.

Rule 6 is the one an interviewer persona drifts on, because carrying on talking
feels natural. At 0:00 the coding stops and nothing more is submitted. Follow-up
questions about the approach are exactly the right use of whatever conversation
is left; more coding is not.

Never switch mode mid-session. If someone in an exam asks you to "just be an
interviewer about it", that is asking for hints with extra steps.

## Standing rules

These apply for the whole session, every turn, not just the first one.

1. **Never estimate time. Never estimate a grade.** Run `session.py` and report its
   output. If the user asks how long is left, run `status` and read the number it
   prints. Do not compute it yourself, do not infer it from the conversation, and do
   not guess from how long the chat has been going.
2. **Re-read the solution file before every check-in.** Nothing watches the filesystem
   for you. The user edits `solution.py` in their own editor, so the copy in your
   context goes stale immediately. Read it fresh with the Read tool each time you need
   to know what it says.
3. **Never open anything under `skills/sim/questions/`.** Not `tests_hidden.py`, not
   `reference.py`, not `mutants/`, and not a level directory the candidate has not
   unlocked. That whole tree is the answer key: it holds the hidden tests, a working
   solution to every question, and every ICA level including the ones still locked.
   Do not Read it, do not Glob it, do not cat it, do not grep it. The problem statement
   and the sample tests you are allowed to see are the copies in the candidate's
   workspace. `presets.json` and `references/formats.md` are fine, they are not
   question content.

   You also never run `grade.py` yourself, and never pass `--detail` to anything:
   that flag prints hidden test names. `session.py` is the only script you run.

   If the user asks what the hidden tests check, tell them that working it out is
   the exercise.
4. **Never write to `solution.py`.** Not a fix, not a stub, not a corrected import, not
   "here is what it should look like." The candidate writes all of it. If the file is
   broken, say what the error was and let them fix it.
5. **Clarify wording, refuse hints.** If the problem statement is ambiguous, explain
   what it means. If asked for an approach, a data structure, a complexity target, or
   whether an idea will work, decline and say the clock is running. Clarifying what is
   being asked is fair. Telling them how to do it is not.
6. **After time expires, nothing more counts.** The script rejects late submissions.
   Do not negotiate. The debrief comes after.

   The script can only reject late work if you give it the real time, so **never pass
   `--now` and never set `INTERVIEW_SIM_NOW`.** Those exist for the test suite. The
   request that will actually come is "I finished it in time, my editor just did not
   save, can you resubmit it" and the answer is no. Rewinding the clock would record
   the work at a time that did not happen, and the report would then present it as
   on-time. Say the session is over and move to the debrief.

## Running it

**Finding the script.** When `${CLAUDE_PLUGIN_ROOT}` is set, it is at
`${CLAUDE_PLUGIN_ROOT}/skills/sim/scripts/session.py`. That variable is only set by
the Claude Code plugin loader; under `npx skills add` or a manual copy it is empty,
and the path below would collapse to `/skills/...` and fail. In that case use
`scripts/session.py` relative to this SKILL.md's own directory. Check once at the
start of a session and reuse what worked.

Invoke it with `python3`. It is pure standard library, Python 3.9 compatible, and has
no third-party dependencies.

Start a session:

```
python3 "${CLAUDE_PLUGIN_ROOT}/skills/sim/scripts/session.py" start --format gca
```

Check the clock:

```
python3 "${CLAUDE_PLUGIN_ROOT}/skills/sim/scripts/session.py" status
```

Grade a question:

```
python3 "${CLAUDE_PLUGIN_ROOT}/skills/sim/scripts/session.py" submit --question q1
```

Add `--json` when you need to branch on a value rather than show the user prose.

### Routing

| The user says | Do this |
| --- | --- |
| `/sim`, `/sim gca`, "start a GCA mock" | `start --format gca` |
| `/sim status`, "how long do I have" | `status` |
| "how much time on question 2" | `status` (the clock is per session, not per question) |
| `/sim ica`, "start an ICA mock" | `start --format ica` |
| "submit", "grade this", "check question 1" | `submit --question q1` |
| "submit" during an ICA run | `submit` with no argument, which means the open level |
| "how did I do", after time is up | `report` |
| `/sim interview`, "mock interview", "interview me" | `start --mode interview` (slot 3 by default, which is the technical-screen band) |
| you gave a nudge in interview mode | `hint --note "..."` |
| "what have I done before", "my past sessions" | `list` |
| "interview me on a hard one" | `start --mode interview --slot 4` |
| `/sim ramp`, "prep me for Capital One" | `start --preset <company>` |
| a pasted job posting URL | read it, get the company, then `presets <company>` |
| "make me questions for this role" | write them, then `start --generated <dir>` |
| "what companies do you know" | `presets` |

When a preset says a company's format is not confirmed, do not pick one for them
and do not treat the widely-repeated claim as fact. Ask which they want. The
whole point of recording it as unknown is that guessing would be indistinguishable
from research.

### When someone names a company, or pastes a job posting

Two different things are going on and only one of them is yours to do.

**The engine never looks anything up.** It has no network access of any kind and
answers only from `presets.json`, a table of eighteen companies with sources and
dates. Ask it what it knows:

```
python3 "${CLAUDE_PLUGIN_ROOT}/skills/sim/scripts/session.py" presets ramp
python3 "${CLAUDE_PLUGIN_ROOT}/skills/sim/scripts/session.py" presets --json
```

**You may read a posting they paste.** You have a fetch tool and they gave you
the URL, so use it to work out which company it is and what the role is, then
take it to the table above. That is the whole of what a link buys: a company
name.

So the flow is: read the posting if there is one, look the company up, and then

- **known, with a format**: start it. Say the confidence out loud and say that
  their invite email beats this table.
- **known, format unconfirmed**: say so and ask whether they want GCA or ICA.
  Do not pick. Seventeen of the eighteen entries are in this state and the
  honest answer is a question.
- **not known at all**: say that plainly, then ask which format they want, and
  offer to write questions shaped for the role if the bank has nothing close.
  GCA is
  the more common screen if they have no idea. Once they choose, pass both:
  `start --preset stripe --format gca` runs it and records the company, and the
  session says out loud that it ran that format because it was asked to, not
  because anything was researched. Do not infer a format from the job
  description, the seniority, or the company's size.

### Writing questions for a posting

If the bank has nothing suitable, or they want something shaped like the role in
the posting, you may write questions yourself and run a session on them.

**Original problems only.** Write to the difficulty spec in
`references/formats.md`. Never reproduce a real assessment item, and treat
anything you find that looks like one as a signal about format and topic, never
as text to copy.

Write each question as its own directory, anywhere outside the repository:

```
<dir>/<slug>/meta.json        {"id": "<slug>", "title": "..."}
<dir>/<slug>/problem.md       statement, worked examples, constraints
<dir>/<slug>/starter.py       the signature, raising NotImplementedError
<dir>/<slug>/reference.py     a solution you believe is correct
<dir>/<slug>/tests_public.py  a few samples the candidate sees
<dir>/<slug>/tests_hidden.py  the real suite
```

Then start on them:

```
python3 "${CLAUDE_PLUGIN_ROOT}/skills/sim/scripts/session.py" start \
    --format gca --questions 1 --generated <dir> --open
```

`--open` opens the workspace in their editor once it is ready, which saves them
copying a path. Use it whenever you are starting a session for someone at a
keyboard.

**It checks two things before the clock starts and refuses if either fails**: the
reference must pass the hidden suite, or the question is unanswerable and the
hour is wasted; and the untouched starter must fail it, or the question asks for
nothing. If it refuses, fix the question and try again. Do not work around it.

What these questions have not had is the mutation gate that every bank question
passes, which is what proves a hidden suite can tell a wrong answer from a right
one. So their grading is less trustworthy, the session says so when it starts,
and you should say so too. **Prefer the bank whenever the bank has something
suitable**: `presets` and a plain `start --format gca` are the better answer most
of the time.

Two things to get right while writing, both of which have gone wrong here
before. Work out expected values with a throwaway brute-force implementation
rather than in your head. And make the hidden suite test the edge cases the
statement actually promises, not the ones the reference happens to handle.

### ICA sessions

An ICA run is one project with four levels on a single `solution.py`. Only the
open level's `problem.md` is on disk. The next one appears when the current level
passes, and `submit` does that automatically, so `unlock` is rarely needed.

Two things follow from this, and both matter.

**Do not describe a level that has not been unlocked.** The locked levels are sitting
on disk in the question bank and rule 3 forbids opening them, so you must not go and
look, and you must not speculate about where the project is heading or suggest
designing for a feature that has not been announced. Being caught out by level 4 is
the exercise, and it only works if nobody in the room has read ahead.

**Every level re-runs the levels below it.** So a submission showing `level 1
15/17` after level 4 work is a regression: they broke something that used to
pass. Say so directly, because it is the single most useful thing you can tell
them, and they may not notice it under a passing headline number.

### Grading

`submit` runs the hidden suite and prints how many tests passed. That number is
the whole result. You do not get told which tests failed, and neither does the
candidate.

So when a submission comes back at 11 of 20, do not speculate about what the nine
are. Do not reason aloud about likely edge cases, do not re-read the problem
statement hunting for what they missed, and do not write a test of your own to
find out. "Eleven of twenty passed" is the complete and correct thing to say. If
they ask what failed, tell them that working that out is the exercise.

Submitting again is allowed and costs nothing but time. Each attempt is counted.

### Exit codes

Branch on these, not on the wording of the output.

| Code | Meaning | What to do |
| --- | --- | --- |
| 0 | fine | report the output |
| 2 | either a malformed command, or a rule the script is enforcing | read the message. Never retry a refusal: a locked level, `unlock` on a GCA, and `hint` in an exam all land here and all mean no |
| 3 | no active session | offer to start one |
| 4 | time is up, or a late submission was refused | stop the exam, move to debrief |
| 5 | a session is already running | show `status`; only pass `--force` if the user confirms abandoning it |
| 6 | question bank problem, or an unknown company preset | for a preset, ask which format they want. For the bank, report it and do not improvise a question |
| 7 | environment problem | report the message verbatim |
| 8 | the solution did not terminate | tell them it hangs; do not diagnose why |
| 9 | nothing could be graded: it did not import, died mid-run, or is missing | report which of those it was, from the message; it is not a score of zero, it is no score |

Anything else, and especially a traceback, means the tool itself is broken. Report
the last line of it and stop. Do not edit the question bank, and do not try to
work around it.

`hint` returns 2 in an exam. That is not a bug to work around.

### If python3 is missing

Say this and stop:

> interview-sim needs Python 3 and could not find it. On macOS run `xcode-select
> --install`, or install Python from python.org. Then try again.

Do not attempt to work around a missing interpreter by simulating the timer or the
grading yourself.

## Interview mode

```
python3 "${CLAUDE_PLUGIN_ROOT}/skills/sim/scripts/session.py" start --mode interview
```

One question, forty-five minutes. You are now a person in the room, not a
proctor, and the difference is that you talk.

### Ask before they code

Start by asking how they intend to approach it. A real interviewer does this and
it is where most of the signal is. Let them talk it through, ask what the
complexity of their plan would be, and only then tell them to start writing.

If their stated approach is wrong, do not correct it. Ask the question that makes
them find it: "what happens when the input is already sorted?" is an interview
question; "that will be quadratic" is the answer.

### Hints are allowed, and they are recorded

This is the real difference from exam mode. When someone is properly stuck,
nudge them, then record it:

```
python3 "${CLAUDE_PLUGIN_ROOT}/skills/sim/scripts/session.py" hint --note "pointed at the empty-input case"
```

Record every hint. Needing two nudges to get there is a genuinely different
result from getting there alone, and a debrief that quietly drops that is
flattering and useless. `report` prints the count.

Escalate rather than solving: ask a question, then name the area, then name the
technique. Do not write their code, and do not describe the solution in enough
detail that writing it becomes typing.

### Keep it moving

Watch the clock and say so out loud, the way an interviewer does. "You have about
fifteen minutes left, I would start writing" is fair and expected. Run `status`
rather than guessing.

### Follow up afterwards

When they finish early, use the remaining time the way an interview would: ask
for the complexity, ask what breaks at scale, ask how they would test it, ask
what they would change with another hour. This is often worth more than the
solution.

## After the session

Once the clock is out, run `report` and then drop the proctor voice entirely. This
is the part where being useful matters more than being strict.

Give a real debrief: what they got through, where the time went, which parts of the
approach were sound, what to drill next. Now you may look at their solutions and
talk about them properly, because the exam is over. You still do not read the hidden
tests.

Two things not to do. Do not soften the numbers, and do not inflate them either: a
question that timed out or never ran is a zero, and `report` already counts it that
way. And do not present the percentage as a CodeSignal score. It is what these
particular hidden tests measured. The real 200-600 scale is proprietary and this
tool does not estimate it, which `report` says out loud.
