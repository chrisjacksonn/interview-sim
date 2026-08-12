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
import random
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

VERSION = "0.5.0"
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
# Nothing could be graded: the file did not import, died mid-run, or is absent.
# Distinct from 2, which means the command itself was wrong or refused.
EXIT_NOT_GRADED = 9

# Session states. EXPIRED is deliberately never written to disk: it exists only
# in the window between the deadline passing and the next command noticing,
# which converts it to ENDED.
STATE_ACTIVE = "active"
STATE_EXPIRED = "expired"
STATE_ENDED = "ended"

# Grader outcomes meaning the hidden tests never executed. These cannot be
# summed with real counts, because 0 of 0 is not "everything passed".
NO_TESTS_RAN = ("timeout", "crashed", "import_error", "missing")

END_REASON_TIME = "time"
END_REASON_SUBMITTED = "submitted"
END_REASON_ABANDONED = "abandoned"

FORMATS = {
    "gca": {"questions": 4, "minutes": 70, "label": "GCA-style", "gated": False},
    # ICA is one project whose levels unlock in order, so "questions" here means
    # levels of a single project rather than independent problems.
    "ica": {"questions": 4, "minutes": 90, "label": "ICA-style", "gated": True},
}

STATE_LOCKED = "locked"
STATE_UNLOCKED = "unlocked"
STATE_PASSED = "passed"

# Interview mode is the same engine with a different set of defaults and a
# different person running it. One question rather than four, more time on it,
# and hints are available at a cost instead of refused outright. The scripts
# still own the clock and the grades; only the persona changes.
MODE_DEFAULTS = {
    "exam": {},
    "interview": {"questions": 1, "minutes": 45},
}

SKILL_DIR = Path(__file__).resolve().parent.parent
QUESTIONS_DIR = SKILL_DIR / "questions"
PRESETS_FILE = SKILL_DIR / "presets.json"

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


class session_lock(object):
    """Serialise the read-modify-write that every mutating command performs.

    write_state is atomic against a torn file but does nothing about lost
    updates, and the window here is the whole grading run: seconds for GCA and
    up to four timeouts for ICA. Two overlapping submits both graded, both
    printed a real score to the candidate, and the second silently discarded the
    first, after which report said the question had never been attempted.

    Not hypothetical. The tool is driven by an agent that batches independent
    shell calls, so two submits starting together is ordinary use.

    flock is advisory and Unix-only. On a platform without it the lock quietly
    does nothing, which is the same behaviour as before rather than a crash.
    """

    def __init__(self, workspace: Path):
        self._path = workspace / STATE_DIR_NAME / "lock"
        self._handle = None

    def __enter__(self) -> "session_lock":
        try:
            import fcntl
        except ImportError:
            return self
        try:
            self._path.parent.mkdir(parents=True, exist_ok=True)
            self._handle = open(str(self._path), "w")
            fcntl.flock(self._handle.fileno(), fcntl.LOCK_EX)
        except (IOError, OSError):
            if self._handle is not None:
                self._handle.close()
                self._handle = None
        return self

    def __exit__(self, *exc_info: Any) -> bool:
        if self._handle is not None:
            try:
                import fcntl

                fcntl.flock(self._handle.fileno(), fcntl.LOCK_UN)
            except (ImportError, IOError, OSError):
                pass
            self._handle.close()
            self._handle = None
        return False


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


HISTORY_NAME = "history.json"
HISTORY_KEEP = 60


def history_path() -> Path:
    return sessions_root() / HISTORY_NAME


def recent_question_ids() -> set:
    """Question ids served recently on this machine.

    Kept in one small file rather than derived by walking session directories,
    so deleting an old workspace does not resurrect its questions, and a session
    started somewhere odd with --workspace still counts.
    """
    try:
        with open(str(history_path()), "r") as handle:
            data = json.load(handle)
    except (IOError, ValueError):
        return set()
    served = data.get("served")
    return set(served) if isinstance(served, list) else set()


def remember_questions(ids: List[str]) -> None:
    """Append served question ids, newest last, oldest trimmed.

    Best effort: a read-only or unwritable sessions root must not stop a session
    from starting, it just means no rotation.
    """
    if not ids:
        return
    try:
        served = [item for item in recent_question_ids()]
        # recent_question_ids returns a set, so order is rebuilt from the file
        # when it parses and simply reset when it does not.
        try:
            with open(str(history_path()), "r") as handle:
                stored = json.load(handle).get("served") or []
            served = [item for item in stored if isinstance(item, str)]
        except (IOError, ValueError):
            served = []

        for question_id in ids:
            if question_id in served:
                served.remove(question_id)
            served.append(question_id)

        path = history_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.parent / (HISTORY_NAME + ".tmp")
        with open(str(tmp), "w") as handle:
            json.dump({"served": served[-HISTORY_KEEP:]}, handle, indent=2)
            handle.write("\n")
        os.replace(str(tmp), str(path))
    except OSError:
        pass


def load_presets() -> Dict[str, Any]:
    try:
        with open(str(PRESETS_FILE), "r") as handle:
            return json.load(handle).get("presets", {})
    except IOError:
        return {}
    except ValueError as exc:
        raise SessionError("%s is not valid JSON: %s" % (PRESETS_FILE, exc), EXIT_BANK)


def resolve_preset(name: str) -> Dict[str, Any]:
    """Look up a company preset.

    Matching is case and punctuation insensitive, because people type "Capital
    One", "capital-one", and "capitalone" for the same thing.
    """
    presets = load_presets()

    def normalise(text: str) -> str:
        return "".join(char for char in text.lower() if char.isalnum())

    wanted = normalise(name)
    for key, value in presets.items():
        if normalise(key) == wanted:
            preset = dict(value)
            preset["_name"] = key
            return preset

    if not presets:
        raise SessionError(
            "No company presets are configured yet, so %r cannot be looked up.\n"
            "Start a format directly instead: --format gca or --format ica." % (name,),
            EXIT_BANK,
        )
    raise SessionError(
        "No preset for %r. Known: %s\n"
        "Start a format directly instead: --format gca or --format ica."
        % (name, ", ".join(sorted(presets))),
        EXIT_BANK,
    )


def load_ica_project(project_id: Optional[str], seed: Optional[int] = None) -> Dict[str, Any]:
    """Pick an ICA project and describe its levels.

    Chosen at random when there is more than one and none was named, for the
    same reason GCA picks within a slot: taking the alphabetically first project
    every time means the second sitting is the same exam, and an ICA project is
    only worth anything the first time you meet its level 4.
    """
    directory = QUESTIONS_DIR / "ica"
    if not directory.is_dir():
        raise SessionError("No ICA projects at %s" % (directory,), EXIT_BANK)

    projects = sorted(
        entry for entry in directory.iterdir()
        if entry.is_dir() and not entry.name.startswith("_")
    )
    if project_id:
        projects = [entry for entry in projects if entry.name == project_id]
        if not projects:
            raise SessionError("No ICA project named %r" % (project_id,), EXIT_BANK)
    if not projects:
        raise SessionError("No ICA projects available", EXIT_BANK)

    project = projects[0] if len(projects) == 1 else random.Random(seed).choice(projects)
    meta_file = project / "meta.json"
    if not meta_file.exists():
        raise SessionError("%s has no meta.json" % (project,), EXIT_BANK)
    with open(str(meta_file), "r") as handle:
        meta = json.load(handle)

    levels = sorted(project.glob("level*"), key=lambda p: int(p.name[5:]))
    if not levels:
        raise SessionError("%s has no level directories" % (project,), EXIT_BANK)
    meta["_dir"] = project
    meta["_levels"] = levels
    return meta


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


def select_questions(
    fmt: str,
    count: int,
    seed: Optional[int] = None,
    slot: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """Pick one question per difficulty slot.

    Slots are the difficulty ramp, so a session takes one question from each
    rather than the first N overall. Taking the first N would serve two warm-ups
    and two mediums as soon as the bank has more than one question per slot, and
    the session would stop resembling the format it is imitating.

    Where a slot holds several questions the choice is random, so sitting the
    same format twice is not the same exam twice. --seed makes that repeatable.
    """
    bank = load_bank(fmt)
    by_slot = {}
    for question in bank:
        by_slot.setdefault(question.get("slot", 99), []).append(question)

    slots = sorted(by_slot)
    if slot is not None:
        # Drawing from one difficulty on purpose, which is what an interview is:
        # a single question at a chosen level rather than a ramp.
        if slot not in by_slot:
            raise SessionError(
                "No questions in slot %d. Slots available: %s"
                % (slot, ", ".join(str(value) for value in slots)),
                EXIT_BANK,
            )
        chooser = random.Random(seed)
        options = sorted(by_slot[slot], key=lambda item: item.get("id", ""))
        if count > len(options):
            raise SessionError(
                "Slot %d has %d question(s) but %d were asked for."
                % (slot, len(options), count),
                EXIT_BANK,
            )
        return chooser.sample(options, count) if count > 1 else [chooser.choice(options)]

    if len(slots) < count:
        raise SessionError(
            "Format %s wants %d questions but the bank only covers %d difficulty "
            "slot(s) (%s). Pass --questions %d, or add questions to %s."
            % (
                fmt,
                count,
                len(slots),
                ", ".join(str(slot) for slot in slots),
                len(slots),
                QUESTIONS_DIR / fmt,
            ),
            EXIT_BANK,
        )

    chooser = random.Random(seed)
    # Prefer questions this machine has not served recently. Drawing
    # independently each sitting sounds fair and is not: measured over the real
    # selector, 98.7% of three-sitting runs repeated a question and the warm-up
    # repeated back to back a third of the time, which is memory practice rather
    # than the thing this tool is for.
    #
    # Skipped entirely when a seed is given, because --seed promises the same
    # exam from the same number and history would make that depend on what the
    # machine happened to have run.
    seen = set() if seed is not None else recent_question_ids()

    chosen = []
    for slot in slots[:count]:
        options = sorted(by_slot[slot], key=lambda item: item.get("id", ""))
        if len(options) == 1:
            chosen.append(options[0])
            continue
        fresh = [item for item in options if item.get("id") not in seen]
        # Once every question in a slot has been seen, the slot starts over
        # rather than refusing to serve anything.
        chosen.append(chooser.choice(fresh if fresh else options))
    return chosen


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
                "hints": 0,
                "last_submit_epoch": None,
                "result": None,
            }
        )
    return entries


def materialize_level(workspace: Path, project_dir: str, level: Dict[str, Any]) -> None:
    """Reveal one ICA level's material into the workspace.

    Only the level being unlocked is copied. A locked level's problem statement
    is not sitting on disk waiting to be read, which is the whole point of
    gating: you design for what you have been told about so far, and level 4
    then makes you regret some of it.
    """
    source = QUESTIONS_DIR / level["source"]
    target = workspace / project_dir
    target.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(str(source / "problem.md"), str(target / ("level%d.md" % level["slot"])))
    shutil.copyfile(
        str(source / "tests_public.py"),
        str(target / ("tests_public_level%d.py" % level["slot"])),
    )


def materialize_ica(workspace: Path, meta: Dict[str, Any], count: int) -> List[Dict[str, Any]]:
    """Lay out an ICA project: one solution file, level 1 revealed."""
    project_dir = meta["id"]
    target = workspace / project_dir
    target.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(str(meta["_dir"] / "starter.py"), str(target / "solution.py"))

    entries = []
    for index, level in enumerate(meta["_levels"][:count], start=1):
        entries.append(
            {
                "slot": index,
                "id": "%s-level%d" % (meta["id"], index),
                "dir": project_dir,
                "source": "ica/%s/%s" % (meta["id"], level.name),
                "title": "Level %d" % (index,),
                "difficulty": "level%d" % (index,),
                "state": STATE_UNLOCKED if index == 1 else STATE_LOCKED,
                "attempts": 0,
                "hints": 0,
                "last_submit_epoch": None,
                "result": None,
            }
        )
    if entries:
        materialize_level(workspace, project_dir, entries[0])
    return entries


README_TEMPLATE = """# {label} session

Started {started} UTC. Deadline {deadline} UTC. You have {duration}.

## What to do

{listing}

{intro}

## Running things

Save yourself the typing:

    sim() {{ python3 "{script}" "$@"; }}

Sample tests, from inside a question directory:

    cd {first_dir}
    python3 -m unittest tests_public

They are a sanity check, not the grade. Passing them all does not mean the
question is done.

Time remaining:

    sim status

Grade a question against the hidden tests:

    sim submit --question {first_dir}

It tells you how many hidden tests passed and nothing else. Which ones failed is
the part you work out. Resubmit as often as you like, it only costs time.

When the clock runs out:

    sim report

## Rules

- The clock does not stop. Closing your editor does not pause it.
- Check the time with `sim status`; do not guess.
- The person proctoring will clarify what a question is asking. They will not
  tell you how to solve it.
- Work submitted after the deadline does not count, even if it is correct.
{extra}"""


def write_readme(workspace: Path, state: Dict[str, Any]) -> None:
    clock = state["clock"]
    questions = state["questions"]
    gated = FORMATS[state["format"]]["gated"]
    lines = []
    if gated:
        project = questions[0]["dir"] if questions else "project"
        lines.append("- `%s/solution.py` is the whole project." % (project,))
        lines.append("- `%s/level1.md` is the only level you can see." % (project,))
        lines.append(
            "- Levels 2 to %d appear as you pass the one before." % (len(questions),)
        )
    else:
        for question in questions:
            title = question["title"] or question["id"]
            lines.append("- `%s/` %s" % (question["dir"], title))

    extra = ""
    if gated:
        extra = (
            "\n## How the levels work\n\n"
            "You extend one `solution.py` the whole way through. Passing a level\n"
            "reveals the next one, and there is no way to read ahead.\n\n"
            "Every submission re-runs the levels below the one you are on, so a\n"
            "level 4 feature that breaks level 1 costs you the marks it broke.\n"
            "`submit` with no argument means whichever level is open.\n"
        )

    body = README_TEMPLATE.format(
        label=FORMATS[state["format"]]["label"],
        started=clock["started_utc"],
        deadline=clock["deadline_utc"],
        duration=format_duration(clock["duration_seconds"]),
        listing="\n".join(lines),
        first_dir=questions[0]["dir"] if questions else "q1",
        script=Path(__file__).resolve(),
        extra=extra,
        intro=(
            "Write your answer in that one `solution.py`. It carries across every level."
            if gated
            else "Write your answer in each `solution.py`."
        ),
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

    preset = resolve_preset(args.preset) if args.preset else None
    if preset is not None and preset.get("format") is None:
        # The company is a confirmed CodeSignal customer but which assessment
        # they give is not known. Say so and let the caller choose, rather than
        # picking one and letting them believe it was researched.
        if args.format_given:
            fmt = args.format
        else:
            raise SessionError(
                "%s is a confirmed CodeSignal customer, but which assessment "
                "they use is not confirmed.%s\n"
                "Pick one: --preset %s --format gca, or --format ica."
                % (
                    preset["_name"],
                    ("\n" + preset["note"]) if preset.get("note") else "",
                    preset["_name"],
                ),
                EXIT_USAGE,
            )
    else:
        fmt = preset["format"] if preset else args.format
    if fmt not in FORMATS:
        raise SessionError(
            "Unknown format %r. Known: %s" % (fmt, ", ".join(sorted(FORMATS))),
            EXIT_USAGE,
        )
    config = FORMATS[fmt]

    # Explicit flags beat the preset, the preset beats the format default.
    # Explicit flags beat the preset, the preset beats the mode's defaults, and
    # those beat the format's.
    mode_defaults = MODE_DEFAULTS.get(args.mode, {})
    count = args.questions
    if count is None:
        count = (preset or {}).get(
            "questions", mode_defaults.get("questions", config["questions"])
        )
    minutes = args.minutes
    if minutes is None:
        minutes = (preset or {}).get(
            "minutes", mode_defaults.get("minutes", config["minutes"])
        )
    if count < 1:
        raise SessionError("--questions must be at least 1", EXIT_USAGE)
    # `minutes != minutes` is the NaN test without importing math. A bare
    # `<= 0` check passes NaN straight through, and it then reaches
    # time.strftime as a deadline and raises a traceback at the user, after the
    # workspace directory has already been created. The upper bound is not
    # pedantry either: 1e17 is finite and still overflows the platform time
    # type. A year of exam is past the point of arguing about.
    if minutes != minutes or minutes <= 0 or minutes > 525600:
        raise SessionError(
            "--minutes must be a positive number of minutes, at most 525600",
            EXIT_USAGE,
        )

    # Look for a session already running, in the named workspace AND in the
    # usual place. Resolving only through args meant that passing --workspace
    # pointed the search at a directory that does not exist yet, the lookup
    # failed, and the guard concluded nothing was running: a second clock
    # started alongside a live session and the pointer moved to it silently.
    existing = None
    candidates = []
    if getattr(args, "workspace", None):
        candidates.append(Path(args.workspace).expanduser().resolve())
    incumbent = argparse.Namespace(
        workspace=None, session=getattr(args, "session", None)
    )
    try:
        candidates.append(resolve_workspace(incumbent))
    except SessionError:
        pass

    for candidate in candidates:
        try:
            candidate_state = read_state(candidate)
        except SessionError:
            continue
        if classify(candidate_state, now) in (STATE_ACTIVE, STATE_EXPIRED):
            existing = (candidate, candidate_state)
            break

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

    if config["gated"]:
        project = load_ica_project(args.project, args.seed)
        available = len(project["_levels"])
        if available < count:
            raise SessionError(
                "Project %s has %d levels but %d were asked for."
                % (project["id"], available, count),
                EXIT_BANK,
            )
        questions = None
    else:
        project = None
        questions = select_questions(fmt, count, args.seed, args.slot)

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
        "seed": args.seed,
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
        "questions": (
            materialize_ica(workspace, project, count)
            if project is not None
            else materialize(workspace, questions)
        ),
        "events": [],
    }
    add_event(state, now, "session_started", format=fmt, mode=args.mode, questions=count)

    write_state(workspace, state)
    write_readme(workspace, state)
    write_pointer(workspace)
    remember_questions([question["id"] for question in state["questions"]])

    payload = status_payload(state, now, STATE_ACTIVE)
    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        print("Session started: %s" % (session_id,))
        print("")
        if preset is not None:
            # Two separate claims. That they use CodeSignal is often first-party
            # and solid; which assessment they give usually is not, and printing
            # the first next to the format would launder one into the other.
            print(
                "%s preset: uses CodeSignal (%s confidence)."
                % (preset["_name"], preset.get("confidence", "unknown"))
            )
            if preset.get("format") is None:
                print(
                    "Their format is not confirmed. Running %s because you asked "
                    "for it, not because it was researched." % (fmt.upper(),)
                )
            else:
                print(
                    "Format %s, %s confidence."
                    % (fmt.upper(), preset.get("format_confidence", "unknown"))
                )
            if preset.get("note"):
                print(preset["note"])
            print(
                "Formats change every hiring cycle. Your actual invite email "
                "names the platform and the format; trust that over this."
            )
            print("")
        if config["gated"]:
            print(
                "One project, %d levels, %s on the clock."
                % (len(state["questions"]), format_duration(duration))
            )
        else:
            print(
                "%d question(s), %s on the clock."
                % (len(state["questions"]), format_duration(duration))
            )
        print("Deadline %s UTC." % (state["clock"]["deadline_utc"],))
        print("")
        print("Work here:")
        print("  %s" % (workspace,))
        if config["gated"]:
            first = state["questions"][0]
            print("    %s/solution.py" % (first["dir"],))
            print("    %s/level1.md" % (first["dir"],))
            print("")
            print(
                "Levels 2 to %d are locked. Each one appears when the level "
                "before it passes." % (len(state["questions"]),)
            )
        else:
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
        # In a gated session exactly one level is open at a time, so "submit"
        # with no argument is unambiguous and means that one. Every level shares
        # a directory name, so falling back to listing directories would offer
        # the same answer four times.
        open_now = [q for q in questions if q["state"] == STATE_UNLOCKED]
        if len(open_now) == 1:
            return open_now[0]
        raise SessionError(
            "Which one? Pass --question with one of: %s"
            % (", ".join(sorted(set(q["dir"] for q in questions))),),
            EXIT_USAGE,
        )
    needle = str(wanted).strip().lower()
    for question in questions:
        if needle in (str(question["slot"]), question["id"].lower()):
            return question
    # Only match on directory when it identifies a single entry, which is true
    # for GCA and false for every level of an ICA project.
    matches = [q for q in questions if q["dir"].lower() == needle]
    if len(matches) == 1:
        return matches[0]
    if matches:
        raise SessionError(
            "%r is the whole project. Pass a level number instead." % (wanted,),
            EXIT_USAGE,
        )
    raise SessionError(
        "No question %r in this session. Have: %s"
        % (wanted, ", ".join(sorted(set(q["dir"] for q in questions)))),
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


def run_gated_grader(
    state: Dict[str, Any], question: Dict[str, Any], solution: Path, timeout: float
) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    """Grade an ICA level and every level below it.

    The combined score is what counts. Passing level 4's new tests while level
    1 has started failing is not progress, and reporting it as a pass would
    teach exactly the wrong habit.
    """
    per_level = []
    passed = 0
    total = 0
    broke_earlier = False
    blocking = None

    for entry in state["questions"]:
        if entry["slot"] > question["slot"]:
            break
        report = run_grader(entry, solution, timeout)
        here = report.get("outcome", "unknown")
        per_level.append(
            {
                "slot": entry["slot"],
                "passed": report.get("passed", 0),
                "total": report.get("total", 0),
                "outcome": here,
            }
        )
        passed += report.get("passed", 0)
        total += report.get("total", 0)
        if here in NO_TESTS_RAN:
            # Nothing ran at this level, so there is nothing to add up. Stop
            # here rather than paying the timeout again at every remaining
            # level, and remember why.
            blocking = here
            break
        if entry["slot"] < question["slot"] and here != "pass":
            broke_earlier = True

    # The combined verdict must not be derived from the sums alone. A level that
    # timed out, crashed, failed to import, or had no solution file reports
    # 0 of 0, which cannot move `passed == total`, so the earlier levels' counts
    # were enough on their own to declare a pass. That marked the level passed,
    # unlocked the next one, and told the candidate 100% for code that never ran.
    if blocking is not None:
        outcome = blocking
    elif broke_earlier:
        # Breaking a level below is never a pass, whatever the totals say.
        outcome = "partial" if passed else "fail"
    elif total and passed == total:
        outcome = "pass"
    elif passed:
        outcome = "partial"
    else:
        outcome = "fail"

    if blocking is not None:
        # The counts are real, and they are the levels that did run, so they are
        # kept. The credit is not: METHODOLOGY says a level that never ran is a
        # zero, and report averages this figure. Leaving it at 1.0 would let a
        # level that hung be worth full marks.
        credit = 0.0
    elif total:
        credit = round(float(passed) / total, 4)
    else:
        credit = 0.0

    combined = {
        "passed": passed,
        "total": total,
        "credit": credit,
        "outcome": outcome,
        "regression": broke_earlier,
    }
    return combined, per_level


def unlock_next(
    workspace: Path, state: Dict[str, Any], now: float
) -> Optional[Dict[str, Any]]:
    """Reveal the next level, if the one before it has been passed."""
    for entry in state["questions"]:
        if entry["state"] != STATE_LOCKED:
            continue
        previous = state["questions"][entry["slot"] - 2]
        if previous["state"] != STATE_PASSED:
            return None
        entry["state"] = STATE_UNLOCKED
        materialize_level(workspace, entry["dir"], entry)
        add_event(state, now, "level_unlocked", level=entry["slot"])
        return entry
    return None


def command_unlock(args: argparse.Namespace) -> int:
    now = resolve_now(args.now)
    workspace = resolve_workspace(args)
    state = read_state(workspace)

    phase = classify(state, now)
    if phase == STATE_EXPIRED:
        state = finalize(workspace, state, now, END_REASON_TIME)
        phase = STATE_ENDED
    if phase == STATE_ENDED:
        sys.stderr.write("This session is over. Nothing more unlocks.\n")
        return EXIT_EXPIRED

    if not FORMATS[state["format"]]["gated"]:
        raise SessionError(
            "%s sessions have every question unlocked already."
            % (state["format"].upper(),),
            EXIT_USAGE,
        )

    entry = unlock_next(workspace, state, now)
    if entry is None:
        locked = [q for q in state["questions"] if q["state"] == STATE_LOCKED]
        if not locked:
            print("Every level is already unlocked.")
            return EXIT_OK
        current = [q for q in state["questions"] if q["state"] == STATE_UNLOCKED]
        name = current[0]["title"] if current else "the current level"
        sys.stderr.write(
            "Still locked. %s has to pass first, and that means its own tests "
            "plus every level before it.\n" % (name,)
        )
        return EXIT_USAGE

    write_state(workspace, state)
    print("Unlocked %s." % (entry["title"],))
    print("")
    print("  %s/level%d.md" % (entry["dir"], entry["slot"]))
    print("  %s/tests_public_level%d.py" % (entry["dir"], entry["slot"]))
    print("")
    print("Keep working in the same solution.py. The earlier levels keep being tested.")
    return EXIT_OK


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
    if question["state"] == STATE_LOCKED:
        raise SessionError(
            "%s is locked. Pass level %d first."
            % (question["title"], question["slot"] - 1),
            EXIT_USAGE,
        )

    solution = workspace / question["dir"] / "solution.py"
    gated = FORMATS[state["format"]]["gated"]

    if gated:
        # Regression grading. Every level up to this one is re-run, so a level 4
        # feature that broke level 1 costs the marks it just broke rather than
        # scoring full for the new work.
        report, per_level = run_gated_grader(state, question, solution, args.timeout)
    else:
        report = run_grader(question, solution, args.timeout)
        per_level = None

    # Grading is slow and holds no lock. Everything after it is the
    # read-modify-write, so the state is taken fresh under an exclusive lock and
    # only this submission's delta is applied. Locking just the write would not
    # help: the stale copy read before grading is what does the clobbering.
    with session_lock(workspace):
        state = read_state(workspace)

        phase = classify(state, now)
        if phase == STATE_EXPIRED:
            state = finalize(workspace, state, now, END_REASON_TIME)
            phase = STATE_ENDED
        if phase == STATE_ENDED:
            # The clock ran out while this was being graded, or another command
            # ended the session. Either way it is late now.
            sys.stderr.write("Time is up. This submission was not accepted.\n")
            return EXIT_EXPIRED

        question = find_question(state, args.question)
        return _record_submission(
            args, workspace, state, question, report, per_level, now, gated
        )


def _record_submission(
    args: argparse.Namespace,
    workspace: Path,
    state: Dict[str, Any],
    question: Dict[str, Any],
    report: Dict[str, Any],
    per_level: Optional[List[Dict[str, Any]]],
    now: float,
    gated: bool,
) -> int:
    """Apply a graded submission to fresh state. Caller holds the lock."""
    question["attempts"] = question.get("attempts", 0) + 1
    question["last_submit_epoch"] = now
    question["result"] = {
        "passed": report.get("passed", 0),
        "total": report.get("total", 0),
        "credit": report.get("credit", 0.0),
        "outcome": report.get("outcome", "unknown"),
        "at_epoch": now,
    }
    if per_level is not None:
        question["result"]["per_level"] = per_level
        question["result"]["regression"] = report.get("regression", False)

        # Write the fresh figures back onto the earlier levels too.
        #
        # Every level was just re-graded against the current solution, but only
        # the submitted level's entry was being updated, so a level 1 that this
        # submission broke kept the passing result it recorded twenty minutes
        # ago. `submit` said "regression" and `report` then said "reached and
        # passed 3 of 4 levels", which is the exact thing the README claims this
        # format catches.
        #
        # Levels store cumulative counts, so the prefix sums are rebuilt rather
        # than the per-level counts written straight in, or report would
        # contradict its own "earlier levels included" line. States are left
        # alone deliberately: demoting a regressed level would leave more than
        # one entry unlocked and break bare `submit`.
        running_passed = 0
        running_total = 0
        by_slot = dict((line["slot"], line) for line in per_level)
        for entry in state["questions"]:
            line = by_slot.get(entry["slot"])
            if line is None:
                continue
            running_passed += line["passed"]
            running_total += line["total"]
            if entry["slot"] == question["slot"]:
                break
            existing = entry.get("result") or {}
            entry["result"] = {
                "passed": running_passed,
                "total": running_total,
                "credit": (
                    round(float(running_passed) / running_total, 4)
                    if running_total
                    else 0.0
                ),
                "outcome": line["outcome"],
                "at_epoch": now,
                "attempts_note": existing.get("attempts_note"),
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

    unlocked = None
    if gated and report.get("outcome") == "pass":
        question["state"] = STATE_PASSED
        unlocked = unlock_next(workspace, state, now)

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
        elif outcome == "crashed":
            print(
                "%s/solution.py stopped the test run before it finished. Nothing "
                "could be graded." % (question["dir"],)
            )
        else:
            label = question["title"] if gated else question["dir"]
            print(
                "%s  %d of %d hidden tests passed (%.0f%%)."
                % (label, report["passed"], report["total"], report["credit"] * 100)
            )
            if per_level and len(per_level) > 1:
                print("")
                for line in per_level:
                    marker = "  " if line["passed"] == line["total"] else "! "
                    print(
                        "  %slevel %d   %d/%d"
                        % (marker, line["slot"], line["passed"], line["total"])
                    )
                if report.get("regression"):
                    print("")
                    print("An earlier level is failing. That is a regression, not progress.")
        if unlocked is not None:
            print("")
            print("Passed. Unlocked %s: %s/level%d.md" % (unlocked["title"], unlocked["dir"], unlocked["slot"]))
        print("")
        print("attempt %d, %s left on the clock." % (question["attempts"], payload["remaining_display"]))

    if report.get("outcome") == "timeout":
        return EXIT_TIMEOUT
    if report.get("outcome") in ("crashed", "import_error", "missing"):
        return EXIT_NOT_GRADED
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
    gated = FORMATS[state["format"]]["gated"]
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
            if gated:
                # Each level is graded cumulatively, so its score already
                # contains every level below it. Summing them counts level 1's
                # tests four times and reports 187 distinct tests where there
                # are 79. The deepest level reached is the real figure.
                total_tests = result["total"]
                passed_tests = result["passed"]
            else:
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
                "hints": question.get("hints", 0),
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
    hints_given = sum(line["hints"] for line in lines)
    clock = state["clock"]
    # Time used can never exceed the time the session had. A session abandoned
    # hours after its deadline records that later moment as its ending, which
    # otherwise reported "used 3:03:20 of 1:10:00".
    end_point = clock.get("ended_epoch")
    if end_point is None:
        end_point = now
    used = min(end_point, clock["deadline_epoch"]) - clock["started_epoch"]

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
        "hints": hints_given,
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
        if gated:
            print("  %-10s %s" % (line["title"], line["summary"]))
        else:
            print(
                "  %-4s %-12s %-10s %s"
                % (line["dir"], line["summary"], line["difficulty"], line["title"])
            )
    print("")
    if gated:
        print("Reached and passed %d of %d levels." % (solved, count))
        if total_tests:
            print(
                "%d of %d hidden tests passing at the deepest level reached, "
                "earlier levels included." % (passed_tests, total_tests)
            )
    else:
        print("Solved %d of %d." % (solved, count))
        if total_tests:
            print(
                "%d of %d hidden tests passed on the questions that ran."
                % (passed_tests, total_tests)
            )
    print(
        "Overall: %.0f%% credit across all %d %s, %s."
        % (
            credit * 100,
            count,
            ("level" if count == 1 else "levels")
            if gated
            else ("question" if count == 1 else "questions"),
            payload["band"],
        )
    )
    if gated and any((q.get("result") or {}).get("regression") for q in questions):
        # The percentage can look healthy while an earlier level is broken,
        # because most of the suite still passes. Saying "strong" over a
        # regression is the flattering reading, and this format exists to
        # punish exactly that.
        print(
            "An earlier level is failing. Whatever the percentage says, this is "
            "a regression: the work broke something that used to pass."
        )
    if state["mode"] == "interview":
        if hints_given:
            print(
                "%d hint%s given. Solving it with help is a different result "
                "from solving it alone, and the debrief should say so."
                % (hints_given, "" if hints_given == 1 else "s")
            )
        else:
            print("No hints given.")
    print("")
    print(payload["score_note"])
    return EXIT_OK


def command_list(args: argparse.Namespace) -> int:
    """Show past sessions, newest first.

    Without this the only reachable session is whatever the pointer file names,
    so a sitting from yesterday is on disk but effectively lost. Sessions are
    read straight from their state files rather than from an index, because an
    index is another thing that can disagree with the truth.
    """
    root = sessions_root()
    rows = []
    if root.is_dir():
        for entry in root.iterdir():
            if not state_path(entry).exists():
                continue
            try:
                state = read_state(entry)
            except SessionError:
                # A session written by a different schema version still deserves
                # a line, so it can be seen and deleted.
                rows.append(
                    {
                        "session_id": entry.name,
                        "unreadable": True,
                        "workspace": str(entry),
                    }
                )
                continue
            clock = state["clock"]
            solved = sum(
                1
                for question in state["questions"]
                if (question.get("result") or {}).get("outcome") == "pass"
            )
            rows.append(
                {
                    "session_id": state["session_id"],
                    "format": state["format"],
                    "mode": state["mode"],
                    "started_utc": clock["started_utc"],
                    "started_epoch": clock["started_epoch"],
                    "state": classify(state, resolve_now(args.now)),
                    "end_reason": clock.get("end_reason"),
                    "solved": solved,
                    "questions": len(state["questions"]),
                    "workspace": state["workspace"],
                    "unreadable": False,
                }
            )

    rows.sort(key=lambda row: row.get("started_epoch", 0), reverse=True)
    if args.limit and args.limit > 0:
        rows = rows[: args.limit]

    if args.json:
        print(json.dumps(rows, indent=2))
        return EXIT_OK

    if not rows:
        print("No sessions yet under %s" % (root,))
        return EXIT_OK

    current = read_pointer()
    for row in rows:
        if row["unreadable"]:
            print("  %-28s (unreadable, from an older version)" % (row["session_id"],))
            continue
        marker = "*" if current is not None and str(current) == row["workspace"] else " "
        print(
            "%s %-28s %-4s %-9s %-8s %d/%d solved  %s"
            % (
                marker,
                row["session_id"],
                row["format"],
                row["mode"],
                row["state"],
                row["solved"],
                row["questions"],
                row["started_utc"],
            )
        )
    print("")
    print("Work on an older one with --session <id>. A * marks the current session.")
    return EXIT_OK


def command_hint(args: argparse.Namespace) -> int:
    """Record that the interviewer gave a nudge.

    Interview mode allows hints because a real interviewer does, but needing one
    is signal, and signal that vanishes is useless. The count and the wording go
    into the session so the debrief can say "you got there, with two nudges on
    the data structure" rather than just reporting a pass.

    Exam mode refuses. A proctor who hands out hints is not proctoring.
    """
    now = resolve_now(args.now)
    workspace = resolve_workspace(args)
    state = read_state(workspace)

    if state["mode"] != "interview":
        raise SessionError(
            "Hints are an interview-mode thing. This is an exam: clarify the "
            "wording if it is ambiguous, but do not give the approach away.",
            EXIT_USAGE,
        )

    phase = classify(state, now)
    if phase == STATE_EXPIRED:
        state = finalize(workspace, state, now, END_REASON_TIME)
        phase = STATE_ENDED
    if phase == STATE_ENDED:
        sys.stderr.write("Time is up. Nothing more to record.\n")
        return EXIT_EXPIRED

    with session_lock(workspace):
        state = read_state(workspace)
        question = find_question(state, args.question)
        question["hints"] = question.get("hints", 0) + 1
        add_event(state, now, "hint", question=question["dir"], note=args.note or "")
        write_state(workspace, state)

    payload = {
        "question": question["dir"],
        "hints": question["hints"],
        "note": args.note or "",
    }
    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        print(
            "Noted: hint %d on %s.%s"
            % (question["hints"], question["dir"], (" " + args.note) if args.note else "")
        )
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
    parser.add_argument(
        "--version", action="version", version="interview-sim %s" % (VERSION,)
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
    start.add_argument("--project", default=None, help="ICA project id")
    start.add_argument("--preset", default=None, help="company preset, e.g. --preset ramp")
    start.add_argument("--seed", type=int, default=None, help="repeatable question choice")
    start.add_argument(
        "--slot", type=int, default=None,
        help="difficulty slot to draw from, 1 easiest. Useful with --mode interview.",
    )
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

    listing = subparsers.add_parser("list", help="show past sessions")
    listing.add_argument("--limit", type=int, default=20)
    add_common(listing)
    listing.set_defaults(func=command_list)

    hint = subparsers.add_parser("hint", help="record an interviewer hint")
    hint.add_argument("--question", default=None)
    hint.add_argument("--note", default=None, help="what the hint actually was")
    hint.add_argument("--workspace", default=None)
    hint.add_argument("--session", default=None)
    add_common(hint)
    hint.set_defaults(func=command_hint)

    unlock = subparsers.add_parser("unlock", help="reveal the next ICA level")
    unlock.add_argument("--workspace", default=None)
    unlock.add_argument("--session", default=None)
    add_common(unlock)
    unlock.set_defaults(func=command_unlock)

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
    # argparse cannot tell a typed --format from its default, and a preset with
    # an unknown format needs to know which it was.
    argv_list = sys.argv[1:] if argv is None else list(argv)
    args.format_given = any(
        item == "--format" or item.startswith("--format=") for item in argv_list
    )
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
