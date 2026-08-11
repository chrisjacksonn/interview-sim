#!/usr/bin/env python3
"""Session engine for interview-sim.

Owns the clock and the session state. Nothing else is allowed to decide how much
time is left or whether a session is over.

Python 3.9 compatible, standard library only. The end user's interpreter is
whatever their machine happens to ship (Apple Command Line Tools is still on
3.9.6), so no f-string '=' specifiers, no match statements, no 'X | Y'
annotations evaluated at runtime, no tomllib, and nothing installed with pip.

Timing model: 'start' computes an absolute deadline once and writes it down.
Every later question is 'deadline minus now'. Nothing accumulates elapsed time
and nothing recomputes the duration, so restarting the process, closing the
laptop, or running the command from a different directory cannot drift the
clock. Epoch seconds are authoritative; the UTC strings in state.json are there
for humans and are never parsed back (3.9's fromisoformat cannot read a 'Z'
suffix, and this way it never has to).
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

SCHEMA_VERSION = 2

# Exit codes. SKILL.md branches on these, so they are a public contract:
# changing one is a breaking change.
EXIT_OK = 0
EXIT_USAGE = 2
EXIT_NO_SESSION = 3
EXIT_EXPIRED = 4
EXIT_ACTIVE_SESSION = 5
EXIT_BANK = 6
EXIT_ENVIRONMENT = 7
EXIT_TIMEOUT = 8

# Session states. EXPIRED is deliberately never written to disk: it exists only
# in the window between the deadline passing and the next command noticing,
# which converts it to ENDED.
STATE_ACTIVE = "active"
STATE_EXPIRED = "expired"
STATE_ENDED = "ended"

END_REASON_TIME = "time"
END_REASON_SUBMITTED = "submitted"
END_REASON_ABANDONED = "abandoned"

FORMATS = {
    "gca": {"questions": 4, "minutes": 70, "label": "GCA-style"},
    "ica": {"questions": 4, "minutes": 90, "label": "ICA-style"},
}

SKILL_DIR = Path(__file__).resolve().parent.parent
QUESTIONS_DIR = SKILL_DIR / "questions"

DEFAULT_ROOT = Path.home() / "interview-sim-sessions"
POINTER_NAME = "current"
STATE_DIR_NAME = ".sim"
STATE_FILE_NAME = "state.json"

# Copied into the workspace. Anything not on this list stays in the bank, which
# is what keeps tests_hidden.py and any reference solution out of the
# candidate's reach.
PUBLIC_FILES = (
    ("problem.md", "problem.md"),
    ("starter.py", "solution.py"),
    ("tests_public.py", "tests_public.py"),
)


class SessionError(Exception):
    """A failure with a specific exit code attached."""

    def __init__(self, message: str, code: int):
        Exception.__init__(self, message)
        self.code = code


# --------------------------------------------------------------------------
# time
# --------------------------------------------------------------------------


def resolve_now(explicit: Optional[float]) -> float:
    """Current time as epoch seconds.

    --now and INTERVIEW_SIM_NOW exist so the tests can sit at an arbitrary point
    on the clock without sleeping. They are not a security boundary: this is a
    practice tool, and anyone who wants more time can simply take it.
    """
    if explicit is not None:
        return explicit
    env = os.environ.get("INTERVIEW_SIM_NOW")
    if env:
        try:
            return float(env)
        except ValueError:
            raise SessionError(
                "INTERVIEW_SIM_NOW must be epoch seconds, got %r" % (env,),
                EXIT_USAGE,
            )
    return time.time()


def utc_string(epoch: float) -> str:
    """Format epoch seconds as UTC. Display only, never parsed back."""
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(epoch))


def format_duration(seconds: float) -> str:
    """Render a duration as H:MM:SS or M:SS, clamped at zero."""
    total = int(seconds)
    if total < 0:
        total = 0
    hours, rem = divmod(total, 3600)
    minutes, secs = divmod(rem, 60)
    if hours:
        return "%d:%02d:%02d" % (hours, minutes, secs)
    return "%d:%02d" % (minutes, secs)


# --------------------------------------------------------------------------
# state file
# --------------------------------------------------------------------------


def state_path(workspace: Path) -> Path:
    return workspace / STATE_DIR_NAME / STATE_FILE_NAME


def read_state(workspace: Path) -> Dict[str, Any]:
    path = state_path(workspace)
    try:
        with open(str(path), "r") as handle:
            state = json.load(handle)
    except IOError:
        raise SessionError("No session found at %s" % (workspace,), EXIT_NO_SESSION)
    except ValueError as exc:
        raise SessionError(
            "Session state at %s is corrupt (%s). Start a new session." % (path, exc),
            EXIT_ENVIRONMENT,
        )
    version = state.get("schema_version")
    if version != SCHEMA_VERSION:
        raise SessionError(
            "Session state at %s is schema version %r, this build speaks %d."
            % (path, version, SCHEMA_VERSION),
            EXIT_ENVIRONMENT,
        )
    return state


def write_state(workspace: Path, state: Dict[str, Any]) -> None:
    """Write state.json atomically.

    A half-written state file would be indistinguishable from a corrupt one, and
    'status' can run while another command is mid-write, so the replace has to
    be atomic. os.replace is atomic within a filesystem, hence the temp file
    living in the same directory as the target rather than in /tmp.
    """
    target = state_path(workspace)
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.parent / (STATE_FILE_NAME + ".tmp")
    with open(str(tmp), "w") as handle:
        json.dump(state, handle, indent=2, sort_keys=False)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(str(tmp), str(target))


def add_event(state: Dict[str, Any], epoch: float, kind: str, **fields: Any) -> None:
    event = {"epoch": epoch, "type": kind}
    event.update(fields)
    state.setdefault("events", []).append(event)


# --------------------------------------------------------------------------
# session resolution
# --------------------------------------------------------------------------


def sessions_root() -> Path:
    override = os.environ.get("INTERVIEW_SIM_HOME")
    if override:
        return Path(override).expanduser()
    return DEFAULT_ROOT


def pointer_path() -> Path:
    return sessions_root() / POINTER_NAME


def write_pointer(workspace: Path) -> None:
    path = pointer_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.parent / (POINTER_NAME + ".tmp")
    with open(str(tmp), "w") as handle:
        handle.write(str(workspace) + "\n")
    os.replace(str(tmp), str(path))


def read_pointer() -> Optional[Path]:
    try:
        with open(str(pointer_path()), "r") as handle:
            raw = handle.read().strip()
    except IOError:
        return None
    if not raw:
        return None
    candidate = Path(raw)
    return candidate if state_path(candidate).exists() else None


def find_workspace_from_cwd() -> Optional[Path]:
    """Walk up from the working directory looking for a session.

    The candidate is usually sitting inside the workspace editing solution.py
    when they ask how much time is left, so this is the resolution path that
    fires most often in practice.
    """
    current = Path.cwd().resolve()
    for directory in [current] + list(current.parents):
        if state_path(directory).exists():
            return directory
    return None


def resolve_workspace(args: argparse.Namespace) -> Path:
    if getattr(args, "workspace", None):
        workspace = Path(args.workspace).expanduser().resolve()
        if not state_path(workspace).exists():
            raise SessionError("No session at %s" % (workspace,), EXIT_NO_SESSION)
        return workspace

    if getattr(args, "session", None):
        workspace = sessions_root() / args.session
        if not state_path(workspace).exists():
            raise SessionError("No session named %r" % (args.session,), EXIT_NO_SESSION)
        return workspace

    env = os.environ.get("INTERVIEW_SIM_SESSION")
    if env:
        workspace = Path(env).expanduser().resolve()
        if state_path(workspace).exists():
            return workspace

    from_cwd = find_workspace_from_cwd()
    if from_cwd is not None:
        return from_cwd

    from_pointer = read_pointer()
    if from_pointer is not None:
        return from_pointer

    raise SessionError(
        "No active session. Start one with: session.py start --format gca",
        EXIT_NO_SESSION,
    )


# --------------------------------------------------------------------------
# state machine
# --------------------------------------------------------------------------


def classify(state: Dict[str, Any], now: float) -> str:
    """Derive the current state. Never trusts a stored status field."""
    clock = state["clock"]
    if clock.get("ended_epoch") is not None:
        return STATE_ENDED
    if now >= clock["deadline_epoch"]:
        return STATE_EXPIRED
    return STATE_ACTIVE


def finalize(
    workspace: Path, state: Dict[str, Any], now: float, reason: str
) -> Dict[str, Any]:
    """Move a session to ENDED and persist it.

    Expiry is observed rather than scheduled: there is no daemon, so the first
    command to run after the deadline is the one that writes the ending. Once
    written it never moves, which is what makes a second 'status' report the
    same thing as the first.
    """
    clock = state["clock"]
    if clock.get("ended_epoch") is not None:
        return state
    ended_at = clock["deadline_epoch"] if reason == END_REASON_TIME else now
    clock["ended_epoch"] = ended_at
    clock["ended_utc"] = utc_string(ended_at)
    clock["end_reason"] = reason
    add_event(state, ended_at, "session_ended", reason=reason)
    write_state(workspace, state)
    return state


# --------------------------------------------------------------------------
# question bank
# --------------------------------------------------------------------------


def load_bank(fmt: str) -> List[Dict[str, Any]]:
    """Load every question for a format, ordered by slot then id."""
    directory = QUESTIONS_DIR / fmt
    if not directory.is_dir():
        raise SessionError(
            "No question bank for format %r at %s" % (fmt, directory), EXIT_BANK
        )

    questions = []
    for entry in sorted(directory.iterdir()):
        if not entry.is_dir() or entry.name.startswith("_"):
            continue
        meta_file = entry / "meta.json"
        if not meta_file.exists():
            raise SessionError("%s has no meta.json" % (entry,), EXIT_BANK)
        try:
            with open(str(meta_file), "r") as handle:
                meta = json.load(handle)
        except ValueError as exc:
            raise SessionError("%s is not valid JSON: %s" % (meta_file, exc), EXIT_BANK)
        for source, _ in PUBLIC_FILES:
            if not (entry / source).exists():
                raise SessionError("%s is missing %s" % (entry, source), EXIT_BANK)
        meta["_dir"] = entry
        meta["_format"] = fmt
        questions.append(meta)

    questions.sort(key=lambda item: (item.get("slot", 99), item.get("id", "")))
    return questions


def select_questions(fmt: str, count: int) -> List[Dict[str, Any]]:
    bank = load_bank(fmt)
    if len(bank) < count:
        raise SessionError(
            "Format %s wants %d questions but the bank has %d. "
            "Pass --questions %d to run a short session, or add questions to %s."
            % (fmt, count, len(bank), len(bank), QUESTIONS_DIR / fmt),
            EXIT_BANK,
        )
    return bank[:count]


# --------------------------------------------------------------------------
# workspace
# --------------------------------------------------------------------------


def materialize(workspace: Path, questions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Create the directories the candidate works in.

    Only PUBLIC_FILES are copied. tests_hidden.py stays in the bank, so it is
    not merely undisplayed, it is not present on any path the candidate or the
    agent would look at.
    """
    entries = []
    for index, question in enumerate(questions, start=1):
        directory_name = "q%d" % (index,)
        target = workspace / directory_name
        target.mkdir(parents=True, exist_ok=True)
        for source_name, dest_name in PUBLIC_FILES:
            shutil.copyfile(
                str(question["_dir"] / source_name), str(target / dest_name)
            )
        entries.append(
            {
                "slot": index,
                "id": question.get("id", directory_name),
                "dir": directory_name,
                # Where the hidden suite lives, relative to the bank root.
                # Recorded rather than reconstructed from the id so that
                # renaming or removing a question breaks loudly at submit time
                # instead of silently grading against the wrong thing.
                "source": "%s/%s" % (question["_format"], question["_dir"].name),
                "title": question.get("title", ""),
                "difficulty": question.get("difficulty", ""),
                "state": "unlocked",
                "attempts": 0,
                "last_submit_epoch": None,
                "result": None,
            }
        )
    return entries


README_TEMPLATE = """# {label} session

Started {started} UTC. Deadline {deadline} UTC. You have {duration}.

## What to do

{listing}

Write your answer in each `solution.py`. Run the sample tests however you like:

    python3 -m unittest discover -s {first_dir} -p 'tests_public.py' -t .

The sample tests are a sanity check, not the grade. Passing them all does not
mean the question is done.

## Rules

- The clock does not stop. Closing your editor does not pause it.
- Check the time with `status`; do not guess.
- The person proctoring will clarify what a question is asking. They will not
  tell you how to solve it.
- Work submitted after the deadline does not count.

## Time remaining

    python3 "{script}" status
"""


def write_readme(workspace: Path, state: Dict[str, Any]) -> None:
    clock = state["clock"]
    questions = state["questions"]
    lines = []
    for question in questions:
        title = question["title"] or question["id"]
        lines.append("- `%s/` %s" % (question["dir"], title))
    body = README_TEMPLATE.format(
        label=FORMATS[state["format"]]["label"],
        started=clock["started_utc"],
        deadline=clock["deadline_utc"],
        duration=format_duration(clock["duration_seconds"]),
        listing="\n".join(lines),
        first_dir=questions[0]["dir"] if questions else "q1",
        script=Path(__file__).resolve(),
    )
    with open(str(workspace / "README.md"), "w") as handle:
        handle.write(body)


# --------------------------------------------------------------------------
# reporting
# --------------------------------------------------------------------------


def status_payload(state: Dict[str, Any], now: float, phase: str) -> Dict[str, Any]:
    clock = state["clock"]
    if phase == STATE_ENDED:
        remaining = 0.0
        elapsed = clock["ended_epoch"] - clock["started_epoch"]
    else:
        remaining = max(0.0, clock["deadline_epoch"] - now)
        elapsed = now - clock["started_epoch"]
    return {
        "session_id": state["session_id"],
        "state": phase,
        "mode": state["mode"],
        "format": state["format"],
        "workspace": state["workspace"],
        "remaining_seconds": round(remaining, 3),
        "remaining_display": format_duration(remaining),
        "elapsed_seconds": round(elapsed, 3),
        "elapsed_display": format_duration(elapsed),
        "deadline_utc": clock["deadline_utc"],
        "end_reason": clock.get("end_reason"),
        "questions": [
            {
                "slot": q["slot"],
                "id": q["id"],
                "dir": q["dir"],
                "title": q["title"],
                "state": q["state"],
                "attempts": q["attempts"],
                "result": q.get("result"),
            }
            for q in state["questions"]
        ],
    }


def print_status(payload: Dict[str, Any], as_json: bool) -> None:
    if as_json:
        print(json.dumps(payload, indent=2))
        return

    phase = payload["state"]
    if phase == STATE_ENDED:
        reason = payload["end_reason"]
        if reason == END_REASON_TIME:
            headline = "TIME IS UP. This session is over."
        elif reason == END_REASON_ABANDONED:
            headline = "This session was abandoned."
        else:
            headline = "This session is over."
    else:
        headline = "%s remaining" % (payload["remaining_display"],)

    print(headline)
    print("")
    print("session   %s  (%s, %s mode)" % (payload["session_id"], payload["format"], payload["mode"]))
    print("elapsed   %s" % (payload["elapsed_display"],))
    print("deadline  %s UTC" % (payload["deadline_utc"],))
    print("workspace %s" % (payload["workspace"],))
    print("")
    for question in payload["questions"]:
        result = question.get("result")
        if result and result.get("total"):
            score = "%d/%d" % (result["passed"], result["total"])
        elif question["attempts"]:
            score = result.get("outcome", "?") if result else "?"
        else:
            score = "not submitted"
        print(
            "  %-4s %-14s %s"
            % (question["dir"], score, question["title"] or question["id"])
        )


# --------------------------------------------------------------------------
# commands
# --------------------------------------------------------------------------


def command_start(args: argparse.Namespace) -> int:
    now = resolve_now(args.now)

    if args.mode == "interview":
        raise SessionError(
            "Interview mode is not implemented in v1. Use --mode exam.", EXIT_USAGE
        )

    fmt = args.format
    if fmt not in FORMATS:
        raise SessionError(
            "Unknown format %r. Known: %s" % (fmt, ", ".join(sorted(FORMATS))),
            EXIT_USAGE,
        )
    config = FORMATS[fmt]

    count = args.questions if args.questions is not None else config["questions"]
    minutes = args.minutes if args.minutes is not None else config["minutes"]
    if count < 1:
        raise SessionError("--questions must be at least 1", EXIT_USAGE)
    if minutes <= 0:
        raise SessionError("--minutes must be positive", EXIT_USAGE)

    existing = None
    try:
        existing_workspace = resolve_workspace(args)
        existing = (existing_workspace, read_state(existing_workspace))
    except SessionError:
        existing = None

    if existing is not None:
        existing_workspace, existing_state = existing
        phase = classify(existing_state, now)
        if phase in (STATE_ACTIVE, STATE_EXPIRED):
            if not args.force:
                raise SessionError(
                    "Session %s is still running at %s.\n"
                    "Check it with 'status', or pass --force to abandon it."
                    % (existing_state["session_id"], existing_workspace),
                    EXIT_ACTIVE_SESSION,
                )
            finalize(existing_workspace, existing_state, now, END_REASON_ABANDONED)

    questions = select_questions(fmt, count)

    duration = minutes * 60.0
    session_id = "%s-%s" % (fmt, time.strftime("%Y%m%dT%H%M%SZ", time.gmtime(now)))

    if args.workspace:
        workspace = Path(args.workspace).expanduser().resolve()
    else:
        workspace = sessions_root() / session_id

    try:
        workspace.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise SessionError(
            "Cannot create workspace at %s: %s" % (workspace, exc), EXIT_ENVIRONMENT
        )

    state = {
        "schema_version": SCHEMA_VERSION,
        "session_id": session_id,
        "mode": args.mode,
        "format": fmt,
        "workspace": str(workspace),
        "clock": {
            "started_epoch": now,
            "deadline_epoch": now + duration,
            "duration_seconds": duration,
            "started_utc": utc_string(now),
            "deadline_utc": utc_string(now + duration),
            "ended_epoch": None,
            "ended_utc": None,
            "end_reason": None,
        },
        "questions": materialize(workspace, questions),
        "events": [],
    }
    add_event(state, now, "session_started", format=fmt, mode=args.mode, questions=count)

    write_state(workspace, state)
    write_readme(workspace, state)
    write_pointer(workspace)

    payload = status_payload(state, now, STATE_ACTIVE)
    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        print("Session started: %s" % (session_id,))
        print("")
        print("%d question(s), %s on the clock." % (len(state["questions"]), format_duration(duration)))
        print("Deadline %s UTC." % (state["clock"]["deadline_utc"],))
        print("")
        print("Work here:")
        print("  %s" % (workspace,))
        for question in state["questions"]:
            print(
                "    %s/solution.py   %s"
                % (question["dir"], question["title"] or question["id"])
            )
        print("")
        print("Read %s/README.md first. The clock is running." % (workspace,))
    return EXIT_OK


def find_question(state: Dict[str, Any], wanted: Optional[str]) -> Dict[str, Any]:
    """Resolve a question by directory name, slot number, or id."""
    questions = state["questions"]
    if wanted is None:
        if len(questions) == 1:
            return questions[0]
        raise SessionError(
            "Which question? Pass --question with one of: %s"
            % (", ".join(q["dir"] for q in questions),),
            EXIT_USAGE,
        )
    needle = str(wanted).strip().lower()
    for question in questions:
        if needle in (question["dir"].lower(), str(question["slot"]), question["id"].lower()):
            return question
    raise SessionError(
        "No question %r in this session. Have: %s"
        % (wanted, ", ".join(q["dir"] for q in questions)),
        EXIT_USAGE,
    )


def run_grader(question: Dict[str, Any], solution: Path, timeout: float) -> Dict[str, Any]:
    """Shell out to grade.py.

    A subprocess rather than an import, so the candidate's code never executes
    inside the process holding the state file open.
    """
    grader = Path(__file__).resolve().parent / "grade.py"
    if not grader.exists():
        raise SessionError("Grader missing at %s" % (grader,), EXIT_ENVIRONMENT)

    bank_dir = QUESTIONS_DIR / question["source"]
    if not bank_dir.is_dir():
        raise SessionError(
            "Question %s is no longer in the bank at %s. It was renamed or "
            "removed after this session started." % (question["id"], bank_dir),
            EXIT_BANK,
        )

    proc = subprocess.Popen(
        [
            sys.executable,
            str(grader),
            "--question",
            str(bank_dir),
            "--solution",
            str(solution),
            "--timeout",
            str(timeout),
            "--json",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
    )
    out, err = proc.communicate()
    try:
        return json.loads(out)
    except ValueError:
        raise SessionError(
            "Grader failed: %s" % ((err or out).strip() or "no output",),
            EXIT_ENVIRONMENT,
        )


def command_submit(args: argparse.Namespace) -> int:
    now = resolve_now(args.now)
    workspace = resolve_workspace(args)
    state = read_state(workspace)

    phase = classify(state, now)
    if phase == STATE_EXPIRED:
        state = finalize(workspace, state, now, END_REASON_TIME)
        phase = STATE_ENDED

    # The lockout. The architecture contract says the script rejects late work,
    # so this decision lives here and not in anything that could be talked out
    # of it.
    if phase == STATE_ENDED:
        reason = state["clock"].get("end_reason")
        if reason == END_REASON_TIME:
            message = "Time is up. This submission was not accepted."
        else:
            message = "This session is over (%s). Nothing more can be submitted." % (reason,)
        sys.stderr.write(message + "\n")
        return EXIT_EXPIRED

    question = find_question(state, args.question)
    solution = workspace / question["dir"] / "solution.py"

    report = run_grader(question, solution, args.timeout)

    question["attempts"] = question.get("attempts", 0) + 1
    question["last_submit_epoch"] = now
    question["result"] = {
        "passed": report.get("passed", 0),
        "total": report.get("total", 0),
        "credit": report.get("credit", 0.0),
        "outcome": report.get("outcome", "unknown"),
        "at_epoch": now,
    }
    add_event(
        state,
        now,
        "submitted",
        question=question["dir"],
        attempt=question["attempts"],
        outcome=question["result"]["outcome"],
        passed=question["result"]["passed"],
        total=question["result"]["total"],
    )
    write_state(workspace, state)

    payload = {
        "question": question["dir"],
        "id": question["id"],
        "attempt": question["attempts"],
        "remaining_display": format_duration(state["clock"]["deadline_epoch"] - now),
        "accepted": True,
    }
    payload.update(question["result"])

    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        outcome = report.get("outcome")
        if outcome == "missing":
            print("No solution.py found in %s/." % (question["dir"],))
        elif outcome == "import_error":
            print(
                "%s/solution.py did not import (%s). Nothing could be graded."
                % (question["dir"], report.get("detail"))
            )
        elif outcome == "timeout":
            print("%s/solution.py did not finish. Something is not terminating." % (question["dir"],))
        else:
            print(
                "%s  %d of %d hidden tests passed (%.0f%%)."
                % (
                    question["dir"],
                    report["passed"],
                    report["total"],
                    report["credit"] * 100,
                )
            )
        print("")
        print("attempt %d, %s left on the clock." % (question["attempts"], payload["remaining_display"]))

    if report.get("outcome") == "timeout":
        return EXIT_TIMEOUT
    return EXIT_OK


def band_for(credit: float, solved: int, count: int) -> str:
    """A qualitative band, deliberately not a number.

    CodeSignal's 200-600 scale is proprietary and calibrated against data that
    is not public. Inventing a point estimate would be dressing a guess up as a
    measurement, so this reports what was actually observed instead. See
    non-negotiable 3.
    """
    if count and solved == count:
        return "every question fully solved"
    if credit >= 0.85:
        return "strong: nearly everything passing"
    if credit >= 0.6:
        return "solid, with gaps to close"
    if credit >= 0.3:
        return "partial: the shape is there, the edge cases are not"
    if credit > 0:
        return "early: most tests still failing"
    return "nothing passing yet"


def command_report(args: argparse.Namespace) -> int:
    now = resolve_now(args.now)
    workspace = resolve_workspace(args)
    state = read_state(workspace)

    phase = classify(state, now)
    if phase == STATE_EXPIRED:
        state = finalize(workspace, state, now, END_REASON_TIME)
        phase = STATE_ENDED

    questions = state["questions"]
    count = len(questions)
    total_tests = 0
    passed_tests = 0
    solved = 0
    attempted = 0
    lines = []

    for question in questions:
        result = question.get("result")
        if question.get("attempts"):
            attempted += 1
        if result and result.get("total"):
            total_tests += result["total"]
            passed_tests += result["passed"]
            if result["outcome"] == "pass":
                solved += 1
            summary = "%d/%d" % (result["passed"], result["total"])
        elif result:
            summary = result.get("outcome", "?")
        else:
            summary = "not attempted"
        lines.append(
            {
                "dir": question["dir"],
                "title": question["title"] or question["id"],
                "difficulty": question.get("difficulty", ""),
                "attempts": question.get("attempts", 0),
                "summary": summary,
                "credit": (result or {}).get("credit", 0.0),
                "last_submit_epoch": question.get("last_submit_epoch"),
            }
        )

    # Average the per-question credit rather than pooling every test.
    # Pooling silently drops any question that produced no test results at all,
    # so a session with three perfect answers and one that timed out reported
    # "60 of 60 passed" and called itself strong. A question that did not run is
    # a zero, not an absence.
    credit = sum(line["credit"] for line in lines) / count if count else 0.0
    clock = state["clock"]
    used = (clock.get("ended_epoch") or min(now, clock["deadline_epoch"])) - clock["started_epoch"]

    payload = {
        "session_id": state["session_id"],
        "format": state["format"],
        "mode": state["mode"],
        "state": phase,
        "end_reason": clock.get("end_reason"),
        "questions": count,
        "attempted": attempted,
        "solved": solved,
        "tests_passed": passed_tests,
        "tests_total": total_tests,
        "credit": round(credit, 4),
        "band": band_for(credit, solved, count),
        "time_used_display": format_duration(used),
        "duration_display": format_duration(clock["duration_seconds"]),
        "detail": lines,
        "score_note": (
            "Unofficial. This is what these hidden tests measured, not a "
            "CodeSignal score. No 200-600 estimate is produced because that "
            "scale is proprietary and cannot be reproduced honestly."
        ),
    }

    if args.json:
        print(json.dumps(payload, indent=2))
        return EXIT_OK

    print("%s  %s" % (state["session_id"], state["format"].upper()))
    if phase == STATE_ENDED:
        print("Finished (%s). Used %s of %s." % (clock.get("end_reason"), payload["time_used_display"], payload["duration_display"]))
    else:
        print("Still running. %s used of %s." % (payload["time_used_display"], payload["duration_display"]))
    print("")
    for line in lines:
        print(
            "  %-4s %-12s %-10s %s"
            % (line["dir"], line["summary"], line["difficulty"], line["title"])
        )
    print("")
    print("Solved %d of %d." % (solved, count))
    if total_tests:
        print(
            "%d of %d hidden tests passed on the questions that ran."
            % (passed_tests, total_tests)
        )
    print("Overall: %.0f%% credit across all %d questions, %s." % (credit * 100, count, payload["band"]))
    print("")
    print(payload["score_note"])
    return EXIT_OK


def command_status(args: argparse.Namespace) -> int:
    now = resolve_now(args.now)
    workspace = resolve_workspace(args)
    state = read_state(workspace)

    phase = classify(state, now)
    if phase == STATE_EXPIRED:
        state = finalize(workspace, state, now, END_REASON_TIME)
        phase = STATE_ENDED

    payload = status_payload(state, now, phase)
    print_status(payload, args.json)

    if phase == STATE_ENDED and state["clock"]["end_reason"] == END_REASON_TIME:
        return EXIT_EXPIRED
    return EXIT_OK


# --------------------------------------------------------------------------
# entry point
# --------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="session.py", description="Timed assessment session engine."
    )
    subparsers = parser.add_subparsers(dest="command")

    def add_common(sub: argparse.ArgumentParser) -> None:
        sub.add_argument("--json", action="store_true", help="machine-readable output")
        # Test-only clock injection; not documented in --help output.
        sub.add_argument("--now", type=float, default=None, help=argparse.SUPPRESS)

    start = subparsers.add_parser("start", help="start a session")
    start.add_argument("--format", default="gca", help="gca or ica")
    start.add_argument("--mode", default="exam", choices=("exam", "interview"))
    start.add_argument("--questions", type=int, default=None)
    start.add_argument("--minutes", type=float, default=None)
    start.add_argument("--workspace", default=None)
    start.add_argument("--session", default=None, help=argparse.SUPPRESS)
    start.add_argument(
        "--force", action="store_true", help="abandon any running session"
    )
    add_common(start)
    start.set_defaults(func=command_start)

    submit = subparsers.add_parser("submit", help="grade a solution against the hidden tests")
    submit.add_argument("--question", default=None, help="q1, a slot number, or a question id")
    submit.add_argument("--workspace", default=None)
    submit.add_argument("--session", default=None)
    submit.add_argument("--timeout", type=float, default=30.0)
    add_common(submit)
    submit.set_defaults(func=command_submit)

    report = subparsers.add_parser("report", help="summarise the session")
    report.add_argument("--workspace", default=None)
    report.add_argument("--session", default=None)
    add_common(report)
    report.set_defaults(func=command_report)

    status = subparsers.add_parser("status", help="show time remaining")
    status.add_argument("--workspace", default=None)
    status.add_argument("--session", default=None)
    add_common(status)
    status.set_defaults(func=command_status)

    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not getattr(args, "command", None):
        parser.print_help()
        return EXIT_USAGE
    try:
        return args.func(args)
    except SessionError as exc:
        sys.stderr.write("%s\n" % (exc,))
        return exc.code


if __name__ == "__main__":
    sys.exit(main())
