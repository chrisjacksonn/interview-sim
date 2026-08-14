# vhs tape for the README demo.
#
#   brew install vhs
#   cd /path/to/interview-sim
#   vhs demo.tape
#
# Produces demo.gif in the repository root. Run it from there.
#
# The shape: name a company, get a real assessment in real files beside the work
# you are already doing, on a real clock. Submit, get back a number and nothing
# else. One command to sitting it.
#
# It records from a directory standing in for whatever project the user happens
# to be in, because that is where sessions are built now, and seeing them land
# next to your own work is half the point.
#
# `sim` is the shell function the tool writes into every session README, so the
# commands on screen are the ones a real user types. The one difference is in
# the hidden preamble below: this wrapper pins --seed on start. The tool picks
# questions at random, and the stand-in solution has to match whichever question
# came up, so the recording has to be reproducible even though a real session is
# not. Nothing else about the run is arranged.
#
# tools/demo-solve.sh drops a nearly-correct solution into q1, standing in for
# the twenty minutes of work a real candidate would do there. It runs on screen
# and says what it is, rather than being hidden: vhs keeps hidden commands in the
# terminal buffer anyway, so they reappear the moment recording resumes, and a
# visible line the viewer can read beats a half-hidden one they cannot.
#
# There is exactly one typed comment in the recording, and it is that one. The
# demo used to open with a caption explaining that you are in your own project,
# which put a sentence of narration in front of the thing people came to see and
# delayed the first command by several seconds. The prompt says which directory
# this is and the output says the rest, so the captions were doing work the
# screen already did. The surviving one is not narration, it is a disclosure:
# without it the recording looks like the tool solved the question itself.

Output demo.gif

Set Shell "bash"
Set FontSize 15
Set Width 1200
Set Height 700
Set Padding 18
Set Theme "Catppuccin Mocha"
Set TypingSpeed 40ms

Hide
Type "REPO=$PWD" Enter
Type "export BANK=$REPO/skills/sim/questions" Enter
Type "SIMPATH=$REPO/skills/sim/scripts/session.py" Enter
Type 'sim() { if [ "$1" = start ]; then shift; python3 $SIMPATH start --seed 2 "$@"; else python3 $SIMPATH "$@"; fi; }' Enter
Type "rm -rf /tmp/checkout-service && mkdir -p /tmp/checkout-service && cd /tmp/checkout-service" Enter
Type 'export PS1="checkout-service $ "' Enter
Type "clear" Enter
Show

Type "sim start --company capital-one --format gca"
Sleep 600ms
Enter
Sleep 4200ms

Type "ls interview-sim-sessions/*/q1"
Sleep 400ms
Enter
Sleep 2400ms

Type "# now you write q1/solution.py. this demo skips that part:"
Sleep 2200ms
Enter
Sleep 300ms

Type "bash $REPO/tools/demo-solve.sh"
Sleep 500ms
Enter
Sleep 1200ms

Type "sim submit --question q1"
Sleep 500ms
Enter
Sleep 4200ms

Type "sim status"
Sleep 400ms
Enter

Sleep 4000ms
