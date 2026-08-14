# Recording the demos

Two different recordings, because they show two different things and only one of
them happens in a terminal.

## The terminal demo (demo.gif)

Reproducible, small, and scripted end to end:

```
brew install vhs
vhs demo.tape
```

`demo.tape` documents its own shortcuts at the top. It pins the question choice
with a seed, because selection is random and the stand-in solution has to match
whichever question came up.

## The posting demo (a screen recording)

**This is the one that should lead the README.** It is the only recording that
shows what the tool actually is: you are in your own project, you name a company,
and a real timed sitting appears in the editor you already have open. A terminal
GIF of `sim start` shows the engine, not the product.

It cannot be recorded by vhs. vhs types into a shell, and the agent loop, the
live research and an editor window filling up are not a shell. This one is a real
screen recording of a real session, which also means the research on screen is
real and takes as long as it takes.

### Setting up

```
tools/demo-project.sh
```

That builds `/tmp/checkout-service`: a small plausible project, a git repo, and
a `.claude/settings.json` turning on auto mode for that directory only. Auto mode
matters more than it sounds. Without it the take is interrupted by permission
prompts every time the proctor reads a file, and a timed sitting that pauses to
ask permission is not a timed sitting.

Open that directory in your editor, open its integrated terminal, and run
`claude` there. Turn on Do Not Disturb. Record a region rather than the whole
screen, or the result is 5120 pixels wide.

### Shot list

Aim for 50 to 70 seconds. The research is the slowest part and it is also the
most interesting, so give it room rather than cutting to the result.

| Seconds | Shot |
| --- | --- |
| 0 to 4 | The editor, showing the project. Your own files, a terminal at the bottom. It should be obvious this is somebody's actual work. |
| 4 to 9 | Type `/interview-sim:sim` and paste a job posting URL after it. Send it. |
| 9 to 35 | **The research, live.** It fetches the posting, works out the company and the role, and searches. Let the tool-use lines run. This is the part people find convincing, because they can see what it is reading. |
| 35 to 45 | It says what that company runs, with sources and a confidence, then starts the sitting. The clock and the questions appear. |
| 45 to 60 | The editor. The workspace has appeared next to `src/`, and `q1/problem.md` is open, because `--open` navigates to the problem rather than the empty starter. |
| 60 to 70 | Optional: type a few lines into `solution.py` so the last frame is somebody working, not somebody reading. |

Then convert:

```
tools/screencast-to-gif.sh recording.mov demo-posting.gif 2 60
```

The last two numbers trim it: start at 2 seconds, keep 60. `WIDTH` and `FPS` are
environment overrides if the file comes out too big. GitHub will not display a
GIF over 10MB in a README, so check the size before committing it.

### Picking a posting

Use a real posting for a company whose process is genuinely reported somewhere,
or the recording ends on the honest-but-dull outcome where the agent says it
could not establish the format and asks you to pick one. That behaviour is
correct and worth having, but it is not the thirty seconds you want representing
the project.

Do a dry run first without recording, for two reasons: to see whether that
company researches well, and because the second attempt is always tighter. There
is no cache, so the take itself still does the full search.

### Two things not to edit out

**The moment it says what it could not establish.** If it hedges the format
confidence, leave it in. That is the difference between this and the sites that
confidently name a format nobody verified, and it is the most credible ten
seconds in the recording.

**The wait.** Speeding the research up to a blur makes it look like a canned
animation. It is genuinely doing the work, and it should look like it.

### Where it goes

Once `demo-posting.gif` exists, it replaces the terminal GIF at the top of the
README and the terminal one moves down. The posting demo shows what the tool is;
the terminal demo shows the engine underneath, which is worth keeping but is not
the opening argument.

```markdown
## What it looks like

![Pasting a job posting into an editor terminal: the agent researches what that
company runs, then a timed session appears in the project with the first problem
open](demo-posting.gif)

You are in your own project. You name a company, it finds out what their screen
actually is, and a real sitting appears beside the work you already had open.

<details>
<summary>The engine underneath, without an agent driving it</summary>

![A GCA session: naming a company starts the clock, real files appear, ...](demo.gif)

</details>
```

Keep both under 10MB. GitHub silently refuses to render a README image above
that, and a broken hero image is worse than a plain heading.
