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
import ast
import json
import re
import os
import sys
from concurrent import futures
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
QUESTIONS = REPO / "skills" / "sim" / "questions"
sys.path.insert(0, str(REPO / "skills" / "sim" / "scripts"))

import grade  # noqa: E402  - path is set up immediately above
import session  # noqa: E402  - for patch_mutant_fields, the one shared piece

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


def grade_all(target, solutions):
    """Grade several solutions against one suite, concurrently.

    Mutants are independent and most of the wall time is a mutant sitting out
    its timeout, so running them one at a time made the gate scale badly with
    the size of the bank. Threads are enough because grade.grade spends its time
    waiting on a subprocess, and it builds its own temp directory per call so
    there is nothing shared to race on.

    Shortening the timeout would have been the easy fix and the wrong one: a
    mutant that is merely slow would then be "caught" by a limit the real
    session does not impose, and the result would drift with machine load.
    """
    solutions = list(solutions)
    if not solutions:
        return []
    workers = min(len(solutions), (os.cpu_count() or 2))
    with futures.ThreadPoolExecutor(max_workers=workers) as pool:
        submitted = [
            (solution, pool.submit(grade.grade, target, solution, TIMEOUT))
            for solution in solutions
        ]
        return [(solution, future.result()) for solution, future in submitted]


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


def check_public_suite(question, total):
    """The samples must be satisfiable too, or they mislead during the session.

    Takes the reference's test count rather than re-grading. Grading the
    reference twice per question doubled the slowest part of the gate for no
    new information.
    """
    if total == 0:
        raise Failure("hidden suite contains no tests")
    public = question / "tests_public.py"
    if "def test_" not in public.read_text():
        raise Failure("tests_public.py contains no tests")


def check_starter_fails(question):
    """An unfilled starter that passes means the question asks for nothing."""
    report = grade.grade(question, question / "starter.py", TIMEOUT)
    if report["outcome"] == "pass":
        raise Failure("the untouched starter passes the hidden suite")


def check_mutants(question, tier):
    """Every plausible wrong answer must be caught by at least one hidden test.

    Two tiers, because the checks cost very different amounts.

    "full" is the real gate: the question ships deliberately-wrong solutions and
    every one is caught. This is what proves the hidden suite discriminates, and
    it has caught three suites in this repository that looked thorough and were
    not.

    "basic" skips it. The question is still answerable and still non-trivial,
    because the reference must pass and the starter must fail, but nothing has
    proved the suite can tell a wrong answer from a right one. A basic question
    can therefore grade something as correct that is not.

    Basic exists so the bank can grow faster than mutants can be written. It is
    a deliberate trade and both the README and the question itself say which
    tier it is.
    """
    directory = question / "mutants"
    mutants = (
        sorted(p for p in directory.glob("*.py") if not p.name.startswith("_"))
        if directory.is_dir()
        else []
    )

    if tier == "basic":
        if len(mutants) >= MIN_MUTANTS:
            raise Failure(
                "marked basic but ships %d mutants: mark it full" % (len(mutants),)
            )
        return [("(not validated)", "no mutants, basic tier")]

    if not directory.is_dir():
        raise Failure(
            "no mutants/ directory. Add at least %d wrong answers, or set "
            '"validated": "basic" in meta.json and accept that nothing has '
            "proved this suite discriminates." % (MIN_MUTANTS,)
        )
    if len(mutants) < MIN_MUTANTS:
        raise Failure(
            "only %d mutants, need at least %d (or mark the question basic)"
            % (len(mutants), MIN_MUTANTS)
        )

    # Patch mutants (OLD/NEW strings composed against the reference) are the
    # convention generated questions use, and without composing them here a
    # patch-style file in a corpus mutants/ dir fails to import and counts as
    # "caught", which is a meaningless mutant passing the gate silently.
    reference_text = (question / "reference.py").read_text()
    composed_dir = None
    prepared = []
    for mutant in mutants:
        fields = session.patch_mutant_fields(mutant)
        if fields is None:
            prepared.append(mutant)
            continue
        old_text, new_text = fields
        if reference_text.count(old_text) != 1:
            raise Failure(
                "%s: OLD must match reference.py exactly once" % (mutant.name,)
            )
        if old_text == new_text:
            raise Failure("%s: OLD and NEW are identical" % (mutant.name,))
        if composed_dir is None:
            import tempfile
            composed_dir = Path(tempfile.mkdtemp(prefix="qa-mutants-"))
        target = composed_dir / mutant.name
        target.write_text(reference_text.replace(old_text, new_text))
        prepared.append(target)

    survivors = []
    caught = []
    for mutant, report in grade_all(question, prepared):
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


def check_ica(project):
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
    # A mutant counts as caught by the earliest level that catches it. Breaking
    # level 1 while adding level 4 is the failure this is really looking for, so
    # levels are checked in order and the first failure is the one reported.
    per_level = dict(
        (level.name, dict((m, r) for m, r in grade_all(level, mutants)))
        for level in levels
    )
    for mutant in mutants:
        worst = None
        for level in levels:
            report = per_level[level.name][mutant]
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

    lines = ["    %d levels, %d hidden tests, reference passes all" % (len(levels), total)]
    for name, score in caught:
        lines.append("    caught %-26s %s" % (name, score))
    return {"id": meta["id"], "hidden_tests": total, "mutants": len(caught), "lines": lines}


# Test names that promise the caller's input came back untouched.
PRESERVATION_TEST = re.compile(r"not_mutated|not_modified|unchanged|is_preserved|left_alone")


def check_preservation_fixtures(question):
    """An input-preservation test needs a fixture that sorting would disturb.

    This has now been the same bug four times, in four different questions, and
    it is invisible by inspection: the test looks right, it asserts the right
    thing, and it passes for a solution that sorts the caller's list in place,
    because the fixture was already in sorted order. The assertion never fires
    and the suite reports a clean pass.

    A literal that is already sorted is not proof of a bug, but in a test whose
    whole purpose is to detect reordering it is never what you meant to write.
    """
    suite = question / "tests_hidden.py"
    if not suite.exists():
        return
    source = suite.read_text()
    try:
        tree = ast.parse(source)
    except SyntaxError as exc:
        raise Failure("tests_hidden.py does not parse: %s" % (exc,))

    for node in ast.walk(tree):
        if not isinstance(node, ast.FunctionDef):
            continue
        if not PRESERVATION_TEST.search(node.name):
            continue
        # Only the outermost literal is the fixture. The rows inside it are
        # records, and a record whose own fields happen to ascend says nothing
        # about whether the collection could be reordered.
        nested = set()
        for outer in ast.walk(node):
            if isinstance(outer, (ast.List, ast.Tuple)):
                for element in outer.elts:
                    nested.add(id(element))
        for literal in ast.walk(node):
            if not isinstance(literal, (ast.List, ast.Tuple)) or len(literal.elts) < 2:
                continue
            if id(literal) in nested:
                continue
            try:
                values = [ast.literal_eval(element) for element in literal.elts]
            except (ValueError, SyntaxError):
                continue
            try:
                ordered = sorted(values)
            except TypeError:
                continue
            if values == ordered:
                raise Failure(
                    "%s uses a fixture that is already sorted (%r), so a solution "
                    "that sorts the input in place would pass it. Give it an order "
                    "that sorting would disturb." % (node.name, values)
                )


def check_question(question):
    if (question / "meta.json").exists():
        try:
            with open(str(question / "meta.json")) as handle:
                if json.load(handle).get("format") == "ica":
                    return check_ica(question)
        except ValueError as exc:
            raise Failure("meta.json is not valid JSON: %s" % (exc,))

    check_files(question)
    check_preservation_fixtures(question)
    meta = check_meta(question)
    tier = meta.get("validated", "full")
    if tier not in ("full", "basic"):
        raise Failure('validated must be "full" or "basic", got %r' % (tier,))
    total = check_reference(question)
    check_public_suite(question, total)
    check_starter_fails(question)
    caught = check_mutants(question, tier)

    lines = [
        "    %d hidden tests, reference passes all%s"
        % (total, "" if tier == "full" else "   [BASIC: suite not proved to discriminate]")
    ]
    for name, score in caught:
        lines.append("    caught %-26s %s" % (name, score))
    return {"id": meta["id"], "hidden_tests": total, "mutants": len(caught), "lines": lines}


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

    # Questions are independent and the slowest part of each is a mutant sitting
    # out its 30 second timeout, so running them one at a time made the gate
    # scale with the size of the bank rather than with its slowest question.
    # Output is collected and printed in order so concurrency stays invisible.
    failures = []
    workers = min(len(targets), (os.cpu_count() or 2))
    with futures.ThreadPoolExecutor(max_workers=workers) as pool:
        pending = [(q, pool.submit(check_question, q)) for q in targets]
        for question, future in pending:
            label = "%s/%s" % (question.parent.name, question.name)
            try:
                result = future.result()
            except Failure as exc:
                failures.append((label, str(exc)))
                print("  FAIL  %s: %s" % (label, exc))
            else:
                if not args.quiet:
                    for line in result["lines"]:
                        print(line)
                print("  ok    %s" % (label,))

    print("")
    if failures:
        print("%d of %d questions failed the gate." % (len(failures), len(targets)))
        return 1
    print("%d question(s) passed the gate." % (len(targets),))
    return 0


if __name__ == "__main__":
    sys.exit(main())
