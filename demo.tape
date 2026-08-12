# vhs tape for the README demo.
#
#   brew install vhs
#   cd /path/to/interview-sim
#   vhs demo.tape
#
# Produces demo.gif in the repository root. Run it from there.
#
# Keep it short. The point is that a real clock starts, real files appear, and
# submitting gives you a number and nothing else. Not a tour of every subcommand.
#
# The hidden block does three things: sends sessions to a scratch directory so
# recording cannot disturb your own, resolves the script to an absolute path
# because the demo cd's into the session directory where a relative one stops
# resolving, and drops in a nearly-correct solution so the last frame shows
# partial credit instead of a zero from an untouched starter.
#
# `sim` is the shell function the tool writes into every session README, so the
# demo shows the same commands a real user would type.
#
# --seed 7 deals run-compression as q1 every time, which is why the solution
# path below can be hardcoded. If the bank changes enough that seed 7 deals
# something else, this tape needs updating; running it will make that obvious.

Output demo.gif

Set Shell "bash"
Set FontSize 15
Set Width 1100
Set Height 640
Set Padding 18
Set Theme "Catppuccin Mocha"
Set TypingSpeed 45ms

Hide
Type "export INTERVIEW_SIM_HOME=/tmp/interview-sim-demo && rm -rf $INTERVIEW_SIM_HOME" Enter
Type "SIMPATH=$PWD/skills/sim/scripts/session.py" Enter
Type 'sim() { python3 $SIMPATH "$@"; }' Enter
Type "export MUTANT=$PWD/skills/sim/questions/gca/run-compression/mutants/compresses_twos.py" Enter
Type "sim start --format gca --seed 7 >/dev/null 2>&1" Enter
Type "export W=$(cat $INTERVIEW_SIM_HOME/current)" Enter
Type "cp $MUTANT $W/q1/solution.py" Enter
Type "clear" Enter
Show

Type "# a real 70 minute assessment, in real files, on a real clock"
Sleep 1200ms
Enter
Sleep 400ms

Type "sim status"
Sleep 500ms
Enter
Sleep 3200ms

Type "cd $W/q1 && ls"
Sleep 400ms
Enter
Sleep 2000ms

Type "# solution.py is yours. the hidden tests are not here."
Sleep 1600ms
Enter
Sleep 500ms

Type "# submit tells you how many hidden tests passed, and nothing else"
Sleep 1900ms
Enter
Sleep 400ms

Type "sim submit --question q1"
Sleep 400ms
Enter
Sleep 3800ms

Type "# which five failed is the exercise"
Sleep 1800ms
Enter

Sleep 2500ms
