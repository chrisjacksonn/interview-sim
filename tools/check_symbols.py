#!/usr/bin/env python3
"""Fail on a top-level name defined more than once in the same module.

This exists because of a real bug rather than as a matter of taste. `session.py`
carried `age_phrase`, `record_research` and `command_learn` each defined twice.
The first two pairs were identical copies, so nothing broke. `command_learn` had
diverged, and the version Python actually kept was the *stale* one, still
describing a company table that had been deleted two versions earlier, while the
refactored version that shared code with `start --source` sat above it,
shadowed and unreachable.

Nothing failed. No test caught it. No test could have: both definitions parse,
both import, and the file runs exactly as if the dead one were not there. It was
found by reading a function index, which is not a repeatable process.

Only module-level definitions count. Methods sharing a name across different
classes are fine, and so is a definition nested inside `if` or `try`, which is
how conditional fallbacks are written.

Python 3.9, standard library only.
"""

import argparse
import ast
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

# Everything written in this repository. Question files are excluded on purpose:
# a bank question and its mutants deliberately define the same entry point, which
# is the whole point of a mutant.
TARGETS = (
    "skills/sim/scripts/*.py",
    "tools/*.py",
    "tests/*.py",
)


def duplicates(path):
    """Top-level names bound more than once, with the lines they were bound on."""
    try:
        tree = ast.parse(path.read_text())
    except SyntaxError as exc:
        return [("<unparseable>", str(exc))]

    seen = {}
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            seen.setdefault(node.name, []).append(node.lineno)
        elif isinstance(node, ast.Assign):
            # Constants shadow just as silently as functions do, and a second
            # CONFIDENCE_LEVELS would be just as hard to spot by eye.
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id.isupper():
                    seen.setdefault(target.id, []).append(node.lineno)

    return [(name, lines) for name, lines in sorted(seen.items()) if len(lines) > 1]


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="check_symbols.py", description=__doc__.splitlines()[0]
    )
    parser.add_argument("paths", nargs="*", help="files to check (default: the repo)")
    args = parser.parse_args(argv)

    if args.paths:
        files = [Path(p).resolve() for p in args.paths]
    else:
        files = sorted(
            path for pattern in TARGETS for path in REPO.glob(pattern)
        )

    if not files:
        print("No files to check.")
        return 1

    failures = 0
    for path in files:
        try:
            shown = path.relative_to(REPO)
        except ValueError:
            # An explicit path outside the repo, which is how this gets pointed
            # at an old revision to check it still catches what it was built for.
            shown = path
        for name, lines in duplicates(path):
            failures += 1
            where = ", ".join(str(line) for line in lines)
            print(
                "  FAIL  %s: %r defined %d times (lines %s). The last one wins "
                "and the others are unreachable."
                % (shown, name, len(lines), where)
            )

    if failures:
        print("")
        print("%d shadowed top-level definition(s)." % (failures,))
        return 1
    print("%d file(s), no shadowed top-level definitions." % (len(files),))
    return 0


if __name__ == "__main__":
    sys.exit(main())
