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

The part that changed my mind about the whole design: when you name a company,
it does not draw from a fixed pool. The agent researches what that company's
screen actually is (candidate reports, dated, with the sources shown), writes an
original question shaped like that round, and the engine refuses to start the
clock until that question proves it can grade. I added this after watching the
fixed pool hand someone a heap problem for a practical frontend round. A
question bank is a promise to be generic.

The part I would actually like feedback on is the gate. Every question, shipped
or written on the spot, must carry a reference solution, a hidden suite, and
deliberately-wrong solutions. Three checks before anything is sat: the reference
passes, the untouched starter does not, and **every wrong solution is caught by
at least one hidden test**. Shipped questions clear it in CI on every commit;
generated ones clear the identical checks before the clock starts, and a
question whose suite lets a wrong answer survive is refused with the reason. A
suite that passes everything discriminates nothing, and grading against one is
worse than not grading at all, because it tells you that you got it right when
you did not.

It keeps catching my own suites being weak, which is the only reason I trust it.
A shortest-path question where a depth-first traversal passed everything,
because every test happened to put the target one hop from the start. A
performance test sized just small enough that a quadratic solution squeaked in
under the timeout, so it caught nothing.

The best one was a rolling-median question. The usual way to get that wrong is
to keep the window sorted and then drop its front, which removes the smallest
value rather than the one that actually slid out of the window. Twenty hidden
tests, and not one of them caught it: in every case I had written, the departing
reading happened to also be the smallest, so the bug was invisible. The question
had been sitting in the bank looking tested. `solve([9, 0, 9], 2)` separates
them, and now it is in the suite.

Two of my "the input must not be modified" tests had the same problem from the
other direction: the fixture was already in sorted order, so a solution that
sorted the caller's list in place looked like it had left it alone.

There is no score. The scales the real platforms report are proprietary and
nobody outside can reproduce them, so the tool reports what it actually measured: which questions
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

> Free practice for timed OAs, in your own editor. Original questions, no cheating tools.

**Body**

Built this because the format was what kept catching me out, not the problems.

- Four questions, seventy minutes, all unlocked, exactly like the real thing
- Or one project across four levels, where each level unlocks by passing the
  previous one and earlier levels keep being tested, so breaking level 1 while
  adding level 4 costs you
- Real files in your own editor, hidden tests, hard stop at time
- Name a company and it researches what their screen actually is, then writes
  an original question for that round; it will not start the clock on a
  question that has not proved it can grade
- Twenty-two pre-written questions and four projects for instant general reps,
  all original
- The report breaks down where your time actually went, per question, so a
  sitting lost to bad triage says so instead of just showing you a low score
- `progress` shows what your sittings add up to: which difficulty band you lose
  tests in, and how many questions you never reached

Two things it deliberately does not do.

**It does not give you a score.** The scales the real platforms report are
proprietary and no third-party tool can reproduce them. Anything claiming to
predict one is guessing. This tells you which questions you solved and how many
hidden tests passed.

**It has nothing to do with cheating.** The engine opens no network connection,
and nothing touches any assessment platform. It is practice equipment.

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
  and above all the levelled project, where level 4 makes you refactor code levels 1 to 3
  still have to pass. Nothing else practises that, and it is the level people
  report failing.

  The concrete version of that answer is the time breakdown. A timer tells you
  that you ran out. It does not tell you that two thirds of the hour went on
  question two and question four was never opened, which is the actual reason
  the sitting went the way it did and the thing you would change next time.
- Difficulty calibration is one person's judgement and there is no candidate data
  behind it. Say so if asked. It is the weakest part.
