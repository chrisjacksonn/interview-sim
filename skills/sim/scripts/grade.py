#!/usr/bin/env python3
"""Hidden-test grader for interview-sim.

Runs a question's hidden suite against a candidate's solution in a throwaway
directory and reports how many tests passed.

What it deliberately does not report on the candidate-facing path: test names,
assertion messages, tracebacks. A failure rendered as
"AssertionError: {} != {'Z2': 0}" hands over the exact edge case it was testing,
and a name like test_negative_count_is_skipped is barely better. Counts only.
--detail exists for authoring and CI, where the whole point is to see which
tests moved.

The candidate's code runs in a subprocess with a timeout. That is not a security
sandbox and is not trying to be one: it is their machine and their own code. It
is there so an infinite loop fails the question instead of hanging the session,
and so an import-time crash cannot take down the engine holding the state file.

Python 3.9, standard library only.
"""

import argparse
import importlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

EXIT_OK = 0
EXIT_USAGE = 2
EXIT_BANK = 6
EXIT_TIMEOUT = 8

DEFAULT_TIMEOUT = 30.0

HIDDEN_TESTS = "tests_hidden.py"
SOLUTION_NAME = "solution.py"


def execute_suite(module_name):
    """Load and run a test module in the current directory. Child process only.

    Returns a dict rather than printing, so the parent decides what is safe to
    show. A failure to load is reported as its own outcome: an unimportable
    solution is a different situation from a wrong one, and the candidate needs
    to be told which they have.
    """
    # The child is launched by absolute path, so sys.path[0] is the scripts
    # directory, not the sandbox. Without this the test module never imports and
    # unittest hands back a single synthetic failure that looks like a real one.
    sys.path.insert(0, os.getcwd())

    # Import explicitly rather than letting the loader do it. loadTestsFromName
    # swallows an ImportError into a _FailedTest, which would report a broken
    # solution as "1 test, 1 failed" instead of "this did not import".
    try:
        module = importlib.import_module(module_name)
    except Exception as exc:  # noqa: BLE001 - any import-time failure counts
        return {
            "loaded": False,
            "load_error": type(exc).__name__,
            "total": 0,
            "passed": 0,
            "failed": 0,
            "errored": 0,
            "skipped": 0,
            "failing": [],
        }

    loader = unittest.TestLoader()
    suite = loader.loadTestsFromModule(module)
    total = suite.countTestCases()
    result = unittest.TestResult()
    suite.run(result)

    failing = [test.id().split(".")[-1] for test, _ in result.failures]
    erroring = [test.id().split(".")[-1] for test, _ in result.errors]
    skipped = len(result.skipped)
    passed = total - len(failing) - len(erroring) - skipped

    return {
        "loaded": True,
        "load_error": None,
        "total": total,
        "passed": passed,
        "failed": len(failing),
        "errored": len(erroring),
        "skipped": skipped,
        "failing": sorted(failing + erroring),
    }


def grade(question_dir, solution_path, timeout=DEFAULT_TIMEOUT):
    """Grade one solution against one question's hidden suite."""
    question_dir = Path(question_dir)
    solution_path = Path(solution_path)

    hidden = question_dir / HIDDEN_TESTS
    if not hidden.exists():
        raise SystemExit(
            "No hidden suite at %s" % (hidden,)
        )
    if not solution_path.exists():
        return {
            "total": 0,
            "passed": 0,
            "credit": 0.0,
            "outcome": "missing",
            "detail": "no solution file at %s" % (solution_path,),
        }

    workdir = tempfile.mkdtemp(prefix="interview-sim-grade-")
    try:
        shutil.copyfile(str(solution_path), str(Path(workdir) / SOLUTION_NAME))
        shutil.copyfile(str(hidden), str(Path(workdir) / HIDDEN_TESTS))

        try:
            proc = subprocess.Popen(
                [sys.executable, str(Path(__file__).resolve()), "--execute", "tests_hidden"],
                cwd=workdir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
            )
            try:
                out, err = proc.communicate(timeout=timeout)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.communicate()
                return {
                    "total": 0,
                    "passed": 0,
                    "credit": 0.0,
                    "outcome": "timeout",
                    "detail": "did not finish within %gs" % (timeout,),
                }
        except OSError as exc:
            raise SystemExit("Could not run the grader: %s" % (exc,))

        try:
            raw = json.loads(out)
        except ValueError:
            return {
                "total": 0,
                "passed": 0,
                "credit": 0.0,
                "outcome": "crashed",
                "detail": (err or out).strip().splitlines()[-1:] or ["no output"],
            }
    finally:
        shutil.rmtree(workdir, ignore_errors=True)

    if not raw["loaded"]:
        return {
            "total": 0,
            "passed": 0,
            "credit": 0.0,
            "outcome": "import_error",
            "detail": raw["load_error"],
        }

    total = raw["total"]
    passed = raw["passed"]
    credit = (float(passed) / total) if total else 0.0
    if passed == total and total:
        outcome = "pass"
    elif passed:
        outcome = "partial"
    else:
        outcome = "fail"

    return {
        "total": total,
        "passed": passed,
        "credit": round(credit, 4),
        "outcome": outcome,
        "failing": raw["failing"],
    }


def describe(report):
    """Candidate-facing summary. Counts and shape, never test identities."""
    outcome = report["outcome"]
    if outcome == "missing":
        return "No solution file found."
    if outcome == "timeout":
        return "Timed out. Something is not terminating."
    if outcome == "import_error":
        return "Solution did not import (%s). Fix that before it can be graded." % (
            report["detail"],
        )
    if outcome == "crashed":
        return "The grader could not run this solution."
    return "%d of %d hidden tests passed (%.0f%%)." % (
        report["passed"],
        report["total"],
        report["credit"] * 100,
    )


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="grade.py", description="Run a question's hidden suite against a solution."
    )
    parser.add_argument("--execute", default=None, help=argparse.SUPPRESS)
    parser.add_argument("--question", default=None, help="question directory in the bank")
    parser.add_argument("--solution", default=None, help="path to the candidate's file")
    parser.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT)
    parser.add_argument("--json", action="store_true")
    parser.add_argument(
        "--detail",
        action="store_true",
        help="include failing test names. For authoring and CI, never for a live session.",
    )
    args = parser.parse_args(argv)

    # Child process: run the suite in cwd and hand structured results back up.
    if args.execute:
        print(json.dumps(execute_suite(args.execute)))
        return EXIT_OK

    if not args.question or not args.solution:
        parser.error("--question and --solution are required")

    report = grade(args.question, args.solution, args.timeout)
    if not args.detail:
        report.pop("failing", None)

    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print(describe(report))
        if args.detail and report.get("failing"):
            print("")
            print("failing: %s" % (", ".join(report["failing"]),))

    if report["outcome"] == "timeout":
        return EXIT_TIMEOUT
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
