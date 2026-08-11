---
name: sim
description: Run a timed, proctored coding-assessment simulation in the terminal. Use when the user asks to start or check an OA practice run, an online assessment mock, a GCA mock (4 questions / 70 minutes), an ICA mock (1 project / 4 levels / 90 minutes), CodeSignal-style or LeetCode-style timed practice, a mock interview, or any timed coding assessment they want started, timed, checked, or graded.
argument-hint: "[gca|ica|status]"
allowed-tools: Read, Glob, Bash(python3:*)
license: MIT
---

# Assessment simulator

Runs a real timed assessment. `scripts/session.py` owns the clock and the grades.
You are the proctor, not the grader.

Not affiliated with or endorsed by CodeSignal or LeetCode.

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
3. **Never read, print, paraphrase, or describe `tests_hidden.py`.** Not the file, not
   its contents, not a summary of what it checks, not "it probably tests empty input."
   Grading runs the file through a script and reports pass and fail counts only. Do not
   open it. Do not glob for it. If the user asks what the hidden tests check, tell them
   that is the part they have to reason about themselves.
4. **Never write to `solution.py`.** Not a fix, not a stub, not a corrected import, not
   "here is what it should look like." The candidate writes all of it. If the file is
   broken, say what the error was and let them fix it.
5. **Clarify wording, refuse hints.** If the problem statement is ambiguous, explain
   what it means. If asked for an approach, a data structure, a complexity target, or
   whether an idea will work, decline and say the clock is running. Clarifying what is
   being asked is fair. Telling them how to do it is not.
6. **After time expires, nothing more counts.** The script rejects late submissions.
   Do not negotiate. The debrief comes after.

## Running it

The script lives at `${CLAUDE_PLUGIN_ROOT}/skills/sim/scripts/session.py`. Invoke it
with `python3`. It is pure standard library, Python 3.9 compatible, and has no
third-party dependencies.

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
| "submit", "grade this", "check question 1" | `submit --question q1` |
| "how did I do", after time is up | `report` |

`unlock` is not implemented yet (it is for ICA mode). If the user asks for it, say
so plainly rather than improvising a substitute.

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
| 2 | bad arguments | fix the command |
| 3 | no active session | offer to start one |
| 4 | time is up, or a late submission was refused | stop the exam, move to debrief |
| 5 | a session is already running | show `status`; only pass `--force` if the user confirms abandoning it |
| 6 | question bank problem | report it, do not improvise a question |
| 7 | environment problem | report the message verbatim |
| 8 | the solution did not terminate | tell them it hangs; do not diagnose why |

### If python3 is missing

Say this and stop:

> interview-sim needs Python 3 and could not find it. On macOS run `xcode-select
> --install`, or install Python from python.org. Then try again.

Do not attempt to work around a missing interpreter by simulating the timer or the
grading yourself.

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
