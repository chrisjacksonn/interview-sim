# vhs tape for the README demo.
#
#   brew install vhs
#   cd /path/to/interview-sim
#   vhs demo.tape
#
# Produces demo.gif in the repository root. Run it from there.
#
# The shape: name a company, get a real assessment in real files on a real
# clock, submit, get back a number and nothing else. One command to sitting it.
#
# `sim` is the shell function the tool writes into every session README, so the
# commands on screen are the ones a real user types.
#
# tools/demo-solve.sh drops a nearly-correct solution into q1, standing in for
# the twenty minutes of work a real candidate would do there. It runs on screen
# and says what it is, rather than being hidden: vhs keeps hidden commands in the
# terminal buffer anyway, so they reappear the moment recording resumes, and a
# visible line the viewer can read beats a half-hidden one they cannot.

Output demo.gif

Set Shell "bash"
Set FontSize 15
Set Width 1200
Set Height 700
Set Padding 18
Set Theme "Catppuccin Mocha"
Set TypingSpeed 40ms

Hide
Type "export INTERVIEW_SIM_HOME=/tmp/interview-sim-demo && rm -rf $INTERVIEW_SIM_HOME" Enter
Type "export BANK=$PWD/skills/sim/questions" Enter
Type "SIMPATH=$PWD/skills/sim/scripts/session.py" Enter
Type 'sim() { python3 $SIMPATH "$@"; }' Enter
Type "clear" Enter
Show

Type "# name the company you are interviewing with"
Sleep 1300ms
Enter
Sleep 300ms

Type "sim start --preset capital-one"
Sleep 600ms
Enter
Sleep 5200ms

Type "# real files in your editor, and the hidden tests are not among them"
Sleep 2000ms
Enter
Sleep 300ms

Type "ls /tmp/interview-sim-demo/*/q1"
Sleep 400ms
Enter
Sleep 2400ms

Type "# now you write q1/solution.py. this demo skips that part:"
Sleep 2200ms
Enter
Sleep 300ms

Type "bash tools/demo-solve.sh"
Sleep 500ms
Enter
Sleep 1200ms

Type "sim submit --question q1"
Sleep 500ms
Enter
Sleep 4200ms

Type "# which ones failed is the exercise"
Sleep 2000ms
Enter

Sleep 2500ms
