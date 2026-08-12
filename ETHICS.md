# Ethics

interview-sim is practice equipment. It exists so that the format of a timed
assessment stops being the thing that surprises you, and the only thing left to
be hard is the problem itself.

## What this tool does not do

**It does not touch real assessments.** The engine runs entirely offline against
questions stored in this repository. It opens no network connection, and the
scripts import nothing that could.

It does not interact with any assessment platform, proctoring system, browser
session, or exam environment, and it never will. There is no feature request that
changes this.

Three honest caveats.

The agent is not offline, and the usual way to run this is inside one. If you use the skill through Claude Code or a similar
tool, your prompts, the problem text, and whatever you show it of your code go to
that provider like anything else you type there. The grading and the clock are
local either way, and the scripts work with no agent at all.

The agent can also read and search on your behalf, when you ask it to. Paste a
job posting and it will fetch that page to work out which company it is; name a
company the preset table does not have and it can go looking for what their
current screen is. That is the agent doing what you asked, and what it finds is
recorded with its sources, its date, and a confidence, and is labelled as
researched rather than reviewed every single time it is used. What it must never
do is come back with a company's actual questions. Question text found while
researching is a signal about format and topic, and copying it would be both
someone else's property and a worse tool: memorising answers is not practice.

And the agent can write questions for you, for a company or a posting the bank
has nothing for. Those are original problems it invents, never real assessment
items, and they are checked to be answerable before the clock starts. What they
have not had is the mutation gate every bank question passes, so their grading is
less trustworthy, and the tool says so out loud when a session uses them.

**It is not a cheating tool.** Nothing here is designed to be undetectable,
because there is nothing to detect: the tool has no contact with the systems it
is modelled on. If you are looking for something to use during a real
assessment, this is the wrong repository, and no fork of it will be maintained
here.

**It does not reproduce real questions.** Every question is written from scratch
against a public format description. Real assessment items are not copied,
paraphrased, or reconstructed, and contributions containing them are rejected.
If you recognise a question here as a real one, open an issue and it will be
replaced.

## On the hidden tests

The hidden test suites are in this repository. Anyone can read them. That is
unavoidable in open source, and encrypting them with a key that ships alongside
them would be theatre rather than security.

So they are not hidden from you, they are only hidden from the session
workspace. The tool does not put them in front of you, does not describe them,
and does not let the agent proctoring your session read them. Going and looking
anyway only costs you the practice you came for.

## On the scoring

The score is not the real score. CodeSignal's 200-600 scale is proprietary and
calibrated against data that is not public, so this tool does not attempt to
reproduce it. What it reports is what it actually measured: which tests passed,
which did not, and how the time went. That is the honest version, and it is more
useful for deciding what to practise next.

## Trademarks

CodeSignal and LeetCode are trademarks of their respective owners. They are
referenced here only to describe the format this tool imitates. interview-sim is
not affiliated with, endorsed by, or connected to either company.
