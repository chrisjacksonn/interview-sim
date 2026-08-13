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

The flow that starts on a job site and ends with files in your editor cannot be
recorded by vhs. vhs types into a shell; a browser and an editor window are not
in a shell. This one is a real screen recording of a real session.

Record with Cmd+Shift+5 on macOS (or QuickTime, File > New Screen Recording).
Before you start: turn on Do Not Disturb, close the tabs you do not want in the
frame, hide the bookmarks bar, and record a region rather than the whole screen
so the result is not 5120 pixels wide.

Then convert:

```
tools/screencast-to-gif.sh recording.mov demo-posting.gif 2 40
```

The last two numbers trim it: start at 2 seconds, keep 40. `WIDTH` and `FPS` are
environment overrides if the file comes out too big.

### Shot list

Aim for about 40 seconds. Roughly:

| Seconds | Shot |
| --- | --- |
| 0 to 5 | The posting open in a browser. Copy the URL. |
| 5 to 10 | Paste it into Claude Code after the skill command. |
| 10 to 20 | The agent reads it, names the company, and says what the table knows, confidence included. |
| 20 to 28 | It starts the session. The clock and the four questions appear. |
| 28 to 40 | The editor, with the workspace open and `q1/problem.md` on screen. |

### One thing to get right

There is no company table any more, so the agent has to research the company on
camera before it can start anything. Either let that happen and keep the take
long enough to show it, which is the honest version and the more interesting
one, or pick a company you have already looked up in that session so the search
does not repeat.

Do not edit out the moment where it says what it could not establish. That is
the difference between this and the sites that will confidently name a format
they have never verified.
