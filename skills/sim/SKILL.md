---
name: sim
description: Run a timed coding assessment simulation in the terminal. Use for OA practice, GCA or ICA mocks, mock interviews, pairing rounds, take-homes, and pasted job postings.
argument-hint: "[job posting URL, or company and role]"
allowed-tools: Read, Glob, Bash(python3:*), WebFetch, WebSearch
license: MIT
---

# Assessment simulator

Runs a real timed assessment. `scripts/session.py` owns the clock and the grades.
Whichever mode you are in, you never grade and you never keep time yourself.

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
   workspace. `references/formats.md` is fine, it is not question content.

   You also never run `grade.py` yourself, and never pass `--detail` to anything:
   that flag prints hidden test names. `session.py` is the only script you run.

   If the user asks what the hidden tests check, tell them that working it out is
   the exercise, and that `debrief` names every one they failed the moment the
   clock is out.

   **That is a difference worth being precise about.** After the session ends,
   `debrief` prints what each failed test was guarding, and reporting its output
   is the whole point of the command. The rule that does not change is the one
   about the file: you never open `tests_hidden.py` yourself, before or after,
   because the thing keeping the answer key shut during a live session cannot be
   your memory of which phase you are in. The script knows the time. You do not.
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
python3 "${CLAUDE_PLUGIN_ROOT}/skills/sim/scripts/session.py" start --format gca --open
```

**Say this in your very first reply, and never again.** Not before the clock
starts, which is far too late: **before your first tool call.** Put it on the
line after you say what you are about to look up, so it arrives while they are
still reading rather than once they are waiting.

The timing is the whole point. Researching a company is a fetch and a dozen
searches, so a permission prompt per call interrupts the part they are actually
watching, and by the time a session is ready to start they have already clicked
through fifteen of them. Mentioning it then tells them what would have helped
ten minutes ago.

> Looking up what Shopify runs for their internship now.
>
> If auto mode is off, shift+tab turns it on. It is recommended for this one:
> a dozen searches happen before the clock starts, and a timed sitting follows.

It is their call and their machine, so say it once and move on whether they do
it or not. Do not offer it as a question you can act on: nothing you emit can
change the permission mode, only shift+tab or the flag the session was launched
with, and a yes you cannot honour is worse than a sentence they can act on
themselves.

If they ask for something more permanent, it is a `.claude/settings.json` in the
directory they practise in, holding `{"permissions": {"defaultMode": "auto"}}`.
Sessions there then start in auto mode and nothing else on their machine
changes. Offer it once; do not write it for them without being asked.

**Always pass `--open`** when there is a person at the keyboard. The workspace
is built in their working directory, so the files appear inside the project they
already have open, and `--open` navigates the editor they are already in to the
problem statement. It does not open a new window and it does not take them
anywhere.

It opens the problem, not the starter, and your first instruction should match:
tell them to read it, and to start writing in the `solution.py` beside it when
they are ready. Somebody sitting in an empty starter file is being invited to
type before they know what is being asked, which is the habit these formats
punish hardest.

Having done that, do not then print the path at them. They are looking at the
file.

Check the clock:

```
python3 "${CLAUDE_PLUGIN_ROOT}/skills/sim/scripts/session.py" status
```

**Never run `watch` yourself.** It is a countdown for a second terminal pane and
it does not return until the clock does, so shelling out to it and waiting hangs
the session until the deadline. Tell them to run it, in a split, in their own
words:

> If you want a clock on screen, split your terminal and run `sim watch` in the
> other pane. It also puts the time in the tab title, so it is there even when
> the pane is not.

Offer that once, when the session starts, and then leave it. `status` is how
**you** read the clock, every time.

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
| "how much time do I have left" | `status`. The remaining clock is per session, never per question |
| "where did my time go", "what did I spend the hour on" | `report`, which breaks the clock down per question once the sitting is over |
| "can I see a timer", "put a clock on screen" | tell them to run `watch` in a split pane. Never run it yourself |
| `/sim ica`, "start an ICA mock" | `start --format ica` |
| "submit", "grade this", "check question 1" | `submit --question q1` |
| "submit" during an ICA run | `submit` with no argument, which means the open level |
| "how did I do", after time is up | `report`, then `debrief` |
| "what did I get wrong", "which tests failed" | `debrief`. It refuses while the clock is running, which is the correct answer to that question during a session |
| "show me how it should have been done" | `debrief --question q2`, which adds a reference solution |
| `/sim interview`, "mock interview", "interview me" | `start --mode interview` (slot 3 by default, which is the technical-screen band) |
| you gave a nudge in interview mode | `hint --note "..."` |
| "what have I done before", "my past sessions" | `list` |
| "am I improving", "how am I doing overall" | `progress` |
| "is this thing set up", or anything failed oddly | `check` |
| "interview me on a hard one" | `start --mode interview --slot 4` |
| `/sim ramp`, "prep me for Capital One" | search for what the company runs, write a question for it, gate it, then start |
| a pasted job posting URL | read it, get the company, then search |
| "make me questions for this role" | write them, then `start --generated <dir>` |
| "what companies do you know" | none of them by heart. Every one is looked up when it is named |

When research does not establish a format, do not pick one for them and do not
treat a widely-repeated claim as fact. Ask which they want. Guessing would be
indistinguishable from research to them, which is exactly why it must not happen.

### When someone names a company, or pastes a job posting

**Look it up. Every time. There is nothing to consult instead.**

This tool used to ship a table of companies, and cache what it researched, and
carry machinery for deciding when either had gone stale. All of it has been
removed, because a search answers the question better and more currently than a
file written last season can. So there is no table to check, no cache to prefer,
and no version of "I already know this one".

**First, use what they already gave you.** The candidate often holds ground
truth the internet does not have: an invite email naming the platform and
duration, a recruiter's description of the round, notes in the directory they
practise in (a CLAUDE.md or similar saying what the company runs). Any of
those is the person sitting the rounds telling you the answer, and it beats
every search. Build the sitting from it, say in the brief that the shape came
from their own material rather than from research, and skip the sweep. Do not
solicit it: if it is in front of you, use it; if it is not, search without
asking whether they have something better.

**Read the posting if they pasted one.** You have a fetch tool and they gave you
the URL, so use it to work out the company and the role. That is what a link
buys: a name to search for.

**Then search, without asking permission.** Naming a company is the request, so
searching is the answer to it, not a favour to check in about. Say in one line
that you are looking, then look.

**Research runs in three waves, and inside a wave every call goes out in one
message.** Wave one is the posting fetch, alone, because everything else needs
the company and the role. Wave two is every search plus the OA index fetch,
which do not depend on each other. Wave three is the deep fetches you picked
out of the results, which need wave two's URLs but not each other. A wave costs
its slowest call instead of the sum, which is the difference between a minute
of research and three.

The thing that breaks this is narration. A sentence between two calls forces
them to run one after the other, so the last run's "good signal already,
cross-checking..." serialised the whole sweep. Say what you are about to look
for once, before the wave, and say nothing again until it is back.

That one line is also where the auto mode sentence goes, on the line beneath it,
before any tool runs. See "Running it" above. Said any later it is advice about
a problem they have already sat through.

**Then build the sitting out of what you found.** The engine has no idea who any
company is; you pass the shape as flags:

```
python3 "${CLAUDE_PLUGIN_ROOT}/skills/sim/scripts/session.py" start \
    --company shopify --round pairing \
    --format gca --mode interview --minutes 45 \
    --topic "rate limiting" --topic "object oriented design" \
    --open
```

`--company` and `--round` are labels for the record. `--format`, `--mode`,
`--questions`, `--minutes` and `--topic` are the shape, and they come from the
research and nowhere else. **Naming a company without `--format` is refused**,
because naming a company is a claim about what that company runs, and the tool will not
guess one. If the search establishes nothing usable, that refusal is your cue to
ask them which format they would rather practise, and to say plainly that nobody
established it.

### How to research it

Do it properly or not at all:

1. **Search for candidate reports**, not for marketing pages. What you want is
   somebody describing a screen they actually sat, with a date attached.

   Where those live, roughly in order of how much they are worth: Blind and the
   company-specific subreddits, then r/csMajors, r/cscareerquestions and
   r/leetcode, then LeetCode Discuss, then Glassdoor's interview section. Search
   terms that work are the plain ones a person would type: "<company> online
   assessment intern 2026", "<company> OA reddit", "<company> codesignal".

   What to discount: the company's own careers page, which describes the process
   they wish they ran, and the prep-site pages that rank for "<company>
   interview questions", which are written for search engines and recycle the
   same paragraph across two hundred companies. If the only thing you can find
   is that kind of page, you have found nothing.

   **And never fetch an aggregator page at all.** Its one claim, when it has
   one, is already in the search snippet, and its page is reliably the largest
   fetch in the sweep: the same 900KB guide has been fetched in three separate
   sittings to corroborate what the snippet already said. Corroboration reads
   fine from a snippet. Fetches are for candidate reports.

   **Research has a stop condition: two independent, dated candidate reports
   agreeing on the round shape.** The moment you have them, stop. A lookup
   after agreement is collecting, not learning, and every sweep so far has
   grown fatter than the one before because nothing said when done was done.
   The ceiling either way is **four searches and four page fetches**; if
   agreement has not arrived by then, say plainly what is established and what
   is not, and let the confidence statement carry the shortfall rather than a
   ninth lookup.

   A candidate report is a page of tens of kilobytes where somebody describes
   a round they sat. An API endpoint is not one, an employer's job-board feed
   is not one (a past sweep pulled 2.3MB of one, compensation data included,
   and learned nothing), and a page measured in megabytes is almost never one.

   What you are looking for is narrow and worth being clear about: **the shape
   of the round and the subjects**. How long, how many problems, unlocked at
   once or gated, live or asynchronous, and what people say the problems were
   about. "Two problems, an hour, one was a string parsing thing and one was a
   graph" is a complete result. Anything more specific than that is question
   text, and question text is not what you are collecting.
2. **Date it against the OA index. Every time, not only when step 1 came back
   thin.** Forum posts do not carry a "still true" stamp, and stale-but-confident
   is the failure mode that matters here: a round described accurately in 2024
   may have been replaced twice since.

   Fetch this exact URL, once. It is the raw file; the rendered page is a
   second, larger fetch of the same content:

   https://raw.githubusercontent.com/perixtar/Tech-OA-Interview-Questions/main/README.md

   It is a table of company, question title, **format** (Coding, SQL, System
   design, Low-level design, AI coding), and **when that question was last
   reported**, flagged for the last two weeks and the last 45 days. Two things
   to take from it: the format column, which is the shape-of-round signal
   directly, and the dates, which tell you whether what the forums described is
   still being seen.

   Weight it as corroboration, never as the finding. It is the front page of a
   commercial practice site, the freshness dates are self-reported and nobody
   has verified them, so it never outranks somebody describing a screen they
   personally sat. What it is good for is saying "and it is still being seen
   this month", or "and nothing has been reported since 2024", both of which
   change the confidence you state out loud.

   **Take titles as topics and stop there. Do not follow the links.** The
   statements behind them are real assessment items and this is the single place
   in the whole flow where reproducing one is easiest, because a title like
   "Minimum Height Difference Between Distant Peaks" is specific enough to
   reconstruct the problem from. "They ask interval problems" is the legitimate
   use of that title. A question that is recognisably that problem with the
   nouns changed is a derivative and is forbidden, see below.

   If the repository is gone, renamed, or will not load, say so in a clause and
   move on. It is a cross-check, not a dependency.
3. **Report what you found before acting on it.** Say what the sources are, how
   old they are, and how much they agree. Two posts from the same month
   describing the same round is a finding. One comment from 2021 is a rumour
   with a link on it.

   **Open with the finding itself.** Not with a verdict on your own research,
   and not with a preamble. "Enough to go on", "that was harder than expected",
   "here is what I could piece together" all rate the search instead of
   reporting it, and they make a solid result sound like a shrug. State what
   the company runs, then where that came from and how confident it is. The confidence
   belongs in a clause at the end, not in a throat-clear at the front.
4. **Say which of the two claims you actually established.** Whether the company runs an
   asynchronous coding assessment at all, and what that assessment is, are
   separate questions and the second is usually the one you cannot answer.
5. **Never present a guess as a finding.** If the search comes back thin, the
   honest output is "I could not establish this", followed by asking which
   format they want to practise. Thin research presented confidently is worse
   than no research, because they will plan around it.
6. **Nothing is remembered between sessions, and that is deliberate.** There is
   no log to write to and none to read from. Every company is looked up the day
   it is named, because a hiring process changes between cycles and a note from
   last month is a guess wearing a date. So never say a search agrees with
   something you found before, never refer to a previous sitting, and never let
   a second session for the same company skip the search.

**A process is usually more than one sitting, so say so.** If the process is
an assessment and then a live round, those are two different shapes and only one of
them is what they are practising today. Tell them what the process looks like
end to end, then **set up the round the posting's stage implies, the technical
screen unless something says otherwise, and say so in one clause with the offer
to switch**: "this sitting is the live screen; say the word if you want the
assessment instead." Do not stop on a blocking question. Two runs asked and one
decided, the deciding one was better, and the answer is almost always the
recommended round while the round-trip costs a minute of their attention.
A live round runs as `--mode interview`, so you are the interviewer for it.

**What you may never do is reproduce their questions.** Not the ones in a forum
post, not the ones on a practice site, not the ones behind a title in the OA
index, not a lightly reworded version of any of them. This is not a preference:
real assessment items are the one thing a company will act on, and a takedown
against this repository is a real outcome with precedent.

The test to apply while writing: if somebody who had sat the real thing read
your question, would they recognise it as the same problem? If yes, it is a
derivative however much the wording moved. Same subject is fine and is the whole
point. Same problem is not.

**What you do instead is take the topics.** If people report being asked about
rate limiting and graph traversal, that is the useful part and it is fair game:
those subjects are what you write the question about, which is the next section.
Put the same topics in the question's `meta.json` and pass them as `--topic`
flags, so the match line the candidate sees says `on` because it is true.

The session prints that match (`on`, `partial` or `off`) on screen, in the
report, and into the record. With a question written for the round it should
never be anything but `on`. If you ever find yourself about to start a sitting
whose match is `off`, stop: that is the failure this line exists to catch, and
the answer is to write the question, not to explain afterwards. A candidate
preparing for a practical React round was once dealt a heap problem this way,
and found out only because they knew the company well enough to notice.

The one honest exception: they would rather start now than wait the few minutes
writing takes. That is theirs to choose. Offer the pre-written corpus, say
plainly it is general practice rather than preparation for that round, and let
the match line say `off` on screen, because it is true.

Never fill the gap by pasting in something you found.

`--topic` works on its own too, whenever someone tells you what they want to
drill against the pre-written corpus.

### Writing the question

The flow, in order, no steps skipped:

1. Sketch the question from the research: scenario, mechanism, three or four
   requirements, sized for the round.
2. Write the findings brief.
3. Write the set: reference first, values from running it, suites, mutants.
4. `start`. Fix anything the gate names yourself.

A subagent dispatch used to sit in this flow so the set could build while the
candidate read. Every live run skipped it, and at the current set size it was
worth thirty seconds against a cold start, so it is gone rather than escalated.
Do not reintroduce it.

**When a company or a round has been researched, the question is written for it.
Every time.** The corpus of pre-written questions exists to prove the gate works
and to serve a plain "give me a GCA mock" with no company attached. It is not
what a researched sitting runs on: it was the fallback once, and what that
produced was a candidate preparing for a practical frontend round being dealt a
heap problem. Research, then write, then gate, then start the clock.

**Original problems only.** Write to the difficulty spec in
`references/formats.md`, shaped by the topics and round style you found. Never
reproduce a real assessment item, and treat anything you find that looks like
one as a signal about format and topic, never as text to copy.

Each question is its own directory, anywhere outside the repository. This
listing and the example below are the complete contract: there is nothing to
verify in the engine source, and the minutes spent re-checking it are minutes
the candidate sits waiting.

```
<dir>/<slug>/meta.json        see below; id, title and topics are the fields read
<dir>/<slug>/problem.md       statement, worked examples, constraints
<dir>/<slug>/starter.py       the signature, raising NotImplementedError
<dir>/<slug>/reference.py     a solution you believe is correct
<dir>/<slug>/tests_public.py  a few samples the candidate sees
<dir>/<slug>/tests_hidden.py  the real suite
<dir>/<slug>/mutants/         plausible wrong solutions, minimum 3
```

A complete `meta.json`, verbatim:

```json
{"id": "formula-cells", "title": "Formula Cells",
 "topics": ["formula parsing", "cell references", "cycles"]}
```

Anything else (`difficulty`, `slot`, `entrypoint`) is defaulted by the engine
and not worth writing.

**`reference.py` is written before either test file, always.** Expected values
come from running it (below), and a suite written first is a suite whose values
were typed from a head. That mistake has cost a correction round once already.

Both test files are **stdlib `unittest`**, and the grader collects nothing
else. This skeleton is the convention, verbatim:

```python
import unittest
from solution import solve

class TestHidden(unittest.TestCase):
    def test_the_worked_example(self):
        self.assertEqual(solve(["a", "b"]), 2)
```

Plain pytest-style test functions collect as **zero tests** and the gate
refuses the question. No pytest, no fixtures, no parametrize: Python 3.9
stdlib is the whole world here.

**Write it in one pass, reference first, mutants beside it.** The gate is the
review: `start` validates the whole set and names what is wrong if anything
is, in under a second, so go straight to it and fix what it names.

**Start from the skeleton instead of typing boilerplate:**

```
cp -r "${CLAUDE_PLUGIN_ROOT}/skills/sim/references/question-skeleton" <dir>/<slug>
```

then fill it. Copying is instant; the imports and class lines are the same
every time and typing them is seconds spent on nothing.

**Size it for one sitting, not for the permanent corpus.** The whole set,
every file included, should land near **275 lines**; sittings have shipped 600
and then 434, and every line above the budget was somebody waiting. Where it
goes:

- Problem statement: **40 lines or fewer.** Statement, one worked example,
  constraints. A candidate reads this on the clock.
- Hidden suite: **12 to 15 tests**, compact. Descriptive names, no docstrings:
  the debrief reads the name back as English, so `test_empty_filter_matches_all`
  is the documentation.
- Public samples: 3 tests.
- **Mutants: 3 or 4, each a different failure mode.** Every mutant is a full
  copy of the reference with one break, which makes them most of the tokens in
  the set, and a second mutant that fails the same way as the first proves
  nothing the gate did not already know. Distinct ways to get it wrong are the
  proof; code only, a one-line comment naming the break, no prose.

Put the topics you researched into `meta.json`. That is where the session reads
what the question covers, and it prints it before the clock starts, so a
candidate can see the sitting was built for their round rather than taking your
word for it.

**Pass those same topics as `--topic` flags too.** The metadata says what the
question covers; the flags say what you set out to cover. With both, the session
can tell them the two agree, which is a stronger claim than either alone and the
one worth making after research.

**The mutants are not optional and they are not busywork.** Each one is a
plausible wrong answer: the off-by-one, the missed edge case, the approach that
skips the hard part. The engine runs the same gate CI runs on the corpus, before
the clock starts, and refuses the question if the reference fails, the starter
passes, fewer than three mutants exist, **or any mutant survives the hidden
suite**. A surviving mutant means the suite cannot tell wrong from right, and a
grade from that suite is worthless. Strengthen the tests, never the mutant, and
try again. Do not work around a refusal.

Then start on it. This invocation is complete, exam and interview both; do not
go and check the parser:

```
# a live round with you interviewing:
python3 "${CLAUDE_PLUGIN_ROOT}/skills/sim/scripts/session.py" start \
    --format gca --questions 1 --mode interview --minutes 45 \
    --generated <dir> --company <name> \
    --topic "<researched topic>" --topic "<another>" --open

# an asynchronous exam: drop --mode and --minutes, set --questions
```

**Deliver the research findings before you write anything yourself, as a
brief, not an essay: about 150 words.** Five parts, one to three lines each:
the loop end to end; what is established against what is only reported, with
dates; the confidence in one line; the adaptation and why; which round this
sitting is, with the offer to switch. Sources as bare links at the end. Longer
is not more confident: the substance is the claims, their dates, and what
disagrees, and paragraphs around them are generation time spent on nobody.

The reason is the shape of the wait. Writing and gating takes a few minutes,
and the findings take about that long to read, so delivered first they overlap:
the candidate spends the authoring time reading what their company actually
runs, and the clock line is waiting when they finish. The first live run did it
the other way, four minutes of "made 9 edits" and then everything at once at
the end, which is the same total time experienced as twice as long. It is also
what a real process does: you are told what the round is before the problem is
put in front of you.

Close the findings with one line saying what happens next: "Writing a question
for this round now." That is the whole line. No time estimate, which is a
promise picked at random that reads as an apology when it runs over. No
narration of the steps, no "checking the format spec first", no setup talk:
that is machinery, and the findings above are what they should be reading while
you work. Say "a question", not "an original question": originality is your
obligation, not a selling point, and announcing it invites the question of what
it is being contrasted with. Then the message that starts the clock carries
only what is new: the match line the session prints, where to look first, and
your opening question as interviewer if it is a live round.

**Then go straight to `start`. Do not build a verification harness first.**
The gate runs every check in under a second and a refusal costs nothing and
names its reason, while a hand-rolled pre-check costs a minute of somebody's
wait and proves less than the gate does. The one check that is yours to do is
the expected values, below, because the gate cannot know what the right answers
are, only whether the suite discriminates.

Two things to get right while writing, both of which have gone wrong here
before. **Expected values come out of running code, in this order: write the
reference first, run it on the test inputs, paste what it printed into the
tests.** The skeleton ships `values.py` for exactly this: fill in the data and
the cases once, run it, transcribe. Never type a value from your head and check it after; the last run
lost a correction round to exactly that, and the order above makes the mistake
impossible rather than catchable. And make the hidden suite test the edge cases the
statement actually promises, not the ones the reference happens to handle.
Fixtures for input-preservation tests must be in an order sorting would disturb,
which has been the same bug four times in this repository.

**When no company is involved** ("give me a GCA mock", "let me practise"), the
pre-written corpus is the right answer: instant start, and every question in it
has been through the same gate plus human review.

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
| 5 | a session is already running | if it has already ended or expired, nothing is at stake and its results are already banked: `--force` and carry on. If it is genuinely still running, show `status` and ask before abandoning it |
| 6 | question bank problem | report it and do not improvise a question |
| 7 | environment problem | run `check` and report what it says. It names the thing that is wrong, which the failing command usually cannot |
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

## Never talk about the machinery

The candidate is here to sit an assessment, not to hear how the tool works.

**Never mention the question bank.** Not its size, not whether a question came
out of it, not whether it had something on a topic. Say "let me find out what
Shopify runs" and go and find out, rather than narrating your own filing. "The bank had nothing on
rate limiting so it drew a scheduling problem instead" is a sentence that costs
them confidence in the sitting they are about to spend an hour on, and they can
do nothing with it. If the topics you researched are not covered, the answer is
to write a question for them before starting, not to run a mismatched one and
apologise. `start --json` tells you what was uncovered; that is for you.

**Show the research as it happens.** Searching visibly is the one part of this
that is genuinely reassuring to watch, because it is the difference between a
tool that looked and a tool that guessed. Do not hide it behind a summary.

**Then say the sourcing once, in your own words.** One or two sentences: what
the company runs, how sure you are, and what you are about to sit. Then stop. Three
sentences of caveat where one would do reads as a tool with no confidence in
itself, and the third one is never the one that changes their mind. Repeating it as the clock starts, and again as a
"quick caveat" once they are in, reads as a tool with no confidence in itself,
and every extra repetition buys nothing that the first one did not.

Compare. This is wrong:

> The bank had nothing on the topics I recorded for Shopify, so it drew a
> classic scheduling problem instead. That's a more algorithm-puzzle-shaped
> than the real pairing round reportedly is. Still good practice though.

This is right:

> Shopify run a pairing round, around 80 minutes, practical rather than
> algorithmic. That's from a handful of candidate reports this year, so treat it
> as a good guess rather than gospel. I've set up 45 minutes on a problem in
> that shape. I'm your interviewer, your file is at <path>.

## After the session

Once the clock is out, run `report` and then drop the proctor voice entirely. This
is the part where being useful matters more than being strict.

Give a real debrief: what they got through, where the time went, which parts of the
approach were sound, what to drill next. Now you may look at their solutions and
talk about them properly, because the exam is over. You still do not read the hidden
tests.

**Run `debrief` as well as `report`.** `report` says what happened; `debrief`
says why. It names every hidden test each answer failed and what that test was
guarding, which is the part that turns a sitting into something they learned
from, and it is safe now precisely because the clock is out. Work through the
question it puts first: it orders by time spent, so the one at the top is the
one that cost them the sitting. For a question worth going deep on, `debrief
--question q2` prints a reference solution beside what they wrote.

Do not read the failures out as a list. Group them: three failures that are all
the empty-input case are one gap, not three, and saying so is the difference
between a report and a teacher.

**Lead with the "Where the time went" block, not with the score.** It is the only
part of the report that measures the thing the format is testing, and it is
usually where the sitting was actually lost: two thirds of the clock on one
question, or a question never opened at all. Talk about that as a decision they
made rather than a fact that befell them, because it is one they can practise.
A question they never opened may well have been one they could have solved, and
that is worth saying plainly. Do not read the timings out as a list; say what
the shape of them means.

Two things not to do. Do not soften the numbers, and do not inflate them either: a
question that timed out or never ran is a zero, and `report` already counts it that
way. And do not present the percentage as the score a real platform would give
them. It is what these particular hidden tests measured, and the scales the real
platforms report are proprietary, which `report` says out loud.

If they have sat more than one session, run `progress` as well. One sitting is a
data point and several are a shape, and the shape is usually the more useful
thing to talk about: which difficulty band they lose tests in, and how many
questions they never reached at all. Read those two rows out and build the drill
plan from them. Do not turn the percentages into a trend on their behalf. The
draw is random and the bank is small, so a better-looking session may only be an
easier one, and `progress` says so for a reason.
