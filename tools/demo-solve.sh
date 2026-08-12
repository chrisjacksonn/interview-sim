#!/bin/sh
# Drop a nearly-correct solution into q1 of the current demo session.
#
# Used only by demo.tape, to stand in for the twenty minutes of work a real
# candidate would do between starting and submitting. It reads the question the
# slot actually dealt out of state.json and takes that question's first mutant,
# so it keeps working whichever question comes up rather than depending on a
# hardcoded path.
#
# Lives here rather than inline in the tape because vhs's Type directive cannot
# carry escaped quotes, and picking the file out of JSON needs them.
set -e

W=$(cat "$INTERVIEW_SIM_HOME/current")
QID=$(grep -o '"source": "[^"]*"' "$W/.sim/state.json" | head -1 | cut -d'"' -f4)

# Basic-tier questions ship no mutants, so there is nothing to stage and the
# tape would otherwise submit an untouched starter and score zero.
if [ ! -d "$BANK/$QID/mutants" ]; then
    echo "demo-solve: $QID ships no mutants, nothing to stage." >&2
    echo "Pin a question that has them with --seed in demo.tape." >&2
    exit 1
fi

MUTANT=$(ls "$BANK/$QID/mutants" | head -1)
cp "$BANK/$QID/mutants/$MUTANT" "$W/q1/solution.py"
