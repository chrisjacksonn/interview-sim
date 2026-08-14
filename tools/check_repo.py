#!/usr/bin/env python3
"""Fail if the repository carries anything that belongs to one machine.

This exists because two files shipped in the repository for two days. `current`
and `history.json` were committed by accident when session workspaces moved into
the working directory. `current` held an absolute path from the author's laptop.
`history.json` was worse: it told every fresh clone that four questions had
already been served, so a new user's first sitting quietly drew around four
questions it had never actually shown them.

CI could not have caught it, and that is the interesting part. Every job runs
from a checkout that already contains the offending files, so the environment
doing the validating was never the environment the user gets. Nothing was
failing. The tool worked perfectly, for the author.

These checks are cheap, so they run on the tracked file list rather than on a
clone. The workflow does the real clone separately: this catches the cause, that
catches the symptom.

Python 3.9, standard library only.
"""

import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

# Directory names that only ever exist because somebody sat a session.
SESSION_DIRS = ("interview-sim-sessions", "sessions", "sim-sessions", ".sim")
# Files a session writes at its root. Harmless looking, and one of them silently
# changes what a new install draws.
SESSION_FILES = ("history.json", "researched.json", "state.json")
# A path into somebody's home directory. Nothing checked in should contain one:
# not in a doc, not in an example, not in a fixture.
HOME_PATH = re.compile(r"/(?:Users|home)/[A-Za-z0-9._-]+/")
# Text that is not source. A .gif has no business being decoded.
SKIP_SUFFIXES = (".gif", ".png", ".jpg", ".jpeg", ".ico", ".pdf", ".zip")


def tracked():
    out = subprocess.check_output(
        ["git", "-C", str(REPO), "ls-files", "-z"], universal_newlines=True
    )
    return [Path(name) for name in out.split("\0") if name]


def main(argv=None):
    try:
        files = tracked()
    except (subprocess.CalledProcessError, OSError) as exc:
        print("Could not list tracked files: %s" % (exc,))
        return 1

    if not files:
        print("No tracked files found.")
        return 1

    failures = []
    for path in files:
        parts = set(path.parts)
        for name in SESSION_DIRS:
            if name in parts:
                failures.append(
                    "%s is inside %s/, which only exists because a session ran "
                    "there. A clone should never carry one." % (path, name)
                )
                break
        else:
            if path.name in SESSION_FILES:
                failures.append(
                    "%s is session state. Committing it hands every fresh clone "
                    "somebody else's history." % (path,)
                )

        if path.suffix.lower() in SKIP_SUFFIXES:
            continue
        try:
            text = (REPO / path).read_text()
        except (UnicodeDecodeError, OSError):
            continue
        found = HOME_PATH.search(text)
        if found:
            failures.append(
                "%s contains an absolute home path (%s). It is true on exactly "
                "one machine." % (path, found.group(0))
            )

    for problem in failures:
        print("  FAIL  %s" % (problem,))
    if failures:
        print("")
        print("%d problem(s). A fresh clone would not be clean." % (len(failures),))
        return 1
    print("%d tracked file(s), nothing machine-specific." % (len(files),))
    return 0


if __name__ == "__main__":
    sys.exit(main())
