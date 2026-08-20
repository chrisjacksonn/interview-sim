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
import json
import os
import shutil
import signal
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

EXIT_OK = 0
EXIT_USAGE = 2
EXIT_BANK = 6
EXIT_TIMEOUT = 8

DEFAULT_TIMEOUT = 30.0

HIDDEN_TESTS = "tests_hidden.py"
SOLUTION_NAME = "solution.py"


class _CountingResult(unittest.TestResult):
    """A TestResult that counts tests that actually passed.

    unittest offers failures and errors but no success list, and deriving
    successes by subtraction breaks whenever the number of recorded failures
    does not equal the number of failed tests.
    """

    def __init__(self):
        unittest.TestResult.__init__(self)
        self.successes = 0

    def addSuccess(self, test):
        unittest.TestResult.addSuccess(self, test)
        self.successes += 1


def execute_suite():
    """Load and run the hidden test module in the current directory. Child process only.

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
    # solution as "1 test, 1 failed" instead of "this did not import". The name
    # is a literal, not a string from the command line: this only ever runs
    # tests_hidden.
    try:
        import tests_hidden as module
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
    result = _CountingResult()
    suite.run(result)

    failing = [test.id().split(".")[-1] for test, _ in result.failures]
    erroring = [test.id().split(".")[-1] for test, _ in result.errors]
    skipped = len(result.skipped)

    # Count successes rather than subtracting failures from the total.
    # unittest records one entry per failed *assertion*, not per test, so a
    # subTest that fails five times inside two tests subtracts five and yields
    # a negative score, and a setUpClass error records one failure for a whole
    # class, scoring every test in it as passed without running any of them.
    # Neither is possible for the questions in this repository today, but this
    # is the scoring core and the gate cannot catch either.
    passed = result.successes
    if passed > total - skipped:
        passed = total - skipped
    if passed < 0:
        passed = 0

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


STALE_AFTER_SECONDS = 3600


def _sweep_stale_workdirs():
    """Remove grading directories left behind by a hard kill.

    Cleanup normally happens in a finally block, which SIGKILL and SIGTERM skip,
    so a session interrupted with Ctrl-C at the wrong moment leaves a directory
    holding a copy of a hidden suite. That is litter rather than a leak, since
    the suites are public files in the repository and the workspace is never
    touched, but it accumulates.

    Only directories older than an hour are removed, so a grading run happening
    right now in another process is never disturbed.
    """
    root = Path(tempfile.gettempdir())
    cutoff = time.time() - STALE_AFTER_SECONDS
    try:
        candidates = list(root.glob("interview-sim-grade-*"))
    except OSError:
        return
    for stale in candidates:
        try:
            if stale.is_dir() and stale.stat().st_mtime < cutoff:
                shutil.rmtree(str(stale), ignore_errors=True)
        except OSError:
            continue


def _kill_group(proc):
    """Kill the child and anything it spawned.

    proc.kill() only reaches the direct child, so a solution that leaked a
    subprocess would leave it running and holding resources after the timeout.
    os.getpgid can raise once the direct child has already exited, so the pid is
    used directly: start_new_session made it the group leader.
    """
    try:
        os.killpg(proc.pid, signal.SIGKILL)
    except (OSError, AttributeError):
        try:
            proc.kill()
        except OSError:
            pass
    try:
        proc.communicate(timeout=5)
    except (subprocess.TimeoutExpired, ValueError, OSError):
        pass


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

    _sweep_stale_workdirs()

    workdir = tempfile.mkdtemp(prefix="interview-sim-grade-")
    # The result channel is a file, not the child's stdout.
    #
    # Reading results off stdout meant any print() in the candidate's solution
    # landed in the middle of the JSON and the whole run was reported as
    # "0 of 0 hidden tests passed (0%)". A stray debug print is the single most
    # likely thing to be left in a file under time pressure, and answering it
    # with a confident zero is the worst thing this tool could do.
    #
    # It lives outside workdir so that candidate code, which runs with workdir
    # as its working directory, cannot plausibly stumble onto it.
    handle, result_file = tempfile.mkstemp(prefix="interview-sim-result-", suffix=".json")
    os.close(handle)
    try:
        shutil.copyfile(str(solution_path), str(Path(workdir) / SOLUTION_NAME))
        shutil.copyfile(str(hidden), str(Path(workdir) / HIDDEN_TESTS))

        # Its own process group, so a solution that spawns children can be killed
        # as a whole. Without this a leaked grandchild holding the pipe open
        # outlives the timeout. POSIX only: Windows rejects the argument, and
        # there the timeout falls back to killing the direct child.
        group = {"start_new_session": True} if os.name == "posix" else {}
        try:
            proc = subprocess.Popen(
                [
                    sys.executable,
                    str(Path(__file__).resolve()),
                    "--execute",
                    "--result-file",
                    result_file,
                ],
                cwd=workdir,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                **group
            )
            try:
                proc.communicate(timeout=timeout)
            except subprocess.TimeoutExpired:
                _kill_group(proc)
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
            with open(result_file, "r") as reader:
                raw = json.loads(reader.read())
        except (IOError, ValueError):
            # The child died before writing anything: a segfault, a killed
            # process, sys.exit() in the solution. Deliberately no child output
            # here. It used to echo the last line of the child's stream, which
            # after a partial write was the grader's own JSON, hidden test names
            # and all.
            return {
                "total": 0,
                "passed": 0,
                "credit": 0.0,
                "outcome": "crashed",
                "detail": "the solution stopped the test run before it finished",
            }
    finally:
        shutil.rmtree(workdir, ignore_errors=True)
        try:
            os.unlink(result_file)
        except OSError:
            pass

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
    elif passed > 0:
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
    parser.add_argument("--execute", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--result-file", default=None, help=argparse.SUPPRESS)
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

    # Child process: run the suite in cwd and hand structured results back up
    # through a file. Never stdout: the candidate's own prints go there.
    if args.execute:
        payload = json.dumps(execute_suite())
        if args.result_file:
            with open(args.result_file, "w") as handle:
                handle.write(payload)
        else:
            print(payload)
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
