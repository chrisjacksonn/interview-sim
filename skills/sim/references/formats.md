# Format specifications

What the questions in this repository are calibrated against. These are public
descriptions of assessment *shape*, not of any particular question, and they are
the only thing about real assessments this project uses.

## GCA-style

Four questions, seventy minutes, all available from the moment the timer starts
so you choose your own order. Scored on correctness and speed.

Difficulty ramp, which is what `slot` in `meta.json` encodes:

| Slot | Difficulty | Shape | Target time |
| --- | --- | --- | --- |
| 1 | warmup | strings, loops, a dictionary. Should be finished quickly | 8-12 min |
| 2 | medium | hash maps, sorting, sliding windows, prefix sums | 15-18 min |
| 3 | medium | graphs, heaps, two-dimensional dynamic programming | 18-22 min |
| 4 | hard | advanced DP, greedy with a proof, optimisation under a size limit | 22-28 min |

The times add to more than seventy minutes on purpose. Not finishing everything
is the normal experience and part of what the format measures is triage.

**Calibration rules for slots 1 and 2.** A candidate who knows the technique
should not be slowed down by the statement. Keep the input shape simple, state
every edge case explicitly, and do not hide a second problem inside the parsing.

**Calibration rules for slots 3 and 4.** The naive solution must be reachable and
must be too slow. If a quadratic answer passes the hidden suite, the question is
a slot-2 question wearing a slot-4 label. Size the largest test so the intended
complexity finishes comfortably and the naive one cannot, then check that with an
actual mutant rather than by reasoning about it.

## ICA-style

One project, ninety minutes, four levels that unlock in order. You extend a
single file, and every level re-runs the tests from the levels below it.

| Level | Shape |
| --- | --- |
| 1 | basic operations with corner cases: create, read, delete, refuse duplicates |
| 2 | reporting over the level 1 data: counts, totals, ranking with a tie-break |
| 3 | a feature added without disturbing existing calls, whether by an optional argument or by new methods over the same data |
| 4 | an extension that invalidates a design decision from level 1, with everything earlier still required to pass |

**Level 4 is the level that matters.** It must make the obvious level 1 data
model wrong. In this repository: one parcel per locker becomes several, one
account id becomes mergeable and reusable, one size per file becomes a history.
Each of those breaks an assumption a reasonable candidate would have baked in.

Weight level 4's hidden suite toward re-checking levels 1 to 3 under the new
model, because the common failure is getting the new feature working while
quietly breaking the old behaviour.

## What is not modelled

- **The real scoring.** The 200-600 scale is proprietary and is not reproduced
  here. See METHODOLOGY.md.
- **Proctoring.** No webcam, no screen capture, no browser lockdown, and none of
  it will ever be added. See ETHICS.md.
- **The in-browser editor.** You work in real files in your own editor, which is
  more pleasant and slightly easier than the real thing. Bear that in mind when
  reading your own times.
- **Languages other than Python.**

## Sources

These describe the format only. No question content comes from any of them.

- CodeSignal's knowledge base on GCA structure:
  https://support.codesignal.com/hc/en-us/articles/360040370853-What-should-I-expect-when-I-take-the-General-Coding-Assessment-GCA-and-how-is-it-structured
- The platform's published customer list, kept as a citation only, since the
  company table it once fed has been removed:
  https://codesignal.com/customers/
- A community-maintained record of online assessment formats:
  https://github.com/Leader-board/OA-and-Interviews
