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
import ast
import calendar
import json
import os
import random
import shutil
import subprocess
import sys
import tempfile
import textwrap
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

VERSION = "0.29.5"
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
    # Slot 3 is the band a forty-five minute technical screen actually sits in.
    # Without a default slot, selection took slots[:1], which is always slot 1,
    # so the headline interview mode served an eight-minute warm-up with
    # forty-five minutes on the clock and drew from three questions forever.
    "interview": {"questions": 1, "minutes": 45, "slot": 3},
}

SKILL_DIR = Path(__file__).resolve().parent.parent
QUESTIONS_DIR = SKILL_DIR / "questions"

SESSIONS_DIR_NAME = "interview-sim-sessions"
LEGACY_ROOT = Path.home() / "interview-sim-sessions"
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


def slugify(value: str, limit: int = 24) -> str:
    """Reduce free text to something safe to put in a path.

    --company and --round are labels typed by whoever started the sitting, and
    they now land in a directory name rather than only in state.json. So this
    has to survive "Ernst & Young", "Goldman Sachs", a pasted tab, and a name
    that is nothing but punctuation, without ever producing a path that escapes
    the sessions root or starts with a dash.

    Letters outside ASCII are kept rather than stripped. Restricting to ASCII
    made a company written in a non-Latin script vanish from its own directory
    name, which is worse than the thing it was guarding against: everything
    dangerous in a path (the separators, the dots, the control characters) is
    not alphanumeric, so isalnum() already excludes it.

    Returns "" when nothing usable survives, which callers treat as "no label"
    rather than substituting a placeholder.
    """
    kept = []
    for char in value.strip().lower():
        if char.isalnum():
            kept.append(char)
        elif kept and kept[-1] != "-":
            kept.append("-")
    slug = "".join(kept).strip("-")
    if len(slug) > limit:
        slug = slug[:limit].rstrip("-")
    return slug


def build_session_id(
    fmt: str, now: float, company: Optional[str], round_name: Optional[str]
) -> str:
    """Name the directory after the sitting it holds.

    A column of gca-20260816T142530Z tells you nothing you wanted to know. What
    you are looking for in a sidebar is which company and which round, so those
    lead, and the format only appears when no round was given, because "oa" and
    "pairing" are what candidates call these and "gca" is our own jargon.

    The timestamp is a directory below that rather than more name, so sittings
    for one company and round stack up under a single folder instead of filling
    a sidebar with near-identical rows. Sorting inside the folder stays
    chronological because the timestamp is the whole leaf name.

    The separator is always "/", including on Windows, because this string is
    both a path fragment and the id that gets printed and typed back into
    --session. pathlib accepts it in either role.
    """
    parts = []
    for label in (company, round_name):
        slug = slugify(label or "")
        if slug:
            parts.append(slug)
    if not round_name or not slugify(round_name):
        parts.append(fmt)
    group = "-".join(parts)
    return "%s/%s" % (group, time.strftime("%Y%m%dT%H%M%SZ", time.gmtime(now)))


def workspace_label(workspace: Path) -> str:
    """A session's name as it sits under its root, e.g. stripe-oa/20260816T142530Z.

    Falls back to the leaf directory name for a workspace somewhere else
    entirely, which --workspace allows.
    """
    try:
        resolved = workspace.resolve()
    except OSError:
        return workspace.name
    for root in history_roots():
        try:
            return resolved.relative_to(root.resolve()).as_posix()
        except (ValueError, OSError):
            continue
    return workspace.name


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


def paragraph(text: str) -> None:
    """Print prose wrapped to the terminal rather than to the source line.

    Several of the things this tool has to say are two or three sentences long,
    and a terminal breaks them wherever the column runs out, mid-word. Capped at
    88 columns because a paragraph running the full width of a wide terminal is
    harder to read than a narrow one, and shrunk to fit a narrow one.

    Only for prose. Anything the eye scans down a column, paths, tables, and
    scores, is printed as-is and left to the terminal.
    """
    width = shutil.get_terminal_size((88, 24)).columns
    print(textwrap.fill(text, width=max(40, min(88, width - 1))))


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
    # Valid JSON is not a valid session. A file holding a list, or a dict
    # missing the keys the engine indexes, used to get all the way to an
    # AttributeError or a KeyError and exit 1 with a traceback, which is not in
    # the documented exit-code contract the skill branches on. It also took
    # `list` down entirely: one unreadable session directory and the whole
    # listing died rather than showing the other sessions.
    if not isinstance(state, dict):
        raise SessionError(
            "Session state at %s is not a session (found %s). Start a new one."
            % (path, type(state).__name__),
            EXIT_ENVIRONMENT,
        )
    clock = state.get("clock")
    required = (
        isinstance(clock, dict)
        and "started_epoch" in clock
        and "deadline_epoch" in clock
        and isinstance(state.get("questions"), list)
        and "session_id" in state
        and "format" in state
        and "mode" in state
    )
    if not required:
        raise SessionError(
            "Session state at %s is missing fields this build needs. "
            "Start a new session." % (path,),
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


def write_json(path: Path, payload: Dict[str, Any]) -> None:
    """Write a JSON file atomically, so a reader never sees half of one."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.parent / (path.name + ".tmp")
    with open(str(tmp), "w") as handle:
        json.dump(payload, handle, indent=2, sort_keys=False)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(str(tmp), str(path))


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
    """Where sessions live: beside the work, not in a corner of your home dir.

    This used to always be ~/interview-sim-sessions, which kept session files
    out of *this* repository and, by over-application, out of the project the
    candidate was actually standing in. The result was a tool that announced a
    path somewhere else and expected you to go and find it, when the whole point
    is coding in your own editor in your own project.

    So it defaults to the working directory. Each session writes a .gitignore
    that ignores itself, which handles the thing the home directory was really
    protecting against.
    """
    override = os.environ.get("INTERVIEW_SIM_HOME")
    if override:
        return Path(override).expanduser()
    return Path.cwd() / SESSIONS_DIR_NAME


def history_roots() -> List[Path]:
    """Every place sessions might be, newest scheme first.

    Sessions sat before the move, or from another project directory, are still
    yours. History that quietly forgets half of itself is worse than no history.
    """
    if os.environ.get("INTERVIEW_SIM_HOME"):
        # An explicit root is the whole answer. Adding the usual places to it
        # would mean a test, or anyone pointing this somewhere deliberate, saw
        # sessions from directories they had not named.
        return [sessions_root()]
    roots = [sessions_root()]
    for candidate in (LEGACY_ROOT,):
        if candidate not in roots:
            roots.append(candidate)
    return roots


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
    try:
        current = Path.cwd().resolve()
    except OSError:
        # The working directory was deleted out from under us. Fall through to
        # the pointer rather than taking down every command.
        return None
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
        if state_path(workspace).exists():
            return workspace
        # Ids have two segments now, and the half worth typing is the timestamp.
        # Accepting the leaf on its own saves retyping the company, as long as
        # it picks out exactly one session: guessing between two would open the
        # wrong one silently.
        matches = [
            found
            for found, _ in walk_sessions()
            if workspace_label(found).split("/")[-1] == args.session
        ]
        if len(matches) == 1:
            return matches[0]
        if len(matches) > 1:
            raise SessionError(
                "%r matches %d sessions. Name one of these in full:\n  %s"
                % (
                    args.session,
                    len(matches),
                    "\n  ".join(sorted(workspace_label(m) for m in matches)),
                ),
                EXIT_USAGE,
            )
        raise SessionError("No session named %r" % (args.session,), EXIT_NO_SESSION)

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



def find_editor() -> Optional[Tuple[str, str]]:
    """The GUI editor to use, as (path, family), or None.

    PATH first, then the places macOS keeps the CLI when nobody ran the "install
    'code' command in PATH" step, which is most people. Skipping that lookup is
    how this ended up launching Finder on a machine with VS Code open in front
    of it: `which code` found nothing, the file manager was the next candidate,
    and the candidate got thrown out of their editor at the moment their clock
    started.

    The family decides the flags, since -g is a VS Code idea and passing it to
    something else would open a file named "-g".
    """
    for name in ("code", "cursor", "subl", "zed"):
        found = shutil.which(name)
        if found:
            return found, name

    bundles = (
        ("Visual Studio Code.app", "code", "code"),
        ("Visual Studio Code - Insiders.app", "code-insiders", "code"),
        ("Cursor.app", "cursor", "cursor"),
        ("Sublime Text.app", "subl", "subl"),
        ("Zed.app", "zed", "zed"),
    )
    roots = (Path("/Applications"), Path.home() / "Applications")
    for root in roots:
        for app, binary, family in bundles:
            candidate = root / app / "Contents" / "Resources" / "app" / "bin" / binary
            if candidate.exists():
                return str(candidate), family
    return None


def open_in_editor(workspace: Path, focus: Optional[Path] = None) -> None:
    """Open the workspace in the user's editor, best effort.

    $EDITOR is not used: it is usually a terminal editor and launching one from
    here would fight the shell for the terminal the candidate is working in.
    A GUI editor if there is one, otherwise the platform file manager.

    Opening the folder alone left someone looking at a file tree with a clock
    already running, which is a strange way to start a timed assessment. Where
    the editor can be told, the file they are about to write in is opened and
    focused, so the session begins on the first line of their own solution.
    """
    candidates = []
    editor = find_editor()
    if editor is not None:
        found, family = editor
        if focus is not None and focus.exists():
            if family in ("code", "cursor"):
                # -r reuses the window that is already open and -g goes to the
                # file in it. Passing the workspace folder as well opened a
                # second window rooted at the session directory, which threw the
                # candidate out of the editor they were working in to look at a
                # file tree. Sessions live in the working directory now, so the
                # file is already inside the project they have open: there is
                # nothing to open, only somewhere to navigate to.
                candidates.append([found, "-r", "-g", str(focus)])
            else:
                candidates.append([found, str(focus)])
        else:
            candidates.append([found, str(workspace)])
    elif sys.platform == "darwin":
        # No editor at all. A file manager is a poor substitute and a terrible
        # surprise mid-session, so it only happens when there was nothing
        # better, and never in place of an editor that was simply not on PATH.
        candidates.append(["open", str(workspace)])
    elif sys.platform.startswith("linux"):
        candidates.append(["xdg-open", str(workspace)])
    elif os.name == "nt":
        opener = shutil.which("explorer")
        if opener:
            candidates.append([opener, str(workspace)])

    for command in candidates:
        try:
            subprocess.Popen(
                command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )
            return
        except OSError:
            continue


# Three is the corpus's own floor (MIN_MUTANTS in tools/qa.py). A generated
# question passes the same bar as a curated one or it does not run.
GENERATED_MIN_MUTANTS = 3


def patch_mutant_fields(path: Path) -> Optional[Tuple[str, str]]:
    """(OLD, NEW) if this mutant is a patch, None if it is a full solution.

    A mutant used to be the entire reference re-typed with one line changed,
    which made mutants most of the tokens in a generated set: forty lines of
    copying to express a one-line break. A patch mutant declares just the
    break, as two module-level strings, and the engine composes it against
    reference.py before grading. Full standalone mutants still work, for the
    rare break a substitution cannot express.

    Read with ast rather than executed: a full mutant defines functions and
    would run on import, and the only question here is whether OLD and NEW
    string constants exist at the top level.
    """
    try:
        tree = ast.parse(path.read_text())
    except (SyntaxError, OSError):
        # Not parseable here; the grader will fail it as a full mutant and
        # name it, which is the better error.
        return None
    old = new = None
    for node in tree.body:
        if not isinstance(node, ast.Assign) or len(node.targets) != 1:
            continue
        target = node.targets[0]
        if not isinstance(target, ast.Name) or target.id not in ("OLD", "NEW"):
            continue
        value = node.value
        if isinstance(value, ast.Constant) and isinstance(value.value, str):
            if target.id == "OLD":
                old = value.value
            else:
                new = value.value
    if old is None or new is None:
        return None
    return old, new


def load_generated(directory: Path, count: int) -> List[Dict[str, Any]]:
    """Load questions written outside the bank, and check them before use.

    This is the primary path: a question written for this sitting, from what
    was researched about the company, rather than drawn from a fixed corpus.

    It passes the same three checks the corpus passes in CI. The reference must
    pass the hidden suite, or the question is unanswerable. The untouched
    starter must fail it, or the question asks for nothing. And every
    deliberately-wrong solution in mutants/ must be caught, or the suite cannot
    tell a wrong answer from a right one and the grade would be worthless.

    All of it happens before the clock starts, which is the only time a
    rejection is free.
    """
    directory = Path(directory).expanduser().resolve()
    if not directory.is_dir():
        raise SessionError("No such directory: %s" % (directory,), EXIT_BANK)
    # The source set is the answer key: reference.py and tests_hidden.py sit in
    # it. Built inside the directory the candidate is working from, it shows up
    # in their file tree one click from the problem, which has happened twice.
    # Instructions drift; refusals do not.
    try:
        directory.relative_to(Path.cwd().resolve())
        raise SessionError(
            "%s is inside the working directory, where the candidate can read "
            "the answer key (reference.py, tests_hidden.py). Build generated "
            "questions in a temp directory outside it." % (directory,),
            EXIT_BANK,
        )
    except ValueError:
        pass

    candidates = sorted(
        entry for entry in directory.iterdir()
        if entry.is_dir() and not entry.name.startswith((".", "_"))
    )
    if (directory / "meta.json").exists():
        candidates = [directory]
    if not candidates:
        raise SessionError(
            "No question directories in %s. Each question is its own directory "
            "with meta.json, problem.md, starter.py, tests_public.py, "
            "tests_hidden.py and reference.py." % (directory,),
            EXIT_BANK,
        )
    if len(candidates) < count:
        raise SessionError(
            "%s holds %d question(s) but %d were asked for."
            % (directory, len(candidates), count),
            EXIT_BANK,
        )

    grader = Path(__file__).resolve().parent / "grade.py"
    questions = []
    for index, entry in enumerate(candidates[:count], start=1):
        for name in ("meta.json", "problem.md", "starter.py", "tests_public.py",
                     "tests_hidden.py", "reference.py"):
            if not (entry / name).exists():
                raise SessionError("%s is missing %s" % (entry, name), EXIT_BANK)
        try:
            with open(str(entry / "meta.json"), "r") as handle:
                meta = json.load(handle)
        except ValueError as exc:
            raise SessionError("%s/meta.json is not valid JSON: %s" % (entry, exc), EXIT_BANK)
        if not isinstance(meta, dict):
            raise SessionError("%s/meta.json is not an object" % (entry,), EXIT_BANK)

        reference = _grade_once(grader, entry, entry / "reference.py")
        if reference.get("total", 0) == 0:
            # The most likely author of a generated question is a model, and the
            # most likely mistake is pytest-style plain functions, which stdlib
            # unittest collects as nothing. Without this message, that shows up
            # as "reference scores 0/0" and the diagnosis costs a trip through
            # the engine source with somebody waiting for a clock.
            raise SessionError(
                "%s produced no runnable tests: unittest collected nothing from "
                "tests_hidden.py. Tests live in a class "
                "(class TestX(unittest.TestCase)) with test_ methods; plain "
                "pytest-style functions collect as zero." % (entry.name,),
                EXIT_BANK,
            )
        if "def test_" not in (entry / "tests_public.py").read_text():
            raise SessionError(
                "%s has no tests in tests_public.py, so the candidate has no "
                "samples to run." % (entry.name,),
                EXIT_BANK,
            )
        if reference.get("outcome") != "pass":
            raise SessionError(
                "%s is unanswerable: its own reference solution scores %d/%d (%s). "
                "Fix the question or the tests before anyone sits it."
                % (entry.name, reference.get("passed", 0), reference.get("total", 0),
                   reference.get("outcome")),
                EXIT_BANK,
            )
        starter = _grade_once(grader, entry, entry / "starter.py")
        if starter.get("outcome") == "pass":
            raise SessionError(
                "%s asks for nothing: the untouched starter already passes its "
                "hidden suite." % (entry.name,),
                EXIT_BANK,
            )

        # The mutation gate, same as CI runs on the corpus. Generated questions
        # used to skip it, disclosed as "nothing has proved this suite can tell
        # a wrong answer from a right one". Now that generation is the primary
        # path rather than the fallback, that disclosure would cover every
        # session, which is another way of saying the gate had stopped being
        # the product's quality claim. Whoever writes the question writes
        # mutants/ beside it, and a suite that lets one survive is rejected
        # here, before the clock starts, when rewriting is free.
        mutants = (
            sorted(p for p in (entry / "mutants").glob("*.py")
                   if not p.name.startswith("_"))
            if (entry / "mutants").is_dir()
            else []
        )
        if len(mutants) < GENERATED_MIN_MUTANTS:
            raise SessionError(
                "%s has %d mutant(s), needs %d. A wrong answer the hidden suite "
                "has never been shown to catch is a grade nobody should trust: "
                "write %d plausible wrong solutions into %s/mutants/ and try "
                "again."
                % (entry.name, len(mutants), GENERATED_MIN_MUTANTS,
                   GENERATED_MIN_MUTANTS, entry.name),
                EXIT_BANK,
            )
        survivors = []
        reference_text = (entry / "reference.py").read_text()
        scratch = None
        try:
            for mutant in mutants:
                fields = patch_mutant_fields(mutant)
                if fields is None:
                    verdict = _grade_once(grader, entry, mutant)
                else:
                    old_text, new_text = fields
                    hits = reference_text.count(old_text)
                    if hits != 1:
                        raise SessionError(
                            "%s/mutants/%s: OLD %s in reference.py. A patch "
                            "mutant quotes a snippet of the reference verbatim, "
                            "and the snippet has to pin down one place."
                            % (entry.name, mutant.name,
                               "matches nothing" if hits == 0
                               else "matches %d places" % (hits,)),
                            EXIT_BANK,
                        )
                    if old_text == new_text:
                        raise SessionError(
                            "%s/mutants/%s: OLD and NEW are identical, so this "
                            "mutant is the reference and proves nothing."
                            % (entry.name, mutant.name),
                            EXIT_BANK,
                        )
                    if scratch is None:
                        scratch = Path(tempfile.mkdtemp(prefix="sim-mutants-"))
                    composed = scratch / mutant.name
                    composed.write_text(
                        reference_text.replace(old_text, new_text)
                    )
                    verdict = _grade_once(grader, entry, composed)
                if verdict.get("outcome") == "pass":
                    survivors.append(mutant.name)
        finally:
            if scratch is not None:
                shutil.rmtree(str(scratch), ignore_errors=True)
        if survivors:
            raise SessionError(
                "%s graded a wrong answer as correct: %s passed the hidden "
                "suite. The suite cannot discriminate. Strengthen the tests, "
                "not the mutant."
                % (entry.name, ", ".join(survivors)),
                EXIT_BANK,
            )

        meta["_dir"] = entry
        meta["_format"] = "generated"
        meta.setdefault("id", entry.name)
        meta.setdefault("title", entry.name)
        meta.setdefault("difficulty", "generated")
        meta["slot"] = index
        meta["_hidden_tests"] = reference.get("total", 0)
        questions.append(meta)
    return questions


def _grade_once(grader: Path, question_dir: Path, solution: Path) -> Dict[str, Any]:
    proc = subprocess.Popen(
        [sys.executable, str(grader), "--question", str(question_dir),
         "--solution", str(solution), "--json"],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True,
    )
    try:
        out, err = proc.communicate(timeout=120)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.communicate()
        raise SessionError("Checking %s took too long." % (question_dir.name,), EXIT_BANK)
    try:
        return json.loads(out)
    except ValueError:
        raise SessionError(
            "Could not check %s: %s" % (question_dir.name, (err or out).strip()[:200]),
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
    try:
        with open(str(meta_file), "r") as handle:
            meta = json.load(handle)
    except ValueError as exc:
        raise SessionError("%s is not valid JSON: %s" % (meta_file, exc), EXIT_BANK)
    if not isinstance(meta, dict) or "id" not in meta:
        raise SessionError("%s has no id" % (meta_file,), EXIT_BANK)

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


def topic_match(question: Dict[str, Any], wanted: List[str]) -> bool:
    """Does this question cover any of the topics asked for?

    Substring matching in both directions, because the topics that come out of
    research are phrases a person wrote ("sliding window problems", "graphs")
    and the bank's are tags ("sliding window", "graphs"). Requiring them to be
    equal would match almost nothing and quietly fall back to a random draw,
    which looks identical to working.
    """
    tags = [str(tag).lower() for tag in question.get("topics", ())]
    for want in wanted:
        want = want.strip().lower()
        if not want:
            continue
        for tag in tags:
            if want in tag or tag in want:
                return True
    return False


def select_questions(
    fmt: str,
    count: int,
    seed: Optional[int] = None,
    slot: Optional[int] = None,
    explicit_slot: bool = True,
    topics: Optional[List[str]] = None,
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
            if explicit_slot:
                raise SessionError(
                    "No questions in slot %d. Slots available: %s"
                    % (slot, ", ".join(str(value) for value in slots)),
                    EXIT_BANK,
                )
            # A mode default must not fail on a thinner bank than this one.
            slot = min(slots, key=lambda value: (abs(value - slot), value))
        chooser = random.Random(seed)
        options = sorted(by_slot[slot], key=lambda item: item.get("id", ""))
        if topics:
            # The single-slot draw is what interview mode uses, which is what a
            # recorded live round runs as. Skipping topics here meant the one
            # sitting most likely to have a subject attached ignored it.
            matching = [item for item in options if topic_match(item, topics)]
            if len(matching) >= count:
                options = matching
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
    covered = set()
    for slot in slots[:count]:
        options = sorted(by_slot[slot], key=lambda item: item.get("id", ""))
        if topics:
            # Topic is a preference, never a filter that can empty a slot. A
            # session missing its hard question because nothing in the bank was
            # tagged "rate limiting" would be a worse imitation of the format
            # than one whose topics are only partly right.
            #
            # Uncovered topics come first, so four sliding-window questions and
            # one graph question do not produce a session of sliding windows
            # when both were asked for. Spread beats depth here: the point is to
            # rehearse the subjects they are reported to ask about.
            uncovered = [want for want in topics if want not in covered]
            matching = [item for item in options if topic_match(item, uncovered)]
            if not matching:
                matching = [item for item in options if topic_match(item, topics)]
            if matching:
                options = matching
        if len(options) == 1:
            pick = options[0]
        else:
            fresh = [item for item in options if item.get("id") not in seen]
            # Once every question in a slot has been seen, the slot starts over
            # rather than refusing to serve anything.
            pick = chooser.choice(fresh if fresh else options)
        chosen.append(pick)
        for want in topics or []:
            if topic_match(pick, [want]):
                covered.add(want)
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
                # Where the hidden suite lives. Relative to the bank root for
                # bank questions, absolute for generated ones, which sit
                # wherever they were written.
                "source": (
                    str(question["_dir"])
                    if question["_format"] == "generated"
                    else "%s/%s" % (question["_format"], question["_dir"].name)
                ),
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

Or put a clock on screen. Split your terminal and run this in the other pane:

    sim watch

It counts down once a second, turns amber at ten minutes and red at two, and
writes the time into the terminal's tab title so it is there even when the pane
is not. A real assessment keeps a countdown where you cannot avoid it, so this
is the closer imitation. Expect to find it slightly harder with the clock
visible. That is the part being practised.

Grade a question against the hidden tests:

    sim submit --question {first_dir}

It tells you how many hidden tests passed and nothing else. Which ones failed is
the part you work out. Resubmit as often as you like, it only costs time.

When the clock runs out:

    sim report

## Rules

- The clock does not stop. Closing your editor does not pause it.
- Check the time with `sim status`, or keep `sim watch` open; do not guess.
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
        # Clamped: a session ended after its deadline never had more time than
        # it was given, and report already does this.
        elapsed = min(clock["ended_epoch"], clock["deadline_epoch"]) - clock["started_epoch"]
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

    # No company lookup. There used to be a table here, nineteen rows deep, and
    # a local cache beside it, and machinery for deciding when either had gone
    # stale. All of it was answering a question that a search answers better and
    # more currently: what does this company actually run right now.
    #
    # So the shape of the sitting arrives as flags, from whoever just looked it
    # up, and the company is a label on the record rather than a key into
    # anything. What is written down afterwards is a dated note of what was
    # found, which is history and never an answer.
    company = (args.company or "").strip().lower() or None
    round_name = (getattr(args, "round", None) or "").strip().lower() or None

    # Naming a company is a claim about what that company runs, so the format
    # has to be said out loud rather than defaulted into. The old table refused
    # to guess a format for a company it did not know; nothing is known now, so
    # the refusal applies to all of them.
    if company and not getattr(args, "format_given", False):
        raise SessionError(
            "Naming a company does not say what they run, and this will not "
            "guess.\nLook it up, then pass what you found: --company %s "
            "--format gca, or --format ica." % (company,),
            EXIT_USAGE,
        )

    fmt = args.format
    if fmt not in FORMATS:
        raise SessionError(
            "Unknown format %r. Known: %s" % (fmt, ", ".join(sorted(FORMATS))),
            EXIT_USAGE,
        )
    config = FORMATS[fmt]

    # What a company is reported to ask about, from research recorded for them
    # or straight from the flag. It steers which questions are drawn out of the
    # bank. It never reaches into what a question says: the topic is the part of
    # someone else's assessment that is fair to imitate, and the wording is not.
    topics = [item for item in (getattr(args, "topic", None) or []) if item.strip()]

    # Flags beat the mode's defaults, and those beat the format's.
    mode_defaults = MODE_DEFAULTS.get(args.mode, {})
    slot = args.slot
    if slot is None:
        slot = mode_defaults.get("slot")
    count = args.questions
    if count is None:
        count = mode_defaults.get("questions", config["questions"])
    minutes = args.minutes
    if minutes is None:
        minutes = mode_defaults.get("minutes", config["minutes"])
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
            # An expired session ended when the clock ran out, not when it was
            # forced over. Recording "abandoned" at `now` stamped the ending
            # hours late, so status reported elapsed 11:06:40 on a 1:10:00
            # session and exit 4 never fired for it.
            existing_phase = classify(existing_state, now)
            finalize(
                existing_workspace,
                existing_state,
                now,
                END_REASON_TIME if existing_phase == STATE_EXPIRED else END_REASON_ABANDONED,
            )

    if args.generated:
        project = None
        questions = load_generated(Path(args.generated), count)
    elif config["gated"]:
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
        questions = select_questions(
            fmt, count, args.seed, slot,
            explicit_slot=args.slot is not None,
            topics=topics,
        )

    duration = minutes * 60.0
    session_id = build_session_id(fmt, now, company, round_name)

    if args.workspace:
        workspace = Path(args.workspace).expanduser().resolve()
    else:
        workspace = sessions_root() / session_id
        # Two sittings can start in the same second, and the name no longer
        # carries the format to tell a GCA one from an ICA one. Reusing the
        # directory would drop a project on top of the last sitting's q1..q4
        # and overwrite whatever had been written in them, so the second one
        # takes the next free name rather than the same bed.
        if state_path(workspace).exists():
            group, leaf = session_id.split("/")
            for suffix in range(2, 100):
                candidate = sessions_root() / group / ("%s-%d" % (leaf, suffix))
                if not state_path(candidate).exists():
                    workspace = candidate
                    session_id = "%s/%s-%d" % (group, leaf, suffix)
                    break

    try:
        workspace.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise SessionError(
            "Cannot create workspace at %s: %s" % (workspace, exc), EXIT_ENVIRONMENT
        )

    # Sessions now land in the working directory, which means they land inside
    # whatever repository the candidate is standing in. A .gitignore that
    # ignores everything, itself included, keeps a sitting from turning into a
    # commit without anyone having to remember.
    try:
        (workspace / ".gitignore").write_text("*\n")
    except OSError:
        pass

    # The per-session file above never covered the root's own bookkeeping, so
    # `current` and history.json still showed up as an untracked
    # interview-sim-sessions/ in a candidate's repository. One at the root
    # covers the whole tree, this file included.
    try:
        root_ignore = sessions_root() / ".gitignore"
        if root_ignore.parent.is_dir() and not root_ignore.exists():
            root_ignore.write_text("*\n")
    except OSError:
        pass

    state = {
        "schema_version": SCHEMA_VERSION,
        "session_id": session_id,
        "mode": args.mode,
        "format": fmt,
        "company": company,
        "round": round_name,
        "generated": bool(args.generated),
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


    # What was asked for against what was actually drawn. Computed here rather
    # than at print time so it lands in state.json: at the debrief, whether the
    # sitting was even on the right subject matters as much as the score.
    briefing = {
        "generated": bool(args.generated),
        "company": company,
        "round": round_name,
        "topics": {"asked": list(topics), "covered": {}, "uncovered": []},
    }
    for want in topics:
        hits = [
            question.get("title", question["id"])
            for question in (questions or [])
            if topic_match(question, [want])
        ]
        if hits:
            briefing["topics"]["covered"][want] = hits
        else:
            briefing["topics"]["uncovered"].append(want)
    briefing["match"] = match_band(list(topics), briefing["topics"]["uncovered"])
    # What the questions themselves say they are about, from their own metadata.
    # A question written for this sitting always declares its subjects, so
    # provenance can be stated without the caller having remembered --topic.
    covers = []
    for question in (questions or []):
        for subject in (question.get("topics") or []):
            if subject not in covers:
                covers.append(subject)
    briefing["covers"] = covers
    state["briefing"] = briefing

    # Record what the freshly copied starters look like, without emitting edit
    # events for them. Copying a starter is not work, and counting it as the
    # first edit would put every session's opening minutes on question one.
    observe_edits(workspace, state, baseline=True)

    write_state(workspace, state)
    write_readme(workspace, state)
    write_pointer(workspace)
    if args.open:
        # The problem, not the solution. Landing in an empty starter file puts
        # someone at a keyboard before they have read what they are being asked
        # for, which is the wrong instinct to rehearse and the opposite of what
        # a real sitting rewards.
        open_in_editor(workspace, first_reading(workspace, state))
    remember_questions([question["id"] for question in state["questions"]])

    payload = status_payload(state, now, STATE_ACTIVE)
    # Everything the human output no longer says, in the channel the agent
    # reads. Removed from the candidate's screen, not from the record: the
    # proctor needs to know which requested topics went uncovered, because that
    # is the cue to write a question for them.
    payload["briefing"] = briefing

    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        print("Session started: %s" % (session_id,))
        print("")
        # What this prints is the sitting, not the evidence behind it. Where a
        # format came from, how confident anyone is in it, and what the bank
        # does or does not hold are questions with real answers, and `presets`
        # and --json give them in full. Reciting them at the moment the clock
        # starts reads as a tool apologising for itself, and none of it is
        # something a candidate can act on with forty-five minutes to spend.
        headline = None
        if company:
            headline = company
            if round_name:
                headline += ", %s round" % (round_name,)
        if args.mode == "interview":
            shape = "live interview"
        elif config["gated"]:
            shape = "%s project" % (config["label"],)
        else:
            shape = "%s exam" % (config["label"],)
        if headline:
            print("%s. %s." % (headline, shape[:1].upper() + shape[1:]))
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
            print("    %s/level1.md     the brief" % (first["dir"],))
            print("    %s/solution.py   yours to write" % (first["dir"],))
            print("")
            print(
                "Levels 2 to %d are locked. Each one appears when the level "
                "before it passes." % (len(state["questions"]),)
            )
        else:
            for question in state["questions"]:
                print(
                    "    %s/problem.md   %s"
                    % (question["dir"], question["title"] or question["id"])
                )
        print("")
        # Point at the problem, not the workspace. Someone who opens the starter
        # first starts typing before they know what is being asked, and the
        # first instruction should rehearse the habit the format rewards.
        told = describe_match(briefing)
        if told:
            for line in told:
                print(line)
            print("")

        opening = first_reading(workspace, state)
        if len(state["questions"]) == 1 or config["gated"]:
            where = "%s/%s" % (opening.parent.name, opening.name)
            paragraph("Read %s first, then write in %s/solution.py." % (where, opening.parent.name))
        else:
            paragraph(
                "Read a problem.md first, then write your answer in the "
                "solution.py beside it."
            )
        print("The clock is running.")
    return EXIT_OK


def first_reading(workspace: Path, state: Dict[str, Any]) -> Path:
    """The file to read before writing anything.

    Gated formats reveal one level at a time, so the opening brief is level1.md
    rather than a problem statement for the whole project.
    """
    first = state["questions"][0]
    if FORMATS[state["format"]]["gated"]:
        return workspace / first["dir"] / "level1.md"
    return workspace / first["dir"] / "problem.md"


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


def run_grader(
    question: Dict[str, Any], solution: Path, timeout: float, detail: bool = False
) -> Dict[str, Any]:
    """Shell out to grade.py.

    A subprocess rather than an import, so the candidate's code never executes
    inside the process holding the state file open.

    `detail` asks the grader for the names of the tests that failed. It stays
    off for `submit`, where naming them would hand over the answer while there
    is still time to use it, and goes on for `debrief`, which runs only once the
    clock is out and exists to name them.
    """
    grader = Path(__file__).resolve().parent / "grade.py"
    if not grader.exists():
        raise SessionError("Grader missing at %s" % (grader,), EXIT_ENVIRONMENT)

    source = question["source"]
    bank_dir = Path(source) if os.path.isabs(source) else QUESTIONS_DIR / source
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
        ] + (["--detail"] if detail else []),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
    )
    try:
        out, err = proc.communicate(timeout=max(timeout * 2 + 30, 60))
    except subprocess.TimeoutExpired:
        proc.kill()
        try:
            proc.communicate(timeout=5)
        except (subprocess.TimeoutExpired, OSError):
            pass
        raise SessionError(
            "The grader did not return. Nothing was recorded for this attempt.",
            EXIT_ENVIRONMENT,
        )
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

        # Already holding the lock, so this is observe_edits rather than
        # sample_edits. _record_submission writes the state on the way out and
        # carries the reading with it.
        observe_edits(workspace, state)

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


# --------------------------------------------------------------------------
# where the time went
#
# The pitch this tool makes is that four questions in seventy minutes is a
# different problem from four questions. Nothing in it measured that: every
# figure it reported was about whether the code was right, which is the part
# any untimed judge already tells you. Almost nobody fails a screen because
# they cannot do binary search. They fail because they spent half the clock on
# question two and never opened question four.
#
# There is no watcher process, so the engine only sees the filesystem when
# somebody runs a command. What survives that gap is the modification time on
# each solution file, so every invocation samples it and records any value it
# has not recorded before. That yields real timestamps, never invented ones,
# just sparser than a watcher would give: the resolution is however often the
# candidate checked the clock or submitted something.
# --------------------------------------------------------------------------

# Filesystem timestamps are not infinitely precise and a copy is not an edit.
# Anything inside this of the value already recorded is the same write.
EDIT_EPSILON = 0.5


def solution_file(workspace: Path, directory: str) -> Path:
    return workspace / directory / "solution.py"


def question_dirs(state: Dict[str, Any]) -> List[str]:
    """Each distinct working directory, in slot order.

    An ICA project is four entries sharing one solution file, so the directory
    is what to sample, not the question.
    """
    seen = []
    for question in state.get("questions", []):
        directory = question.get("dir")
        if directory and directory not in seen:
            seen.append(directory)
    return seen


def observe_edits(workspace: Path, state: Dict[str, Any], baseline: bool = False) -> bool:
    """Fold the current mtime of every solution file into the event log.

    With `baseline`, the current values are recorded without emitting events:
    that is the copy `start` just made, and copying a starter is not work.

    Returns whether anything was added, so the caller can decide to persist.
    """
    seen = state.setdefault("edits_seen", {})
    changed = False
    for directory in question_dirs(state):
        try:
            mtime = os.stat(str(solution_file(workspace, directory))).st_mtime
        except OSError:
            continue
        previous = seen.get(directory)
        if previous is None or baseline:
            seen[directory] = mtime
            changed = True
            continue
        # Different, not later. An editor writing through a temp file, a restore
        # from a backup, or a checkout can all move an mtime backwards, and a
        # file that is not what it was is an edit whichever way the clock went.
        if abs(mtime - previous) > EDIT_EPSILON:
            seen[directory] = mtime
            add_event(state, mtime, "edited", question=directory)
            changed = True
    return changed


def sample_edits(workspace: Path, state: Dict[str, Any]) -> None:
    """Take a reading, and write it down if there was anything new.

    Best effort deliberately. A read-only workspace, or a lock somebody else is
    holding, should cost the timeline some resolution and nothing more: no
    command fails because a measurement could not be taken.

    Never call this while already holding the session lock. flock associates
    with the open file description, so a second open in the same process waits
    on the first and the command hangs. The paths that already hold the lock
    call observe_edits directly and let their own write carry it.
    """
    try:
        if not observe_edits(workspace, state):
            return
        with session_lock(workspace):
            write_state(workspace, state)
    except (SessionError, IOError, OSError):
        pass


def sample_edits_locked(workspace: Path) -> None:
    """Take a reading under the lock, re-reading the state first.

    `sample_edits` writes the state object its caller is already holding, which
    is correct for a command that read it a moment ago and exits. A watch pane
    lives for an hour beside a grader, so it must not write back a copy it read
    before the last submission landed. Re-reading inside the lock closes that
    window; the cost is a lock the grader briefly waits on, which is
    microseconds against a run that takes seconds.
    """
    try:
        with session_lock(workspace):
            fresh = read_state(workspace)
            if observe_edits(workspace, fresh):
                write_state(workspace, fresh)
    except (SessionError, IOError, OSError):
        pass


def session_end_point(state: Dict[str, Any], now: float) -> float:
    """The last moment that counts, whether or not the session is over."""
    clock = state["clock"]
    end_point = clock.get("ended_epoch")
    if end_point is None:
        end_point = now
    return min(end_point, clock["deadline_epoch"])


def time_attribution(state: Dict[str, Any], now: float) -> Dict[str, Any]:
    """Split the clock between the questions, from what was actually observed.

    Non-gated formats are attributed forwards: touching a question at time T
    means it holds the clock from T until something else is touched. The other
    direction, giving a question the stretch that ends at its first save, reads
    plausibly and is wrong. It hands the opening minutes of real work on
    question one to whatever got saved next, and leaves question one owning
    only the time before anybody had written anything.

    The stretch before the first edit belongs to no question, because nothing
    had been written yet. That is reading, and it is worth seeing on its own.

    Gated formats put every level in one file, so mtimes cannot separate them.
    They partition on the level boundaries instead, which are exact: a level
    runs from the moment it unlocked to the moment the next one did.
    """
    clock = state["clock"]
    start = clock["started_epoch"]
    end_point = session_end_point(state, now)
    spent = dict((directory, 0.0) for directory in question_dirs(state))
    events = sorted(state.get("events", []), key=lambda item: item.get("epoch", 0.0))

    if FORMATS[state["format"]]["gated"]:
        # Level 1 begins when the session does; each later level begins when it
        # was unlocked. Boundaries partition the clock, so nothing is lost.
        by_slot = {}
        for question in state.get("questions", []):
            by_slot[question["slot"]] = question
        opened = {1: start}
        for event in events:
            if event.get("type") == "level_unlocked":
                opened[event.get("level")] = event.get("epoch", start)
        levels = sorted(opened)
        per_level = {}
        for index, slot in enumerate(levels):
            began = opened[slot]
            finished = opened[levels[index + 1]] if index + 1 < len(levels) else end_point
            question = by_slot.get(slot)
            if question is not None:
                per_level[question["id"]] = max(0.0, finished - began)
        return {
            "by_level": per_level,
            "by_question": spent,
            "touched": set(),
            "reading": 0.0,
            "observed": True,
        }

    moments = []
    touched = set()
    for event in events:
        kind = event.get("type")
        if kind not in ("edited", "submitted"):
            continue
        directory = event.get("question")
        if directory not in spent:
            continue
        epoch = event.get("epoch")
        if epoch is None:
            continue
        touched.add(directory)
        moments.append((min(max(epoch, start), end_point), directory))
    moments.sort()

    for index, (epoch, directory) in enumerate(moments):
        following = moments[index + 1][0] if index + 1 < len(moments) else end_point
        spent[directory] += max(0.0, following - epoch)
    return {
        "by_level": {},
        "by_question": spent,
        "touched": touched,
        "reading": max(0.0, moments[0][0] - start) if moments else 0.0,
        "observed": bool(moments),
    }


def band_for(credit: float, solved: int, count: int) -> str:
    """A qualitative band, deliberately not a number.

    The scales real platforms report are proprietary and calibrated against data
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
    # The last look, so work done after the final submission still lands on the
    # timeline rather than vanishing into the unaccounted bucket.
    sample_edits(workspace, state)

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
                "id": question["id"],
                "state": question.get("state"),
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
    used = session_end_point(state, now) - clock["started_epoch"]

    # Where the time went, folded onto the lines the report already prints.
    timing = time_attribution(state, now)
    for line in lines:
        if gated:
            seconds = timing["by_level"].get(line["id"], 0.0)
            # A level still locked was never reached, which is not the same as
            # reached and left unsubmitted.
            opened = line["state"] != STATE_LOCKED
        else:
            seconds = timing["by_question"].get(line["dir"], 0.0)
            # Never edited and never submitted. Worth separating from a question
            # that was opened and got nowhere, because they are different
            # mistakes with different fixes. Judged on whether it was ever
            # touched, not on the seconds: a question opened in the last minute
            # of the session is still a question that was opened.
            opened = line["dir"] in timing["touched"]
        line["seconds"] = round(max(0.0, seconds), 1)
        line["time_display"] = format_duration(seconds) if opened else None
        line["share"] = round(seconds / used, 4) if used > 0 else 0.0
        line["opened"] = opened
    unopened = [line for line in lines if not line["opened"]]
    heaviest = max(lines, key=lambda item: item["seconds"]) if lines else None

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
        "timing": {
            "reading_seconds": round(timing["reading"], 1),
            "observed": timing["observed"],
            "never_opened": [line["dir"] for line in unopened],
        },
        "detail": lines,
        "score_note": (
            "Unofficial. This is what these hidden tests measured, and not the "
            "score any real platform would give you: those scales are "
            "proprietary and cannot be reproduced honestly."
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
                "  %-4s %-13s %-10s %s"
                % (line["dir"], line["summary"], line["difficulty"], line["title"])
            )
    print("")

    if timing["observed"]:
        print("Where the time went")
        print("")
        # "Level 1" needs more room than "q1", and a ragged first column makes
        # the times impossible to compare down the page.
        width = max([len(line["title"] if gated else line["dir"]) for line in lines] or [4])
        for line in lines:
            label = line["title"] if gated else line["dir"]
            if not line["opened"]:
                print("  %-*s %s" % (width, label, "never reached" if gated else "not opened"))
                continue
            marker = ""
            # Only worth pointing at when it is genuinely lopsided. An even
            # split across four questions has no story in it and drawing an
            # arrow at 26% would invent one.
            if line is heaviest and line["share"] >= 0.30 and len(lines) > 1:
                marker = "   %.0f%% of the clock" % (line["share"] * 100,)
            # "not attempted" is the right word in the results above and the
            # wrong one here, where the line exists to say a quarter of an hour
            # went into it. It was attempted. It was never submitted.
            summary = "not submitted" if not line["attempts"] else line["summary"]
            print(
                "  %-*s %-13s %8s   %d submit%s%s"
                % (
                    width,
                    label,
                    summary,
                    line["time_display"],
                    line["attempts"],
                    "" if line["attempts"] == 1 else "s",
                    marker,
                )
            )
        if timing["reading"] >= 60:
            print("")
            print(
                "  %s before the first edit, reading."
                % (format_duration(timing["reading"]),)
            )
        if unopened and not gated:
            print("")
            paragraph(
                "%d question%s never opened. Running out of time is a result, "
                "but never seeing a question is a triage result: the one you "
                "skipped may have been the one you could do."
                % (len(unopened), "" if len(unopened) == 1 else "s")
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
        paragraph(
            "An earlier level is failing. Whatever the percentage says, this is "
            "a regression: the work broke something that used to pass."
        )
    if state["mode"] == "interview":
        if hints_given:
            paragraph(
                "%d hint%s given. Solving it with help is a different result "
                "from solving it alone, and the debrief should say so."
                % (hints_given, "" if hints_given == 1 else "s")
            )
        else:
            print("No hints given.")
    told = describe_match(state.get("briefing") or {})
    if told:
        print("")
        for line in told:
            print(line)
        if (state.get("briefing") or {}).get("match") == "off":
            paragraph(
                "Worth remembering when you read the numbers above: this sitting "
                "was not on the subject you asked to practise."
            )

    print("")
    paragraph(payload["score_note"])
    return EXIT_OK


def walk_sessions() -> List[Tuple[Path, Optional[Dict[str, Any]]]]:
    """Every session under the root, newest first, state or None if unreadable.

    Unreadable ones are kept rather than skipped. A session written by an older
    schema still exists on disk, and dropping it silently is how a tool ends up
    unable to show you something you can plainly see in your file manager.

    Read from the state files themselves rather than from an index, because an
    index is another thing that can disagree with the truth.
    """
    found = []  # type: List[Tuple[Path, Optional[Dict[str, Any]]]]
    seen = set()
    for root in history_roots():
        if not root.is_dir():
            continue
        for entry in sorted(root.iterdir()):
            if not entry.is_dir():
                continue
            # Sessions sit one level down now, grouped by company and round, so
            # a directory is either a session itself (every session sat before
            # the change, and anything started with --workspace) or a group
            # holding them. Only the second case is descended into, which keeps
            # this out of q1/ and .sim/ and off the rest of the tree.
            if state_path(entry).exists():
                candidates = [entry]
            else:
                try:
                    candidates = sorted(
                        child for child in entry.iterdir() if child.is_dir()
                    )
                except OSError:
                    continue
            for candidate in candidates:
                if not state_path(candidate).exists():
                    continue
                key = str(candidate.resolve())
                if key in seen:
                    continue
                seen.add(key)
                try:
                    found.append((candidate, read_state(candidate)))
                except SessionError:
                    found.append((candidate, None))
    found.sort(
        key=lambda pair: ((pair[1] or {}).get("clock") or {}).get("started_epoch", 0),
        reverse=True,
    )
    return found

def time_used(state: Dict[str, Any], now: float) -> float:
    """Seconds spent in a session, which is not the same as seconds elapsed.

    A session left running overnight did not take nine hours. Anything still on
    the clock is counted up to the deadline and no further.
    """
    clock = state["clock"]
    started = clock["started_epoch"]
    if clock.get("ended_epoch"):
        return max(0.0, clock["ended_epoch"] - started)
    return max(0.0, min(now, clock["deadline_epoch"]) - started)

def command_progress(args: argparse.Namespace) -> int:
    """History across sessions: what was sat, what passed, what was never reached.

    The stickiest thing a practice tool can show you is that you are getting
    better, and the one number this tool will not print is a score. So it prints
    what it did measure and puts the rows next to each other, which is the
    honest version of a progress chart.

    It deliberately stops short of a single improvement figure. Questions differ
    in difficulty and the draw is random, so across a bank this size a rising
    percentage is as likely to mean an easier session as a better one. The
    difficulty rows below carry the signal a single number would bury.
    """
    now = resolve_now(args.now)
    sessions = [
        (workspace, state)
        for workspace, state in walk_sessions()
        if state is not None
    ]
    if args.format:
        sessions = [
            pair for pair in sessions if pair[1]["format"] == args.format.lower()
        ]
    if args.limit and args.limit > 0:
        sessions = sessions[: args.limit]

    rows = []
    by_difficulty = {}  # type: Dict[str, Dict[str, int]]
    order = []  # type: List[str]
    attempted = 0
    never = 0
    for workspace, state in sessions:
        passed = total = solved = hints = 0
        for question in state["questions"]:
            hints += question.get("hints", 0) or 0
            difficulty = question.get("difficulty") or "unknown"
            if difficulty not in by_difficulty:
                by_difficulty[difficulty] = {"passed": 0, "total": 0, "questions": 0}
                order.append(difficulty)
            result = question.get("result") or {}
            if not result:
                never += 1
                continue
            attempted += 1
            passed += result.get("passed", 0)
            total += result.get("total", 0)
            if result.get("outcome") == "pass":
                solved += 1
            bucket = by_difficulty[difficulty]
            bucket["passed"] += result.get("passed", 0)
            bucket["total"] += result.get("total", 0)
            bucket["questions"] += 1
        rows.append(
            {
                "session_id": state["session_id"],
                "date": state["clock"]["started_utc"][:10],
                "format": state["format"],
                "mode": state["mode"],
                "company": state.get("company"),
                "solved": solved,
                "questions": len(state["questions"]),
                "passed": passed,
                "total": total,
                "hints": hints,
                "used_seconds": round(time_used(state, now), 3),
                "duration_seconds": state["clock"]["duration_seconds"],
            }
        )

    # Named order, so the rows read as a ramp rather than in whatever sequence
    # the sessions happened to be drawn in.
    ramp = ("warmup", "medium", "hard", "level1", "level2", "level3", "level4")
    order.sort(key=lambda name: (ramp.index(name) if name in ramp else len(ramp), name))
    difficulties = [
        dict(by_difficulty[name], difficulty=name)
        for name in order
        if by_difficulty[name]["questions"]
    ]
    payload = {
        "sessions": rows,
        "by_difficulty": difficulties,
        "attempted": attempted,
        "never_submitted": never,
        "note": (
            "A history, not a score. Questions differ in difficulty and the draw "
            "is random, so a rising percentage can mean an easier session rather "
            "than a better one."
        ),
    }

    if args.json:
        print(json.dumps(payload, indent=2))
        return EXIT_OK

    if not rows:
        if args.format:
            print("No %s sessions yet under %s" % (args.format.lower(), sessions_root()))
        else:
            print("No sessions yet under %s" % (sessions_root(),))
        return EXIT_OK

    formats = {}  # type: Dict[str, int]
    for row in rows:
        formats[row["format"]] = formats.get(row["format"], 0) + 1
    spread = ", ".join(
        "%d %s" % (count, name.upper()) for name, count in sorted(formats.items())
    )
    print(
        "%d session%s since %s. %s."
        % (len(rows), "" if len(rows) == 1 else "s", rows[-1]["date"], spread)
    )
    print("")
    for row in rows:
        tests = (
            "%d/%d tests" % (row["passed"], row["total"]) if row["total"] else "no tests run"
        )
        print(
            "  %s  %-4s  %d/%d solved  %-14s %s of %s%s"
            % (
                row["date"],
                row["format"],
                row["solved"],
                row["questions"],
                tests,
                format_duration(row["used_seconds"]),
                format_duration(row["duration_seconds"]),
                ", %d hint%s" % (row["hints"], "" if row["hints"] == 1 else "s")
                if row["hints"]
                else "",
            )
        )

    if difficulties:
        print("")
        print("Hidden tests passed, by difficulty:")
        for entry in difficulties:
            share = (
                100.0 * entry["passed"] / entry["total"] if entry["total"] else 0.0
            )
            print(
                "  %-10s %3d%%   (%d of %d, across %d question%s)"
                % (
                    entry["difficulty"],
                    round(share),
                    entry["passed"],
                    entry["total"],
                    entry["questions"],
                    "" if entry["questions"] == 1 else "s",
                )
            )

    if never:
        print("")
        paragraph(
            "Never submitted: %d of %d question%s. Running out of time is a "
            "result too, and it is the one a pass rate hides."
            % (never, attempted + never, "" if attempted + never == 1 else "s")
        )

    print("")
    paragraph(payload["note"])
    return EXIT_OK

def command_check(args: argparse.Namespace) -> int:
    """Say whether this machine can run a session, before the clock is involved.

    Everything here is knowable in advance, and every one of these failures is
    otherwise discovered halfway through a start, which is the worst moment: the
    workspace is half built and the user is deciding whether the tool is broken
    or they are. Cheap to run, so the skill runs it when anything else fails.
    """
    checks = []  # type: List[Dict[str, Any]]

    version = sys.version_info
    running = "%d.%d.%d" % (version[0], version[1], version[2])
    if version < (3, 6):
        checks.append(
            {
                "name": "python",
                "ok": False,
                "detail": "%s at %s, too old. 3.9 is what this is tested on."
                % (running, sys.executable),
            }
        )
    elif version < (3, 9):
        checks.append(
            {
                "name": "python",
                "ok": True,
                "warn": True,
                "detail": "%s at %s. Older than the 3.9 this is tested on, so it "
                "may work and is not something I have checked."
                % (running, sys.executable),
            }
        )
    else:
        checks.append(
            {"name": "python", "ok": True, "detail": "%s at %s" % (running, sys.executable)}
        )

    try:
        questions = sorted(
            entry
            for family in QUESTIONS_DIR.iterdir()
            if family.is_dir()
            for entry in family.iterdir()
            if (entry / "meta.json").exists()
        )
    except OSError as exc:
        questions = []
        checks.append({"name": "bank", "ok": False, "detail": str(exc)})
    else:
        checks.append(
            {
                "name": "bank",
                "ok": bool(questions),
                "detail": "%d question%s under %s"
                % (len(questions), "" if len(questions) == 1 else "s", QUESTIONS_DIR)
                if questions
                else "no questions found under %s" % (QUESTIONS_DIR,),
            }
        )

    root = sessions_root()
    try:
        root.mkdir(parents=True, exist_ok=True)
        probe = root / ".write-probe"
        probe.write_text("")
        probe.unlink()
    except OSError as exc:
        checks.append(
            {"name": "sessions", "ok": False, "detail": "%s is not writable: %s" % (root, exc)}
        )
    else:
        checks.append({"name": "sessions", "ok": True, "detail": str(root)})

    editor = find_editor()
    checks.append(
        {
            "name": "editor",
            "ok": True,
            "detail": "%s, so --open will open the problem in it" % (editor[0],)
            if editor
            else "no GUI editor found, so --open has nothing to open. Sessions "
            "still work; the workspace path is printed when one starts",
        }
    )

    # Not a failure either way. The clock on screen is the real surface and the
    # notification is a supplement, so this exists to say so before a sitting
    # rather than at ten minutes to go.
    found = notifier()
    checks.append(
        {
            "name": "alerts",
            "ok": True,
            "detail": "%s, so `watch` can raise its ten and two minute warnings"
            % (found,)
            if found
            else "no notifier on this platform, so `watch` warns with the bell "
            "and the tab title only. The countdown itself still works",
        }
    )

    # Not a pass or fail, just the thing people ask for after their first
    # session, and this is the one command that knows the path.
    shortcut = 'sim() { python3 "%s" "$@"; }' % (Path(__file__).resolve(),)

    failed = [entry for entry in checks if not entry["ok"]]
    if args.json:
        print(
            json.dumps(
                {"ok": not failed, "checks": checks, "shortcut": shortcut}, indent=2
            )
        )
        return EXIT_OK if not failed else EXIT_ENVIRONMENT

    for entry in checks:
        mark = "ok  " if entry["ok"] else "FAIL"
        if entry.get("warn"):
            mark = "note"
        print("%s  %-9s %s" % (mark, entry["name"], entry["detail"]))
    print("")
    if failed:
        paragraph(
            "Not ready: fix the FAIL line%s above. Nothing here needs a network "
            "connection or an install." % ("" if len(failed) == 1 else "s")
        )
        return EXIT_ENVIRONMENT
    print("Ready. A shortcut, if you want one:")
    print("  %s" % (shortcut,))
    return EXIT_OK


def command_list(args: argparse.Namespace) -> int:
    """Show past sessions, newest first."""
    rows = []
    for workspace, state in walk_sessions():
        if state is None:
            # A session written by a different schema version still deserves a
            # line, so it can be seen and deleted.
            rows.append(
                {
                    "session_id": workspace_label(workspace),
                    "unreadable": True,
                    "workspace": str(workspace),
                }
            )
        else:
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

    if args.limit and args.limit > 0:
        rows = rows[: args.limit]

    if args.json:
        print(json.dumps(rows, indent=2))
        return EXIT_OK

    if not rows:
        print("No sessions yet under %s" % (sessions_root(),))
        return EXIT_OK

    current = read_pointer()
    # Ids carry a company and a round now, so their width varies with whoever
    # was typed in rather than sitting at a known 28. Measured across the rows
    # actually being printed, so the columns line up in this listing instead of
    # in the abstract.
    width = max(28, max(len(row["session_id"]) for row in rows))
    for row in rows:
        if row["unreadable"]:
            print(
                "  %-*s (unreadable, from an older version)"
                % (width, row["session_id"])
            )
            continue
        marker = "*" if current is not None and str(current) == row["workspace"] else " "
        print(
            "%s %-*s %-4s %-9s %-8s %d/%d solved  %s"
            % (
                marker,
                width,
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


def command_end(args: argparse.Namespace) -> int:
    """Stop a session on purpose, before the clock does.

    Giving up is a legitimate ending and it needed a door: without one, the
    only path to the abandoned state was force-starting a new session, so
    somebody who stopped caring still had a live clock holding the debrief
    shut for half an hour.
    """
    now = resolve_now(args.now)
    workspace = resolve_workspace(args)
    state = read_state(workspace)
    sample_edits(workspace, state)

    phase = classify(state, now)
    if phase == STATE_EXPIRED:
        state = finalize(workspace, state, now, END_REASON_TIME)
        phase = STATE_ENDED
    if phase == STATE_ENDED:
        print("This session is already over (%s)." % (state["clock"].get("end_reason"),))
        return EXIT_OK

    state = finalize(workspace, state, now, END_REASON_ABANDONED)
    print("Session ended (abandoned), %s in." % (format_duration(time_used(state, now)),))
    paragraph(
        "Nothing more can be submitted. `report` shows what happened, and "
        "`debrief` now names what each hidden test was checking, with "
        "`debrief --question q1` printing a reference solution."
    )
    return EXIT_OK


def command_status(args: argparse.Namespace) -> int:
    now = resolve_now(args.now)
    workspace = resolve_workspace(args)
    state = read_state(workspace)
    # Checking the clock is the commonest thing anybody does mid-session, which
    # makes it the best chance to see the files as they are right now.
    sample_edits(workspace, state)

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


# --------------------------------------------------------------------------
# watch
#
# A real assessment puts a countdown in the browser chrome where you cannot
# avoid it, and coding with a clock in your peripheral vision is a different
# skill from coding. Nothing here owns that clock: the pane re-reads
# state.json and draws `deadline - now`. It decides nothing and grades
# nothing, so late work is still refused by the script alone. A display
# process is fine where a timing process would not be.
# --------------------------------------------------------------------------

# Amber, then red. Ten minutes is when triage stops being optional and two is
# when the answer is to submit whatever exists.
WARN_AT = 600.0
CRITICAL_AT = 120.0
MILESTONES = ((1800.0, "Thirty minutes left"),
              (600.0, "Ten minutes left"),
              (120.0, "Two minutes left"))
SAMPLE_EVERY = 15.0

ANSI = {
    "reset": "\033[0m", "dim": "\033[2m", "bold": "\033[1m",
    "green": "\033[32m", "yellow": "\033[33m", "red": "\033[31m",
}


def urgency(remaining: float) -> str:
    if remaining <= 0:
        return "over"
    if remaining <= CRITICAL_AT:
        return "critical"
    if remaining <= WARN_AT:
        return "warning"
    return "calm"


def due_milestones(remaining: float, fired: set) -> List[Tuple[float, str]]:
    """Thresholds crossed since the last look.

    Starting a watch with five minutes left must not fire thirty and ten on the
    way in, so the caller seeds `fired` with everything already behind it.
    """
    return [(at, label) for at, label in MILESTONES
            if remaining <= at and at not in fired]


def notifier() -> Optional[str]:
    """The program that can raise a desktop notification here, if any."""
    if sys.platform == "darwin":
        return shutil.which("osascript")
    if sys.platform.startswith("linux"):
        return shutil.which("notify-send")
    return None


def notify(message: str) -> None:
    """Best effort desktop notification. Never raises, never blocks.

    Notifications are a supplement to the clock on screen, never the thing the
    design leans on: permission may never have been granted and Do Not Disturb
    may be on, and something you rely on to say the time is nearly gone that
    quietly does not is worse than not having it.
    """
    found = notifier()
    if not found:
        return
    safe = message.replace('"', "'")
    if sys.platform == "darwin":
        command = [found, "-e",
                   'display notification "%s" with title "interview-sim"' % (safe,)]
    else:
        command = [found, "interview-sim", safe]
    try:
        with open(os.devnull, "w") as sink:
            subprocess.Popen(command, stdout=sink, stderr=sink)
    except (OSError, ValueError):
        pass


def watch_frame(state: Dict[str, Any], now: float, colour: bool = True) -> str:
    """One rendered frame of the pane."""
    def paint(text, name):
        return "%s%s%s" % (ANSI[name], text, ANSI["reset"]) if colour else text

    clock = state["clock"]
    ended = clock.get("ended_epoch") is not None
    remaining = max(0.0, clock["deadline_epoch"] - now)
    level = "over" if ended else urgency(remaining)

    if level == "over":
        face = (
            "TIME IS UP"
            if clock.get("end_reason") in (None, END_REASON_TIME)
            else "SESSION ENDED"
        )
        tint = "red"
    else:
        face = format_duration(remaining)
        tint = {"calm": "bold", "warning": "yellow", "critical": "red"}[level]

    width = max(len(face) + 8, 17)
    pad = (width - len(face)) // 2
    lines = [
        "",
        "  ┌" + "─" * width + "┐",
        "  │" + " " * pad + paint(face, tint) + " " * (width - pad - len(face)) + "│",
        "  └" + "─" * width + "┘",
        "  " + paint(state["session_id"], "dim"),
        "",
    ]

    # The pane already samples edits, so it knows where the hour is going while
    # there is still time to change it. Waiting for the debrief to say two
    # thirds of the clock went on question two is telling somebody the thing
    # they could have acted on, an hour after they could have acted on it.
    timing = time_attribution(state, now)
    spent = timing["by_level"] if FORMATS[state["format"]]["gated"] else timing["by_question"]
    current = None
    latest = None
    for event in state.get("events", []):
        if event.get("type") in ("edited", "submitted") and event.get("epoch") is not None:
            if latest is None or event["epoch"] >= latest:
                latest, current = event["epoch"], event.get("question")

    gated = FORMATS[state["format"]]["gated"]
    for question in state["questions"]:
        label = question["title"] if gated else question["dir"]
        result = question.get("result")
        key = question["id"] if gated else question["dir"]
        if result and result.get("total"):
            body = "%d/%d" % (result["passed"], result["total"])
            body = paint(body, "green" if result.get("outcome") == "pass" else "yellow")
        elif question.get("state") == STATE_LOCKED:
            body = paint("locked", "dim")
        elif question.get("attempts"):
            body = paint(result.get("outcome", "?") if result else "?", "yellow")
        elif gated or question["dir"] in timing["touched"]:
            body = paint("not submitted", "dim")
        else:
            body = paint("not opened", "dim")

        seconds = spent.get(key, 0.0)
        opened = gated or question["dir"] in timing["touched"] or question.get("attempts")
        clock_col = format_duration(seconds) if opened else ""
        here = paint(" <- now", "yellow") if (not gated and question["dir"] == current) else ""
        lines.append(("  %-10s %-15s %7s%s" % (label, body, clock_col, here)).rstrip())

    if level == "over":
        lines.append("")
        lines.append("  " + paint("Nothing more can be submitted.", "dim"))
    return "\n".join(lines) + "\n"


def command_watch(args: argparse.Namespace) -> int:
    """A countdown in its own pane, redrawn once a second.

    Never run this from an agent. It does not return until the clock does, so
    anything that shells out to it and waits will simply hang.
    """
    workspace = resolve_workspace(args)
    state = read_state(workspace)
    live = sys.stdout.isatty() and not args.plain

    if args.once:
        sys.stdout.write(watch_frame(state, resolve_now(args.now), colour=live))
        return EXIT_EXPIRED if classify(state, resolve_now(args.now)) != STATE_ACTIVE else EXIT_OK

    # Everything already behind us is not news.
    now = resolve_now(args.now)
    remaining = max(0.0, state["clock"]["deadline_epoch"] - now)
    fired = set(at for at, _ in MILESTONES if remaining <= at)
    last_sample = now

    if live:
        sys.stdout.write("\033[?25l")  # hide the cursor
    try:
        while True:
            now = time.time()
            state = read_state(workspace)
            phase = classify(state, now)
            if phase == STATE_EXPIRED:
                state = finalize(workspace, state, now, END_REASON_TIME)
                phase = STATE_ENDED
            remaining = max(0.0, state["clock"]["deadline_epoch"] - now)

            if live:
                sys.stdout.write("\033[H\033[J")
                # The tab title carries the clock even when this pane is buried,
                # which is the cheapest surface here and the only one that needs
                # no permission and no pane on screen.
                sys.stdout.write("\033]0;%s left\007" % (format_duration(remaining),))
            sys.stdout.write(watch_frame(state, now, colour=live))
            sys.stdout.flush()

            if phase == STATE_ENDED:
                if live:
                    sys.stdout.write("\a")
                    sys.stdout.flush()
                notify("Time is up.")
                return EXIT_EXPIRED if state["clock"].get("end_reason") == END_REASON_TIME else EXIT_OK

            for at, label in due_milestones(remaining, fired):
                fired.add(at)
                if live:
                    sys.stdout.write("\a")
                    sys.stdout.flush()
                notify(label + ".")

            # A running pane is also the best observer the timeline ever gets:
            # without it, resolution is however often a command happened to run.
            if now - last_sample >= SAMPLE_EVERY:
                last_sample = now
                sample_edits_locked(workspace)

            time.sleep(max(0.05, 1.0 - (time.time() % 1.0)))
    except KeyboardInterrupt:
        return EXIT_OK
    except (BrokenPipeError, IOError):
        # The pane was closed, or the output was piped somewhere that stopped
        # reading. A clock nobody is looking at should die quietly rather than
        # print a stack trace into whatever is left of the terminal. stdout is
        # pointed at the void first, because the interpreter flushes it again on
        # the way out and would raise a second time.
        try:
            sink = os.open(os.devnull, os.O_WRONLY)
            os.dup2(sink, sys.stdout.fileno())
        except OSError:
            pass
        return EXIT_OK
    finally:
        if live:
            try:
                sys.stdout.write("\033[?25h")  # give the cursor back
                sys.stdout.flush()
            except (BrokenPipeError, IOError, ValueError):
                pass


# --------------------------------------------------------------------------
# debrief
#
# The hidden tests are hidden for exactly as long as the clock is running.
# The moment it stops they have no reason to stay secret, and keeping them
# secret is what makes a failed sitting useless: you are told you passed 19 of
# 25 and left to guess which five cases you never thought about. That is a
# scoreboard. Naming them, after time, is the part that teaches.
#
# The gate is a timestamp, never a judgement. `debrief` refuses while a
# session is live, which is the same rule `submit` follows, for the same
# reason: a proctor that can be talked into it is not a proctor.
# --------------------------------------------------------------------------


# Enough to see the shape of what was missed. Past this it stops being a list of
# gaps and becomes the suite printed out.
FAILURES_SHOWN = 8


def question_bank_dir(question: Dict[str, Any]) -> Optional[Path]:
    source = question.get("source")
    if not source:
        return None
    found = Path(source) if os.path.isabs(source) else QUESTIONS_DIR / source
    return found if found.is_dir() else None


def test_descriptions(bank_dir: Path) -> Dict[str, str]:
    """What each hidden test is guarding, by name.

    The docstring if the test has one, otherwise the name read back as English.
    Test names in this bank are written to describe the case rather than to
    number it, which is what makes the fallback worth having at all.
    """
    suite = bank_dir / "tests_hidden.py"
    if not suite.exists():
        return {}
    try:
        tree = ast.parse(suite.read_text())
    except (SyntaxError, OSError):
        return {}
    found = {}
    for node in ast.walk(tree):
        if not isinstance(node, ast.FunctionDef) or not node.name.startswith("test"):
            continue
        doc = ast.get_docstring(node)
        if doc:
            found[node.name] = " ".join(doc.strip().splitlines()[0].split())
        else:
            found[node.name] = node.name[5:].replace("_", " ").strip() or node.name
    return found


def debrief_question(
    workspace: Path, question: Dict[str, Any], timeout: float, touched: bool = True
) -> Dict[str, Any]:
    """Re-grade one question and name what it failed."""
    line = {
        "dir": question["dir"],
        "id": question["id"],
        "title": question["title"] or question["id"],
        "failing": [],
        "note": None,
    }
    bank_dir = question_bank_dir(question)
    if bank_dir is None:
        line["note"] = "no longer in the bank, so its tests cannot be named"
        return line

    solution = workspace / question["dir"] / "solution.py"
    if not solution.exists():
        line["note"] = "no solution file was written"
        return line
    if not touched:
        # An untouched starter fails everything, and printing all twenty-six as
        # things they got wrong is both useless and a lie about what happened.
        # Never reaching a question is a triage result, not a knowledge one.
        line["note"] = "never opened. Nothing to name: it was the clock, not the question"
        return line

    report = run_grader(question, solution, timeout, detail=True)
    line["passed"] = report.get("passed", 0)
    line["total"] = report.get("total", 0)
    line["outcome"] = report.get("outcome", "unknown")
    if report.get("outcome") in ("timeout", "crashed", "import_error"):
        line["note"] = {
            "timeout": "did not finish in time, so nothing could be measured",
            "crashed": "stopped the run before a result could be read",
            "import_error": "did not import, so no test ran",
        }[report["outcome"]]
        return line

    described = test_descriptions(bank_dir)
    line["failing"] = [
        {"name": name, "guards": described.get(name, name)}
        for name in report.get("failing", [])
    ]
    return line


def command_debrief(args: argparse.Namespace) -> int:
    now = resolve_now(args.now)
    workspace = resolve_workspace(args)
    state = read_state(workspace)
    sample_edits(workspace, state)

    phase = classify(state, now)
    if phase == STATE_EXPIRED:
        state = finalize(workspace, state, now, END_REASON_TIME)
        phase = STATE_ENDED

    if phase != STATE_ENDED:
        raise SessionError(
            "The clock is still running. A debrief names the hidden tests you "
            "failed,\nand that is the answer key: it waits until the session is "
            "over.\n\n%s remaining."
            % (format_duration(state["clock"]["deadline_epoch"] - now),),
            EXIT_USAGE,
        )

    gated = FORMATS[state["format"]]["gated"]
    timing = time_attribution(state, now)
    spent = timing["by_level"] if gated else timing["by_question"]
    used = session_end_point(state, now) - state["clock"]["started_epoch"]

    wanted = None
    if args.question:
        wanted = find_question(state, args.question)

    lines = []
    for question in state["questions"]:
        if wanted is not None and question["slot"] != wanted["slot"]:
            continue
        if question.get("state") == STATE_LOCKED:
            continue
        opened = gated or question["dir"] in timing["touched"] or question.get("attempts")
        line = debrief_question(workspace, question, args.timeout, bool(opened))
        key = question["id"] if gated else question["dir"]
        line["seconds"] = round(spent.get(key, 0.0), 1)
        line["share"] = round(line["seconds"] / used, 4) if used > 0 else 0.0
        lines.append(line)

    # Costliest first. The question that ate the clock is the one worth reading
    # about, and it is rarely the one they would have opened on their own.
    lines.sort(key=lambda item: item["seconds"], reverse=True)

    if args.json:
        print(json.dumps({"session_id": state["session_id"], "detail": lines}, indent=2))
        return EXIT_OK

    print("Debrief: %s" % (state["session_id"],))
    print("")
    paragraph(
        "The clock is out, so the hidden tests are no longer hidden. Below is "
        "what each question was checking that your answer did not do."
    )
    for line in lines:
        print("")
        head = "%s  %s" % (line["dir"], line["title"])
        if "total" in line and line["total"]:
            head += "   %d/%d" % (line["passed"], line["total"])
        if line["seconds"]:
            head += "   %s" % (format_duration(line["seconds"]),)
            if line["share"] >= 0.30:
                head += " (%.0f%% of the sitting)" % (line["share"] * 100,)
        print(head)
        if line["note"]:
            print("  %s" % (line["note"],))
            continue
        if not line["failing"]:
            print("  Nothing failed.")
            continue
        # An answer that fails everything produces a wall rather than a lesson,
        # and the twenty-sixth line teaches nothing the first eight did not.
        # The count is still printed above, so nothing is being hidden.
        shown = line["failing"][:FAILURES_SHOWN]
        for failure in shown:
            print("  - %s" % (failure["guards"],))
        rest = len(line["failing"]) - len(shown)
        if rest:
            print("  ... and %d more. This one did not come close, so start with"
                  " the problem statement rather than the list." % (rest,))

    if wanted is not None and lines:
        bank_dir = question_bank_dir(wanted)
        reference = (bank_dir / "reference.py") if bank_dir else None
        if reference and reference.exists():
            print("")
            print("One way to write it:")
            print("")
            for text in reference.read_text().splitlines():
                print("    %s" % (text,))
    elif len(lines) > 1:
        print("")
        paragraph(
            "For one question in full, with a reference solution beside yours: "
            "debrief --question %s" % (lines[0]["dir"],)
        )
    return EXIT_OK


def match_band(asked: List[str], uncovered: List[str]) -> Optional[str]:
    """How well the drawn questions match what was asked for.

    Three words rather than a percentage. The only signal here is which topic
    tags overlap, and turning that into "68% match" would invent a precision the
    data does not have. That is the same mistake as reporting a score out of
    600, which this tool refuses to do for the same reason.
    """
    if not asked:
        return None
    if len(uncovered) == len(asked):
        return "off"
    if uncovered:
        return "partial"
    return "on"


def describe_match(briefing: Dict[str, Any]) -> List[str]:
    """Where this question came from and whether it is the right subject.

    Two separate claims, and a session can make either without the other.
    Provenance comes from the question's own metadata, so it is stated even when
    nobody passed --topic: a sitting whose question was written for the round
    should say so, and the first live run of that flow did not, because the
    agent wrote the question and then started without the flags.
    """
    topics = briefing.get("topics") or {}
    asked = topics.get("asked") or []
    covered = topics.get("covered") or {}
    uncovered = topics.get("uncovered") or []
    band = briefing.get("match")
    covers = briefing.get("covers") or []

    lines = []
    if briefing.get("generated"):
        lines.append("Written for this round, not drawn from the shipped set.")
        if covers:
            lines.append("  covers        %s" % (", ".join(covers),))
        lines.append("  it passed the same grading gate as every shipped question.")

    if not asked or band is None:
        return lines
    if lines:
        lines.append("")

    if band == "on":
        lines.append("Topic match: on. Covers %s." % (", ".join(sorted(covered)),))
    elif band == "partial":
        lines.extend([
            "Topic match: partial.",
            "  covers      %s" % (", ".join(sorted(covered)),),
            "  not covered %s" % (", ".join(uncovered),),
        ])
    else:
        lines.extend([
            "Topic match: off.",
            "  you asked for  %s" % (", ".join(asked),),
            "  nothing drawn covers any of it. General practice, not that round.",
        ])
    return lines


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
    start.add_argument(
        "--company", default=None,
        help="who this sitting is for, e.g. --company shopify. A label on the "
             "record: nothing is looked up, the shape comes from the flags",
    )
    start.add_argument(
        "--round", default=None,
        help="which round of their process, e.g. --round pairing. A label too",
    )
    start.add_argument(
        "--open", action="store_true",
        help="open the workspace in your editor once it is ready",
    )
    start.add_argument(
        "--generated", default=None,
        help="run questions from this directory: written for this sitting, "
             "and put through the same mutation gate as the corpus before the "
             "clock starts. Each question directory needs mutants/ with at "
             "least 3 wrong solutions.",
    )
    start.add_argument(
        "--topic", action="append", default=None,
        help="prefer bank questions on this topic, e.g. --topic graphs. "
             "Repeatable. Taken from the preset when it records any",
    )
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

    check = subparsers.add_parser(
        "check", help="whether this machine can run a session"
    )
    add_common(check)
    check.set_defaults(func=command_check)

    progress = subparsers.add_parser(
        "progress", help="what your sessions add up to over time"
    )
    progress.add_argument("--format", default=None, help="only gca, or only ica")
    progress.add_argument("--limit", type=int, default=20)
    add_common(progress)
    progress.set_defaults(func=command_progress)

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

    watch = subparsers.add_parser(
        "watch", help="a live countdown, for a second terminal pane"
    )
    watch.add_argument("--workspace", default=None)
    watch.add_argument("--session", default=None)
    watch.add_argument(
        "--once", action="store_true",
        help="draw one frame and exit instead of running the clock down",
    )
    watch.add_argument(
        "--plain", action="store_true",
        help="no colour, no cursor tricks, no tab title",
    )
    add_common(watch)
    watch.set_defaults(func=command_watch)

    end = subparsers.add_parser(
        "end", help="stop the session now, recorded as abandoned"
    )
    end.add_argument("--workspace", default=None)
    end.add_argument("--session", default=None)
    add_common(end)
    end.set_defaults(func=command_end)

    debrief = subparsers.add_parser(
        "debrief", help="after time: which hidden tests failed, and what they guarded"
    )
    debrief.add_argument("--workspace", default=None)
    debrief.add_argument("--session", default=None)
    debrief.add_argument(
        "--question", default=None,
        help="one question in full, with a reference solution beside yours",
    )
    debrief.add_argument("--timeout", type=float, default=30.0)
    add_common(debrief)
    debrief.set_defaults(func=command_debrief)

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
    # Same problem for --mode: a preset that records a live round should be able
    # to select interview mode, but only when the caller did not say otherwise.
    args.mode_given = any(
        item == "--mode" or item.startswith("--mode=") for item in argv_list
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
