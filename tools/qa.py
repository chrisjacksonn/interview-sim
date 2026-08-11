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
# ICA projects are one evolving file across several gated levels, so the
# per-level material lives in levelN/ and there is a single starter and
# reference at the top.
REQUIRED_ICA_FILES = ("meta.json", "starter.py", "reference.py")
REQUIRED_ICA_LEVEL_FILES = ("problem.md", "tests_public.py", "tests_hidden.py")
REQUIRED_META = ("id", "slot", "difficulty", "title")
REQUIRED_ICA_META = ("id", "levels", "title")
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
        elif report["total"]:
            caught.append((mutant.name, "%d/%d" % (report["passed"], report["total"])))
        else:
            # No tests ran at all: the mutant hung or would not import. Still
            # caught, but "0/0" reads like a suite that did not execute.
            caught.append((mutant.name, report["outcome"]))
    if survivors:
        raise Failure(
            "these wrong answers passed the hidden suite: %s" % (", ".join(survivors),)
        )
    return caught


def level_dirs(project):
    return sorted(project.glob("level*"), key=lambda p: int(p.name[5:]))


def check_ica(project, verbose):
    """Validate a multi-level ICA project.

    Same two halves as a GCA question, applied per level, plus the thing that
    makes ICA different: the reference has to satisfy every level at once, since
    the candidate is extending one file rather than starting fresh each time. A
    reference that passes level 4 but broke level 1 would let a question ship
    that punishes the candidate for doing exactly what was asked.
    """
    for name in REQUIRED_ICA_FILES:
        if not (project / name).exists():
            raise Failure("missing %s" % (name,))

    with open(str(project / "meta.json")) as handle:
        meta = json.load(handle)
    for key in REQUIRED_ICA_META:
        if key not in meta:
            raise Failure("meta.json has no %r" % (key,))
    if meta["id"] != project.name:
        raise Failure(
            "meta.json id is %r but the directory is %r" % (meta["id"], project.name)
        )

    levels = level_dirs(project)
    if len(levels) != meta["levels"]:
        raise Failure(
            "meta.json says %d levels but %d level directories exist"
            % (meta["levels"], len(levels))
        )
    if not levels:
        raise Failure("no level directories")

    for level in levels:
        for name in REQUIRED_ICA_LEVEL_FILES:
            if not (level / name).exists():
                raise Failure("%s is missing %s" % (level.name, name))

    total = 0
    for level in levels:
        report = grade.grade(level, project / "reference.py", TIMEOUT)
        if report["outcome"] != "pass":
            raise Failure(
                "reference fails %s: %d/%d (%s)"
                % (level.name, report["passed"], report["total"], report["outcome"])
            )
        total += report["total"]

    starter = grade.grade(levels[0], project / "starter.py", TIMEOUT)
    if starter["outcome"] == "pass":
        raise Failure("the untouched starter passes level 1")

    mutants = sorted(
        p for p in (project / "mutants").glob("*.py") if not p.name.startswith("_")
    ) if (project / "mutants").is_dir() else []
    if len(mutants) < MIN_MUTANTS:
        raise Failure("only %d mutants, need at least %d" % (len(mutants), MIN_MUTANTS))

    survivors = []
    caught = []
    for mutant in mutants:
        # A mutant counts as caught if any level catches it. Breaking level 1
        # while adding level 4 is the failure this is really looking for.
        worst = None
        for level in levels:
            report = grade.grade(level, mutant, TIMEOUT)
            if report["outcome"] != "pass":
                worst = (level.name, report)
                break
        if worst is None:
            survivors.append(mutant.name)
        else:
            level_name, report = worst
            score = (
                "%s %d/%d" % (level_name, report["passed"], report["total"])
                if report["total"]
                else "%s %s" % (level_name, report["outcome"])
            )
            caught.append((mutant.name, score))

    if survivors:
        raise Failure(
            "these wrong answers passed every level: %s" % (", ".join(survivors),)
        )

    if verbose:
        print("    %d levels, %d hidden tests, reference passes all" % (len(levels), total))
        for name, score in caught:
            print("    caught %-26s %s" % (name, score))
    return {"id": meta["id"], "hidden_tests": total, "mutants": len(caught)}


def check_question(question, verbose):
    if (question / "meta.json").exists():
        try:
            with open(str(question / "meta.json")) as handle:
                if json.load(handle).get("format") == "ica":
                    return check_ica(question, verbose)
        except ValueError as exc:
            raise Failure("meta.json is not valid JSON: %s" % (exc,))

    check_files(question)
    meta = check_meta(question)
    total = check_reference(question)
    check_public_suite(question)
    check_starter_fails(question)
    caught = check_mutants(question)

    if verbose:
        print("    %d hidden tests, reference passes all" % (total,))
        for name, score in caught:
            print("    caught %-26s %s" % (name, score))
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
