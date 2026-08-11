#!/usr/bin/env python3
"""Quality gate for the question bank.

Every question has to earn its place by passing this, and CI runs it on every
commit. Development tooling, deliberately outside skills/ so it does not ship to
users who install the skill.

The gate is in two halves. The first is obvious: the reference solution must
pass the hidden suite, or the question is unanswerable. The second is the one
that actually matters: deliberately-broken solutions must FAIL the hidden suite.
A suite that passes everything discriminates nothing, and a question graded by
such a suite is worse than no question, because it tells the candidate they got
it right when they did not.

So each question ships a mutants/ directory. Every file in it is a plausible
wrong answer, and every one of them must be caught by at least one hidden test.
That is mutation testing pointed at my own test suites.

Python 3.9, standard library only.
"""

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
QUESTIONS = REPO / "skills" / "sim" / "questions"
sys.path.insert(0, str(REPO / "skills" / "sim" / "scripts"))

import grade  # noqa: E402  - path is set up immediately above

REQUIRED_FILES = (
    "meta.json",
    "problem.md",
    "starter.py",
    "tests_public.py",
    "tests_hidden.py",
    "reference.py",
)
REQUIRED_META = ("id", "slot", "difficulty", "title")
MIN_MUTANTS = 3
TIMEOUT = 30.0


class Failure(Exception):
    pass


def check_files(question):
    for name in REQUIRED_FILES:
        if not (question / name).exists():
            raise Failure("missing %s" % (name,))


def check_meta(question):
    try:
        with open(str(question / "meta.json")) as handle:
            meta = json.load(handle)
    except ValueError as exc:
        raise Failure("meta.json is not valid JSON: %s" % (exc,))
    for key in REQUIRED_META:
        if key not in meta:
            raise Failure("meta.json has no %r" % (key,))
    if meta["id"] != question.name:
        raise Failure(
            "meta.json id is %r but the directory is %r" % (meta["id"], question.name)
        )
    return meta


def check_reference(question):
    """The reference must pass the hidden suite outright."""
    report = grade.grade(question, question / "reference.py", TIMEOUT)
    if report["outcome"] != "pass":
        raise Failure(
            "reference solution scores %d/%d (%s)"
            % (report["passed"], report["total"], report["outcome"])
        )
    return report["total"]


def check_public_suite(question):
    """The samples must be satisfiable too, or they mislead during the session."""
    report = grade.grade(question, question / "reference.py", TIMEOUT)
    if report["total"] == 0:
        raise Failure("hidden suite contains no tests")
    public = question / "tests_public.py"
    if "def test_" not in public.read_text():
        raise Failure("tests_public.py contains no tests")


def check_starter_fails(question):
    """An unfilled starter that passes means the question asks for nothing."""
    report = grade.grade(question, question / "starter.py", TIMEOUT)
    if report["outcome"] == "pass":
        raise Failure("the untouched starter passes the hidden suite")


def check_mutants(question):
    """Every plausible wrong answer must be caught by at least one hidden test."""
    directory = question / "mutants"
    if not directory.is_dir():
        raise Failure("no mutants/ directory")
    mutants = sorted(p for p in directory.glob("*.py") if not p.name.startswith("_"))
    if len(mutants) < MIN_MUTANTS:
        raise Failure(
            "only %d mutants, need at least %d" % (len(mutants), MIN_MUTANTS)
        )

    survivors = []
    caught = []
    for mutant in mutants:
        report = grade.grade(question, mutant, TIMEOUT)
        if report["outcome"] == "pass":
            survivors.append(mutant.name)
        else:
            caught.append((mutant.name, report["passed"], report["total"]))
    if survivors:
        raise Failure(
            "these wrong answers passed the hidden suite: %s" % (", ".join(survivors),)
        )
    return caught


def check_question(question, verbose):
    check_files(question)
    meta = check_meta(question)
    total = check_reference(question)
    check_public_suite(question)
    check_starter_fails(question)
    caught = check_mutants(question)

    if verbose:
        print("    %d hidden tests, reference passes all" % (total,))
        for name, passed, out_of in caught:
            print("    caught %-22s %d/%d" % (name, passed, out_of))
    return {"id": meta["id"], "hidden_tests": total, "mutants": len(caught)}


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="qa.py", description="Validate every question in the bank."
    )
    parser.add_argument("--question", default=None, help="check only this directory")
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args(argv)

    if args.question:
        targets = [Path(args.question).resolve()]
    else:
        targets = sorted(
            path
            for path in QUESTIONS.glob("*/*")
            if path.is_dir() and not path.name.startswith("_")
        )

    if not targets:
        print("No questions found under %s" % (QUESTIONS,))
        return 1

    failures = []
    for question in targets:
        label = "%s/%s" % (question.parent.name, question.name)
        try:
            check_question(question, verbose=not args.quiet)
        except Failure as exc:
            failures.append((label, str(exc)))
            print("  FAIL  %s: %s" % (label, exc))
        else:
            print("  ok    %s" % (label,))

    print("")
    if failures:
        print("%d of %d questions failed the gate." % (len(failures), len(targets)))
        return 1
    print("%d question(s) passed the gate." % (len(targets),))
    return 0


if __name__ == "__main__":
    sys.exit(main())
