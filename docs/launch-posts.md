# Launch post drafts

Drafts, not schedules. Edit before posting; the star counts and dates are yours
to fill in.

Order that works: Show HN and r/ClaudeAI the same morning, r/csMajors and
r/leetcode the next day. Clear the calendar to answer comments for the first six
to eight hours, because the first hour of replies decides how the thread goes.
Tell friends it is live so they can try it and comment honestly. Never coordinate
upvotes, and do not ask anyone for a star. A star from someone who never ran it
is worth nothing to you anyway: it is the one number that can look like traction
without being any.

Post each of these as its own text, not the same text four times. Identical
copies across subreddits is what spam filters and moderators are looking for, and
these communities treat undisclosed self-promotion as spam, so say you built it
in the first line.

---

## Show HN

**Title**

> Show HN: interview-sim, timed coding-assessment practice that runs in your terminal

**Body**

I kept failing timed online assessments for reasons that had nothing to do with
whether I could solve the problems. Four questions in seventy minutes is a
different skill from four questions, and you cannot practise it on a site that
lets you take as long as you like.

So I built the format rather than the questions: a deterministic timer, real
files in your own editor, hidden tests you cannot see, and a hard stop when the
clock runs out. A correct answer submitted one second late is refused, because
that is what happens in the real thing.

The part I would actually like feedback on is the question pipeline. Every
question ships with a reference solution, a hidden suite, and a directory of
deliberately-wrong solutions. CI checks three things on every commit: the
reference passes, the untouched starter does not, and **every wrong solution is
caught by at least one hidden test**. That last check is the point. A suite that
passes everything discriminates nothing, and grading against one is worse than
not grading at all, because it tells you that you got it right when you did not.

It has already caught two of my own suites being weak. A shortest-path question
where a depth-first traversal passed everything, because every test happened to
put the target one hop from the start. And a performance test sized just small
enough that a quadratic solution squeaked in under the timeout, so it caught
nothing.

There is no score. CodeSignal's 200-600 scale is proprietary and nobody outside
can reproduce it, so the tool reports what it actually measured: which questions
you solved, how many hidden tests passed, and how the time went. A question that
timed out counts as a zero rather than being quietly dropped from the average.

Every question is original, written against public format descriptions. Nothing
is scraped, and PRs containing real assessment items are rejected.

The weakest part, since someone will find it anyway: difficulty calibration is
one person's judgement. The gate proves a question's tests can tell right from
wrong, and proves nothing about whether a question belongs in the medium slot or
the hard one. That needs candidate data I do not have yet.

Python 3, standard library only, no dependencies. Runs as an Agent Skill in
Claude Code, or as plain scripts anywhere.

[link]

---

## r/ClaudeAI

**Title**

> I built an Agent Skill that runs timed coding assessments and refuses to help you

**Body**

`/sim gca` and you get four questions, seventy minutes, and a proctor who will
clarify what a question is asking and will not tell you how to solve it.

The interesting part for this sub is what it took to make an agent behave like a
proctor rather than a helpful assistant. Two rules in SKILL.md do most of the
work:

- **Re-read the solution file every check-in.** Nothing watches the filesystem,
  so the copy in context goes stale the moment the candidate edits it. Without
  this the agent confidently discusses code from ten minutes ago.
- **Never estimate the time.** Left to itself the model infers remaining time
  from how long the conversation has been going, which is wrong and sounds
  authoritative. A script owns the clock and the agent reports its output.

Grading is a script too, and it reports counts only, never which tests failed.
A failing test's name describes the edge case it guards, so listing them hands
over the answer.

There is also an interview mode where the agent does talk: it asks how you plan
to approach it before you write anything, and hints are allowed but every one is
recorded, because solving something with two nudges is a different result from
solving it alone.

Python 3, stdlib only, no dependencies. Works in Claude Code as a plugin, and in
other agents through the Agent Skills convention.

[link]

---

## r/csMajors

**Title**

> Free offline practice for timed OAs. Original questions, no cheating tools.

**Body**

Built this because the format was what kept catching me out, not the problems.

- Four questions, seventy minutes, all unlocked, exactly like the real thing
- Or one project across four levels, where each level unlocks by passing the
  previous one and earlier levels keep being tested, so breaking level 1 while
  adding level 4 costs you
- Real files in your own editor, hidden tests, hard stop at time
- Nineteen questions and four projects, all original
- `progress` shows what your sittings add up to: which difficulty band you lose
  tests in, and how many questions you never reached

Two things it deliberately does not do.

**It does not give you a score.** The 200-600 scale is proprietary and no
third-party tool can reproduce it. Anything claiming to predict it is guessing.
This tells you which questions you solved and how many hidden tests passed.

**It has nothing to do with cheating.** Offline, no contact with any assessment
platform, no browser anything. It is practice equipment.

Free, MIT, no signup, no account.

[link]

---

## Notes for whoever posts these

- Do not claim it predicts a real score. It does not and saying so is the fastest
  way to lose the thread.
- If someone points out the hidden tests are readable in the repo: yes, and it
  says so in the README. They are hidden from the session, not from you.
- If someone asks why not just use LeetCode with a timer: concede most of it.
  For reps on algorithms, LeetCode with a timer gets you most of the way at zero
  setup, and saying otherwise makes you look like you are selling something. What
  it does not give you is the triage of four questions at once, the not-finishing,
  and above all the ICA shape, where level 4 makes you refactor code levels 1 to 3
  still have to pass. Nothing else practises that, and it is the level people
  report failing.
- Difficulty calibration is one person's judgement and there is no candidate data
  behind it. Say so if asked. It is the weakest part.
