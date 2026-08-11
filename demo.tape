# vhs tape for the README demo.
#
#   brew install vhs
#   vhs demo.tape
#
# Produces demo.gif. Keep it short: the point is that a real clock starts and
# real files appear, not a tour of every subcommand.
#
# Uses a scratch sessions directory so recording does not disturb your own
# sessions, and --seed so the questions are the same every take.

Output demo.gif

Set Shell "bash"
Set FontSize 15
Set Width 1100
Set Height 640
Set Padding 18
Set Theme "Catppuccin Mocha"
Set TypingSpeed 45ms

Hide
Type "export INTERVIEW_SIM_HOME=$(mktemp -d)" Enter
Type "export SIM=skills/sim/scripts/session.py" Enter
Type "clear" Enter
Show

Type "# a real 70 minute assessment, in real files, on a real clock"
Sleep 1200ms
Enter
Sleep 400ms

Type "python3 $SIM start --format gca --seed 7"
Sleep 500ms
Enter
Sleep 3500ms

Type "cd $(cat $INTERVIEW_SIM_HOME/current)/q1 && ls"
Sleep 400ms
Enter
Sleep 2000ms

Type "# solution.py is yours. the hidden tests are not here."
Sleep 1500ms
Enter
Sleep 400ms

Type "python3 $SIM status"
Sleep 400ms
Enter
Sleep 3000ms

Type "# submit tells you how many hidden tests passed, and nothing else"
Sleep 1800ms
Enter
Sleep 400ms

Type "python3 $SIM submit --question q1"
Sleep 400ms
Enter
Sleep 3500ms

Sleep 2000ms
