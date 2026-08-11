"""Tests for the session engine.

Driven through the CLI with subprocess rather than by importing session.py,
because the exit codes are a public contract that SKILL.md branches on. Testing
the functions directly would leave the thing that actually matters untested.

--now injects a fixed clock so timer behaviour is exercised without sleeping.
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SCRIPT = REPO / "skills" / "sim" / "scripts" / "session.py"

EXIT_OK = 0
EXIT_USAGE = 2
EXIT_NO_SESSION = 3
EXIT_EXPIRED = 4
EXIT_ACTIVE_SESSION = 5
EXIT_BANK = 6

# An arbitrary fixed point on the clock. Any epoch works; a constant keeps the
# arithmetic in the tests readable.
T0 = 1786541445.0
HOUR = 3600.0


class SessionTestCase(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix="interview-sim-test-"))
        self.addCleanup(shutil.rmtree, str(self.root), True)

    def run_session(self, *args, **kwargs):
        """Invoke the CLI. Returns (exit_code, stdout, stderr)."""
        env = dict(os.environ)
        env["INTERVIEW_SIM_HOME"] = str(self.root)
        env.pop("INTERVIEW_SIM_NOW", None)
        env.pop("INTERVIEW_SIM_SESSION", None)
        proc = subprocess.Popen(
            [sys.executable, str(SCRIPT)] + [str(a) for a in args],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
            cwd=kwargs.get("cwd", str(REPO)),
            universal_newlines=True,
        )
        out, err = proc.communicate()
        return proc.returncode, out, err

    def start(self, now=T0, extra=()):
        args = ["start", "--format", "gca", "--questions", "1", "--now", now]
        code, out, err = self.run_session(*(list(args) + list(extra)))
        self.assertEqual(code, EXIT_OK, "start failed: %s%s" % (out, err))
        return self.workspace()

    def workspace(self):
        pointer = self.root / "current"
        return Path(pointer.read_text().strip())

    def state(self):
        path = self.workspace() / ".sim" / "state.json"
        with open(str(path)) as handle:
            return json.load(handle)

    def status_json(self, now):
        code, out, _ = self.run_session("status", "--now", now, "--json")
        return code, json.loads(out)


QUESTIONS = REPO / "skills" / "sim" / "questions"

# Anything that loops forever regardless of how many arguments the question's
# entry point takes, so it works whichever question the slot happened to pick.
HANGS = "def solve(*args, **kwargs):\n    while True:\n        pass\n"


class BankAwareTestCase(SessionTestCase):
    """Helpers that follow whichever question the session actually chose.

    Slots hold several questions and one is picked at random, so a test cannot
    assume q1 is any particular problem. state.json records each question's
    source in the bank, which is exactly what that field is for.
    """

    def bank_dir(self, index=0):
        return QUESTIONS / self.state()["questions"][index]["source"]

    def install_reference(self, workspace, index=0):
        question = self.state()["questions"][index]
        shutil.copyfile(
            str(QUESTIONS / question["source"] / "reference.py"),
            str(workspace / question["dir"] / "solution.py"),
        )

    def install_partial_mutant(self, workspace, index=0):
        """Install a wrong answer that scores some but not all of the suite."""
        question = self.state()["questions"][index]
        target = workspace / question["dir"] / "solution.py"
        for mutant in sorted((self.bank_dir(index) / "mutants").glob("*.py")):
            shutil.copyfile(str(mutant), str(target))
            _, out, _ = self.run_session(
                "submit", "--question", question["dir"], "--now", T0 + 30, "--json"
            )
            report = json.loads(out)
            if report["outcome"] == "partial":
                return report
        self.fail("no mutant of %s scored partial credit" % (question["id"],))


class TestStart(SessionTestCase):
    def test_creates_workspace_with_public_files_only(self):
        workspace = self.start()
        self.assertTrue((workspace / "README.md").exists())
        self.assertTrue((workspace / ".sim" / "state.json").exists())
        for name in ("problem.md", "solution.py", "tests_public.py"):
            self.assertTrue((workspace / "q1" / name).exists(), name)

    def test_hidden_material_never_reaches_the_workspace(self):
        """The one test that must never be allowed to regress.

        Checks filenames and content: a future refactor that renamed the file
        while still copying it would slip past a name-only assertion.
        """
        workspace = self.start()
        leaked = [
            str(path)
            for path in workspace.rglob("*")
            if "hidden" in path.name or "reference" in path.name
        ]
        self.assertEqual(leaked, [], "hidden material copied into workspace")

        bank = REPO / "skills" / "sim" / "questions" / "gca" / "shelf-tally"
        needle = "test_aisle_with_only_invalid_entries_is_absent"
        self.assertIn(needle, (bank / "tests_hidden.py").read_text())
        for path in workspace.rglob("*"):
            if path.is_file():
                self.assertNotIn(needle, path.read_text(), "hidden test text in %s" % path)

    def test_deadline_is_start_plus_duration(self):
        self.start()
        clock = self.state()["clock"]
        self.assertEqual(clock["started_epoch"], T0)
        self.assertEqual(clock["duration_seconds"], 70 * 60)
        self.assertEqual(clock["deadline_epoch"], T0 + 70 * 60)
        self.assertIsNone(clock["ended_epoch"])

    def test_minutes_override(self):
        self.start(extra=["--minutes", "5"])
        self.assertEqual(self.state()["clock"]["duration_seconds"], 300)

    def test_mode_defaults_to_exam(self):
        self.start()
        self.assertEqual(self.state()["mode"], "exam")

    def test_short_bank_is_an_error_not_a_silent_short_session(self):
        """Asking for more questions than exist must fail loudly.

        Quietly running a 2-question GCA when 4 were asked for would misreport
        what the session actually was.
        """
        code, _, err = self.run_session(
            "start", "--format", "gca", "--questions", "99", "--now", T0
        )
        self.assertEqual(code, EXIT_BANK)
        self.assertIn("--questions", err)

    def test_full_gca_takes_one_question_per_difficulty_slot(self):
        """Not the first four in the bank.

        Once a slot holds more than one question, taking the first N overall
        serves two warm-ups and two mediums and the session stops resembling the
        format it is imitating.
        """
        code, _, err = self.run_session("start", "--format", "gca", "--now", T0)
        self.assertEqual(code, EXIT_OK, err)
        questions = self.state()["questions"]
        self.assertEqual(len(questions), 4)
        self.assertEqual([q["dir"] for q in questions], ["q1", "q2", "q3", "q4"])
        self.assertEqual(questions[0]["difficulty"], "warmup")
        self.assertEqual(questions[-1]["difficulty"], "hard")
        # One from each slot means no repeats.
        self.assertEqual(len(set(q["id"] for q in questions)), 4)

    def test_the_same_seed_gives_the_same_exam(self):
        self.start_seeded(7)
        first = [q["id"] for q in self.state()["questions"]]
        self.run_session("start", "--format", "gca", "--seed", "7", "--now", T0, "--force")
        second = [q["id"] for q in self.state()["questions"]]
        self.assertEqual(first, second)

    def start_seeded(self, seed):
        code, _, err = self.run_session(
            "start", "--format", "gca", "--seed", str(seed), "--now", T0, "--force"
        )
        self.assertEqual(code, EXIT_OK, err)

    def test_different_seeds_can_give_different_questions(self):
        """Sitting the format twice should not be the same exam twice."""
        seen = set()
        for seed in range(12):
            self.start_seeded(seed)
            seen.add(tuple(q["id"] for q in self.state()["questions"]))
        self.assertGreater(len(seen), 1, "question choice never varied across seeds")

    def test_unknown_format(self):
        code, _, _ = self.run_session("start", "--format", "nope", "--now", T0)
        self.assertEqual(code, EXIT_USAGE)


class TestConcurrentSessions(SessionTestCase):
    def test_second_start_is_refused_while_one_runs(self):
        self.start()
        code, _, err = self.run_session(
            "start", "--format", "gca", "--questions", "1", "--now", T0 + 60
        )
        self.assertEqual(code, EXIT_ACTIVE_SESSION)
        self.assertIn("--force", err)

    def test_force_abandons_the_old_session(self):
        first = self.start()
        code, _, _ = self.run_session(
            "start", "--format", "gca", "--questions", "1", "--now", T0 + 60, "--force"
        )
        self.assertEqual(code, EXIT_OK)

        with open(str(first / ".sim" / "state.json")) as handle:
            old = json.load(handle)
        self.assertEqual(old["clock"]["end_reason"], "abandoned")
        self.assertNotEqual(self.workspace(), first)

    def test_start_is_allowed_once_the_previous_session_ended(self):
        self.start()
        self.run_session("status", "--now", T0 + 2 * HOUR)  # observe expiry
        code, _, _ = self.run_session(
            "start", "--format", "gca", "--questions", "1", "--now", T0 + 2 * HOUR
        )
        self.assertEqual(code, EXIT_OK)


class TestStatus(SessionTestCase):
    def test_no_session_at_all(self):
        code, _, err = self.run_session("status", cwd=str(self.root))
        self.assertEqual(code, EXIT_NO_SESSION)
        self.assertIn("start", err)

    def test_remaining_counts_down(self):
        self.start()
        code, payload = self.status_json(T0 + 20 * 60)
        self.assertEqual(code, EXIT_OK)
        self.assertEqual(payload["state"], "active")
        self.assertEqual(payload["remaining_seconds"], 50 * 60)
        self.assertEqual(payload["remaining_display"], "50:00")
        self.assertEqual(payload["elapsed_display"], "20:00")

    def test_expiry_returns_four_and_persists_the_ending(self):
        self.start()
        code, payload = self.status_json(T0 + 70 * 60 + 1)
        self.assertEqual(code, EXIT_EXPIRED)
        self.assertEqual(payload["state"], "ended")
        self.assertEqual(payload["end_reason"], "time")

        clock = self.state()["clock"]
        self.assertEqual(clock["ended_epoch"], T0 + 70 * 60)
        self.assertEqual(clock["end_reason"], "time")

    def test_exactly_at_the_deadline_is_over(self):
        self.start()
        code, payload = self.status_json(T0 + 70 * 60)
        self.assertEqual(code, EXIT_EXPIRED)
        self.assertEqual(payload["state"], "ended")

    def test_expiry_is_idempotent(self):
        """Checking the time twice after the buzzer must give the same answer.

        The ending is stamped at the deadline, not at the moment it was
        noticed, so elapsed does not keep growing after the session is over.
        """
        self.start()
        first_code, first = self.status_json(T0 + 70 * 60 + 1)
        second_code, second = self.status_json(T0 + 5 * HOUR)
        self.assertEqual(first_code, EXIT_EXPIRED)
        self.assertEqual(second_code, EXIT_EXPIRED)
        self.assertEqual(first["elapsed_seconds"], second["elapsed_seconds"])
        self.assertEqual(second["elapsed_display"], "1:10:00")
        self.assertEqual(second["remaining_seconds"], 0)

    def test_resolves_session_from_inside_the_workspace(self):
        workspace = self.start()
        (self.root / "current").unlink()  # force the cwd walk-up path
        code, _, err = self.run_session(
            "status", "--now", T0 + 60, cwd=str(workspace / "q1")
        )
        self.assertEqual(code, EXIT_OK, err)

    def test_json_shape(self):
        self.start()
        _, payload = self.status_json(T0 + 60)
        for key in (
            "session_id",
            "state",
            "mode",
            "format",
            "workspace",
            "remaining_seconds",
            "remaining_display",
            "deadline_utc",
            "questions",
        ):
            self.assertIn(key, payload)
        self.assertEqual(payload["questions"][0]["dir"], "q1")


class TestReport(BankAwareTestCase):
    def start_full(self, now=T0):
        code, out, err = self.run_session("start", "--format", "gca", "--now", now)
        self.assertEqual(code, EXIT_OK, err)
        return self.workspace()

    def test_report_on_an_untouched_session(self):
        self.start_full()
        code, out, _ = self.run_session("report", "--now", T0 + 60, "--json")
        self.assertEqual(code, EXIT_OK)
        payload = json.loads(out)
        self.assertEqual(payload["solved"], 0)
        self.assertEqual(payload["attempted"], 0)
        self.assertEqual(payload["credit"], 0.0)

    def test_a_question_that_never_ran_counts_as_zero_not_as_absent(self):
        """Three perfect answers and one that hangs is 75 percent, not 100.

        Pooling raw test counts drops a timed-out question entirely, because it
        produced no tests to pool, and reports the other three as the whole
        session.
        """
        workspace = self.start_full()
        for index in range(3):
            self.install_reference(workspace, index)
            self.run_session(
                "submit", "--question", "q%d" % (index + 1), "--now", T0 + 60
            )

        (workspace / "q4" / "solution.py").write_text(HANGS)
        self.run_session("submit", "--question", "q4", "--timeout", "3", "--now", T0 + 120)

        _, out, _ = self.run_session("report", "--now", T0 + 200, "--json")
        payload = json.loads(out)
        self.assertEqual(payload["solved"], 3)
        self.assertEqual(payload["questions"], 4)
        self.assertEqual(payload["credit"], 0.75)
        self.assertNotIn("strong", payload["band"])

    def test_report_never_claims_a_200_600_score(self):
        self.start_full()
        _, out, _ = self.run_session("report", "--now", T0 + 60)
        self.assertIn("Unofficial", out)
        self.assertNotIn("200-600 estimate is produced", out.replace("No 200-600", ""))

    def test_report_after_expiry_shows_the_ending(self):
        self.start_full()
        _, out, _ = self.run_session("report", "--now", T0 + 70 * 60 + 5, "--json")
        payload = json.loads(out)
        self.assertEqual(payload["state"], "ended")
        self.assertEqual(payload["end_reason"], "time")
        self.assertEqual(payload["time_used_display"], "1:10:00")


PROJECT = REPO / "skills" / "sim" / "questions" / "ica" / "parcel-locker"


class TestICA(SessionTestCase):
    def start_ica(self, now=T0):
        """Pinned to one project on purpose.

        These tests assert behaviour specific to parcel-locker's levels, and
        project choice is random when none is named. Variety is covered
        separately below.
        """
        code, _, err = self.run_session(
            "start", "--format", "ica", "--project", "parcel-locker", "--now", now
        )
        self.assertEqual(code, EXIT_OK, err)
        return self.workspace()

    def test_project_choice_varies_across_seeds(self):
        seen = set()
        for seed in range(12):
            code, _, err = self.run_session(
                "start", "--format", "ica", "--seed", str(seed), "--now", T0, "--force"
            )
            self.assertEqual(code, EXIT_OK, err)
            seen.add(self.state()["questions"][0]["dir"])
        self.assertGreater(len(seen), 1, "the same ICA project came up every time")

    def test_named_project_is_honoured(self):
        code, _, err = self.run_session(
            "start", "--format", "ica", "--project", "ledger", "--now", T0
        )
        self.assertEqual(code, EXIT_OK, err)
        self.assertEqual(self.state()["questions"][0]["dir"], "ledger")

    def test_unknown_project_is_refused(self):
        code, _, err = self.run_session(
            "start", "--format", "ica", "--project", "nope", "--now", T0
        )
        self.assertEqual(code, EXIT_BANK)

    def solve(self, workspace, source=None):
        shutil.copyfile(
            str(source or (PROJECT / "reference.py")),
            str(workspace / "parcel-locker" / "solution.py"),
        )

    def test_only_level_one_is_on_disk_at_the_start(self):
        """Locked levels must not be readable, which is the point of gating."""
        workspace = self.start_ica()
        project = workspace / "parcel-locker"
        self.assertTrue((project / "level1.md").exists())
        for level in (2, 3, 4):
            self.assertFalse(
                (project / ("level%d.md" % level)).exists(),
                "level %d was readable before it was unlocked" % level,
            )
            self.assertFalse((project / ("tests_public_level%d.py" % level)).exists())

    def test_one_solution_file_not_one_per_level(self):
        workspace = self.start_ica()
        solutions = list(workspace.rglob("solution.py"))
        self.assertEqual(len(solutions), 1)

    def test_locked_level_cannot_be_submitted(self):
        self.start_ica()
        code, _, err = self.run_session("submit", "--question", "2", "--now", T0 + 60)
        self.assertEqual(code, EXIT_USAGE)
        self.assertIn("locked", err)

    def test_unlock_refuses_until_the_level_passes(self):
        self.start_ica()
        code, _, err = self.run_session("unlock", "--now", T0 + 60)
        self.assertEqual(code, EXIT_USAGE)
        self.assertIn("locked", err.lower())

    def test_passing_a_level_unlocks_the_next(self):
        workspace = self.start_ica()
        self.solve(workspace)
        code, out, _ = self.run_session("submit", "--now", T0 + 60)
        self.assertEqual(code, EXIT_OK)
        self.assertIn("Unlocked Level 2", out)
        self.assertTrue((workspace / "parcel-locker" / "level2.md").exists())
        self.assertFalse((workspace / "parcel-locker" / "level3.md").exists())

    def test_submit_with_no_argument_means_the_open_level(self):
        workspace = self.start_ica()
        self.solve(workspace)
        self.run_session("submit", "--now", T0 + 60)
        _, out, _ = self.run_session("submit", "--now", T0 + 120, "--json")
        self.assertEqual(json.loads(out)["question"], "parcel-locker")
        self.assertEqual(self.state()["questions"][1]["state"], "passed")

    def test_regression_grading_reruns_earlier_levels(self):
        """A level 4 answer that breaks level 1 must not score as a pass.

        The mutant implements multi-parcel lockers by dropping the capacity
        check entirely, so every unconfigured locker stops holding exactly one.
        """
        workspace = self.start_ica()
        self.solve(workspace)
        for step in range(3):
            code, _, err = self.run_session("submit", "--now", T0 + 60 * (step + 1))
            self.assertEqual(code, EXIT_OK, err)

        self.solve(workspace, PROJECT / "mutants" / "l4_breaks_l1.py")
        code, out, _ = self.run_session("submit", "--now", T0 + 600, "--json")
        self.assertEqual(code, EXIT_OK)
        report = json.loads(out)
        self.assertNotEqual(report["outcome"], "pass")
        self.assertTrue(report["regression"], "broken level 1 was not flagged")

        by_slot = dict((line["slot"], line) for line in report["per_level"])
        self.assertLess(by_slot[1]["passed"], by_slot[1]["total"])
        self.assertEqual(len(by_slot), 4)

    def test_report_does_not_double_count_cumulative_levels(self):
        """Each level's score already contains the ones below it."""
        workspace = self.start_ica()
        self.solve(workspace)
        for step in range(4):
            self.run_session("submit", "--now", T0 + 60 * (step + 1))
        _, out, _ = self.run_session("report", "--now", T0 + 1000, "--json")
        payload = json.loads(out)
        self.assertEqual(payload["solved"], 4)
        self.assertEqual(payload["credit"], 1.0)
        deepest = payload["detail"][-1]
        self.assertEqual(
            payload["tests_total"],
            int(deepest["summary"].split("/")[1]),
            "totals were summed across levels instead of taken from the deepest",
        )

    def test_stopping_partway_is_scored_as_partway(self):
        workspace = self.start_ica()
        self.solve(workspace)
        self.run_session("submit", "--now", T0 + 60)
        self.run_session("submit", "--now", T0 + 120)
        _, out, _ = self.run_session("report", "--now", T0 + 1000, "--json")
        payload = json.loads(out)
        self.assertEqual(payload["solved"], 2)
        self.assertEqual(payload["credit"], 0.5)

    def test_unlock_is_meaningless_for_gca(self):
        self.run_session("start", "--format", "gca", "--now", T0)
        code, _, err = self.run_session("unlock", "--now", T0 + 60)
        self.assertEqual(code, EXIT_USAGE)
        self.assertIn("unlocked already", err)

    def test_ica_duration_is_ninety_minutes(self):
        self.start_ica()
        self.assertEqual(self.state()["clock"]["duration_seconds"], 90 * 60)


class TestInterviewMode(BankAwareTestCase):
    def start_interview(self, now=T0):
        code, _, err = self.run_session("start", "--mode", "interview", "--now", now)
        self.assertEqual(code, EXIT_OK, err)
        return self.workspace()

    def test_defaults_to_one_question_and_forty_five_minutes(self):
        self.start_interview()
        state = self.state()
        self.assertEqual(state["mode"], "interview")
        self.assertEqual(len(state["questions"]), 1)
        self.assertEqual(state["clock"]["duration_seconds"], 45 * 60)

    def test_explicit_flags_still_win(self):
        code, _, err = self.run_session(
            "start", "--mode", "interview", "--questions", "2",
            "--minutes", "20", "--now", T0,
        )
        self.assertEqual(code, EXIT_OK, err)
        self.assertEqual(len(self.state()["questions"]), 2)
        self.assertEqual(self.state()["clock"]["duration_seconds"], 20 * 60)

    def test_hints_are_recorded(self):
        self.start_interview()
        code, out, err = self.run_session(
            "hint", "--note", "nudged toward a dictionary", "--now", T0 + 60, "--json"
        )
        self.assertEqual(code, EXIT_OK, err)
        self.assertEqual(json.loads(out)["hints"], 1)
        self.assertEqual(self.state()["questions"][0]["hints"], 1)

    def test_hints_accumulate(self):
        self.start_interview()
        for step in range(3):
            self.run_session("hint", "--now", T0 + 60 * (step + 1))
        self.assertEqual(self.state()["questions"][0]["hints"], 3)

    def test_hint_wording_is_kept_in_the_event_log(self):
        """A count alone cannot tell you whether the nudge was small or huge."""
        self.start_interview()
        self.run_session("hint", "--note", "pointed at the empty case", "--now", T0 + 60)
        notes = [e.get("note") for e in self.state()["events"] if e["type"] == "hint"]
        self.assertEqual(notes, ["pointed at the empty case"])

    def test_report_surfaces_hints(self):
        workspace = self.start_interview()
        self.run_session("hint", "--now", T0 + 60)
        self.install_reference(workspace)
        self.run_session("submit", "--now", T0 + 120)
        code, out, _ = self.run_session("report", "--now", T0 + 200, "--json")
        self.assertEqual(code, EXIT_OK)
        payload = json.loads(out)
        self.assertEqual(payload["hints"], 1)
        self.assertEqual(payload["detail"][0]["hints"], 1)

        _, text, _ = self.run_session("report", "--now", T0 + 200)
        self.assertIn("1 hint given", text)

    def test_report_says_so_when_no_hints_were_given(self):
        workspace = self.start_interview()
        self.install_reference(workspace)
        self.run_session("submit", "--now", T0 + 120)
        _, text, _ = self.run_session("report", "--now", T0 + 200)
        self.assertIn("No hints given", text)

    def test_hints_are_refused_in_exam_mode(self):
        """A proctor who hands out hints is not proctoring."""
        self.run_session("start", "--format", "gca", "--now", T0)
        code, _, err = self.run_session("hint", "--question", "q1", "--now", T0 + 60)
        self.assertEqual(code, EXIT_USAGE)
        self.assertIn("interview-mode", err)
        self.assertEqual(self.state()["questions"][0]["hints"], 0)

    def test_hints_are_refused_after_time(self):
        self.start_interview()
        code, _, err = self.run_session("hint", "--now", T0 + 46 * 60)
        self.assertEqual(code, EXIT_EXPIRED)
        self.assertIn("Time is up", err)

    def test_grading_is_unchanged_by_the_mode(self):
        """Only the persona changes. The scripts still own the grades."""
        workspace = self.start_interview()
        self.install_reference(workspace)
        _, out, _ = self.run_session("submit", "--now", T0 + 120, "--json")
        report = json.loads(out)
        self.assertEqual(report["outcome"], "pass")
        self.assertEqual(report["passed"], report["total"])

    def test_late_submission_still_refused_in_interview_mode(self):
        workspace = self.start_interview()
        self.install_reference(workspace)
        code, _, _ = self.run_session("submit", "--now", T0 + 46 * 60)
        self.assertEqual(code, EXIT_EXPIRED)

    def test_exam_mode_reports_do_not_mention_hints(self):
        workspace = self.run_session("start", "--format", "gca", "--questions", "1", "--now", T0)
        _, text, _ = self.run_session("report", "--now", T0 + 60)
        self.assertNotIn("hint", text.lower())


class TestListing(BankAwareTestCase):
    def test_no_sessions(self):
        code, out, _ = self.run_session("list", cwd=str(self.root))
        self.assertEqual(code, EXIT_OK)
        self.assertIn("No sessions", out)

    def test_lists_newest_first(self):
        self.run_session("start", "--format", "gca", "--now", T0)
        self.run_session("start", "--format", "gca", "--now", T0 + HOUR * 3, "--force")
        _, out, _ = self.run_session("list", "--now", T0 + HOUR * 4, "--json")
        rows = json.loads(out)
        self.assertEqual(len(rows), 2)
        self.assertGreater(rows[0]["started_epoch"], rows[1]["started_epoch"])

    def test_marks_the_current_session(self):
        self.run_session("start", "--format", "gca", "--now", T0)
        _, out, _ = self.run_session("list", "--now", T0 + 60)
        self.assertIn("*", out.splitlines()[0])

    def test_an_older_session_is_reachable_by_id(self):
        """Without this the only reachable session is whatever the pointer names."""
        self.run_session("start", "--format", "gca", "--questions", "1", "--now", T0)
        first = self.state()["session_id"]
        self.run_session("start", "--format", "gca", "--now", T0 + HOUR * 3, "--force")

        code, out, err = self.run_session(
            "report", "--session", first, "--now", T0 + HOUR * 4, "--json"
        )
        self.assertEqual(code, EXIT_OK, err)
        self.assertEqual(json.loads(out)["session_id"], first)

    def test_limit(self):
        for step in range(3):
            self.run_session(
                "start", "--format", "gca", "--now", T0 + HOUR * 3 * step, "--force"
            )
        _, out, _ = self.run_session("list", "--limit", "2", "--now", T0, "--json")
        self.assertEqual(len(json.loads(out)), 2)

    def test_time_used_never_exceeds_the_time_available(self):
        """A session abandoned hours late still only had its allotted time.

        The ending of an abandoned session is the moment it was abandoned, which
        can be long past the deadline, and reporting that raw gave "used 3:03:20
        of 1:10:00".
        """
        self.run_session("start", "--format", "gca", "--now", T0)
        self.run_session("start", "--format", "gca", "--now", T0 + HOUR * 3, "--force")
        _, out, _ = self.run_session("list", "--now", T0 + HOUR * 4, "--json")
        abandoned = [row for row in json.loads(out) if row["end_reason"] == "abandoned"]
        self.assertTrue(abandoned)

        _, report, _ = self.run_session(
            "report", "--session", abandoned[0]["session_id"],
            "--now", T0 + HOUR * 4, "--json",
        )
        payload = json.loads(report)
        self.assertEqual(payload["time_used_display"], payload["duration_display"])


class TestSlotSelection(SessionTestCase):
    def test_slot_picks_that_difficulty(self):
        code, _, err = self.run_session(
            "start", "--mode", "interview", "--slot", "4", "--now", T0
        )
        self.assertEqual(code, EXIT_OK, err)
        questions = self.state()["questions"]
        self.assertEqual(len(questions), 1)
        self.assertEqual(questions[0]["difficulty"], "hard")

    def test_slot_one_is_a_warmup(self):
        self.run_session("start", "--mode", "interview", "--slot", "1", "--now", T0)
        self.assertEqual(self.state()["questions"][0]["difficulty"], "warmup")

    def test_unknown_slot_is_refused(self):
        code, _, err = self.run_session("start", "--slot", "9", "--now", T0)
        self.assertEqual(code, EXIT_BANK)
        self.assertIn("Slots available", err)

    def test_asking_for_more_than_a_slot_holds(self):
        code, _, err = self.run_session(
            "start", "--slot", "1", "--questions", "99", "--now", T0
        )
        self.assertEqual(code, EXIT_BANK)


class TestPresets(SessionTestCase):
    def test_a_preset_with_a_known_format_just_runs(self):
        code, out, err = self.run_session(
            "start", "--preset", "capital-one", "--now", T0
        )
        self.assertEqual(code, EXIT_OK, err)
        self.assertEqual(self.state()["format"], "gca")
        self.assertEqual(self.state()["clock"]["duration_seconds"], 70 * 60)

    def test_platform_and_format_confidence_are_reported_separately(self):
        """Conflating them is how a guess becomes received wisdom.

        Capital One is a confirmed CodeSignal customer, which is first-party and
        solid, but the claim that they use the GCA comes from a community repo
        and is several seasons old. Printing "high confidence" next to the
        format would launder the first claim into the second.
        """
        _, out, _ = self.run_session("start", "--preset", "capital-one", "--now", T0)
        self.assertIn("uses CodeSignal (high confidence)", out)
        self.assertIn("Format GCA, medium confidence", out)

    def test_a_preset_with_an_unknown_format_refuses_to_guess(self):
        code, _, err = self.run_session("start", "--preset", "ramp", "--now", T0)
        self.assertEqual(code, EXIT_USAGE)
        self.assertIn("not confirmed", err)
        self.assertIn("--format", err)

    def test_an_unknown_format_preset_runs_once_you_choose(self):
        code, out, err = self.run_session(
            "start", "--preset", "ramp", "--format", "ica", "--now", T0
        )
        self.assertEqual(code, EXIT_OK, err)
        self.assertEqual(self.state()["format"], "ica")
        self.assertIn("not because it was researched", out)

    def test_matching_ignores_case_and_punctuation(self):
        for spelling in ("Capital One", "capital-one", "CAPITALONE"):
            code, _, err = self.run_session(
                "start", "--preset", spelling, "--now", T0, "--force"
            )
            self.assertEqual(code, EXIT_OK, "%s: %s" % (spelling, err))

    def test_unknown_company_lists_the_known_ones(self):
        code, _, err = self.run_session("start", "--preset", "nintendo", "--now", T0)
        self.assertEqual(code, EXIT_BANK)
        self.assertIn("capital-one", err)

    def test_every_preset_carries_its_evidence(self):
        """The validator enforces this in CI; this is the same check at unit level."""
        presets_file = REPO / "skills" / "sim" / "presets.json"
        with open(str(presets_file)) as handle:
            presets = json.load(handle)["presets"]
        self.assertGreater(len(presets), 10)
        for name, entry in presets.items():
            self.assertTrue(entry.get("sources"), "%s cites nothing" % name)
            for source in entry["sources"]:
                self.assertTrue(source.startswith("http"), "%s: %r" % (name, source))
            self.assertRegex(entry.get("last_confirmed", ""), r"^\d{4}-\d{2}-\d{2}$")
            self.assertIn(entry.get("confidence"), ("high", "medium"), name)
            if entry.get("format") is None:
                self.assertIsNone(entry.get("format_confidence"), name)
            else:
                self.assertIn(entry.get("format_confidence"), ("high", "medium"), name)
                self.assertIsInstance(entry.get("minutes"), int, name)


class TestStateFile(SessionTestCase):
    def test_schema_version_is_recorded(self):
        self.start()
        self.assertEqual(self.state()["schema_version"], 2)

    def test_corrupt_state_is_reported_not_crashed(self):
        workspace = self.start()
        (workspace / ".sim" / "state.json").write_text("{not json")
        code, _, err = self.run_session("status", "--now", T0 + 60)
        self.assertNotEqual(code, 0)
        self.assertIn("corrupt", err.lower())

    def test_starts_ungraded(self):
        self.start()
        question = self.state()["questions"][0]
        self.assertEqual(question["attempts"], 0)
        self.assertIsNone(question["result"])
        self.assertEqual(question["state"], "unlocked")


class TestSubmit(BankAwareTestCase):

    def test_correct_solution_scores_full_marks(self):
        workspace = self.start()
        self.install_reference(workspace)
        code, out, err = self.run_session("submit", "--now", T0 + 60, "--json")
        self.assertEqual(code, EXIT_OK, err)
        report = json.loads(out)
        self.assertEqual(report["outcome"], "pass")
        self.assertEqual(report["passed"], report["total"])
        self.assertEqual(report["credit"], 1.0)
        self.assertEqual(report["attempt"], 1)

    def test_untouched_starter_scores_zero(self):
        self.start()
        code, out, _ = self.run_session("submit", "--now", T0 + 60, "--json")
        self.assertEqual(code, EXIT_OK)
        self.assertEqual(json.loads(out)["passed"], 0)

    def test_partial_credit_is_between(self):
        workspace = self.start()
        report = self.install_partial_mutant(workspace)
        self.assertGreater(report["passed"], 0)
        self.assertLess(report["passed"], report["total"])
        self.assertEqual(report["outcome"], "partial")

    def test_unimportable_solution_is_reported_not_crashed(self):
        workspace = self.start()
        (workspace / "q1" / "solution.py").write_text("def solve(entries)\n    return {}\n")
        code, out, _ = self.run_session("submit", "--now", T0 + 60, "--json")
        self.assertEqual(code, EXIT_OK)
        self.assertEqual(json.loads(out)["outcome"], "import_error")

    def test_non_terminating_solution_times_out(self):
        workspace = self.start()
        (workspace / "q1" / "solution.py").write_text(
            "def solve(entries):\n    while True:\n        pass\n"
        )
        code, out, _ = self.run_session(
            "submit", "--now", T0 + 60, "--timeout", "3", "--json"
        )
        self.assertEqual(code, 8)
        self.assertEqual(json.loads(out)["outcome"], "timeout")

    def test_results_are_recorded_in_state(self):
        workspace = self.start()
        self.install_reference(workspace)
        self.run_session("submit", "--now", T0 + 60)
        self.run_session("submit", "--now", T0 + 120)
        question = self.state()["questions"][0]
        self.assertEqual(question["attempts"], 2)
        self.assertEqual(question["result"]["outcome"], "pass")
        self.assertEqual(question["last_submit_epoch"], T0 + 120)

    def test_late_submission_is_rejected_even_when_perfect(self):
        """The lockout. A correct answer after the buzzer is still not accepted."""
        workspace = self.start()
        self.install_reference(workspace)
        code, _, err = self.run_session("submit", "--now", T0 + 70 * 60 + 1)
        self.assertEqual(code, EXIT_EXPIRED)
        self.assertIn("Time is up", err)

        question = self.state()["questions"][0]
        self.assertEqual(question["attempts"], 0, "late attempt was recorded")
        self.assertIsNone(question["result"], "late work was graded")

    def test_submit_with_no_session(self):
        code, _, _ = self.run_session("submit", cwd=str(self.root))
        self.assertEqual(code, EXIT_NO_SESSION)

    def test_unknown_question(self):
        self.start()
        code, _, err = self.run_session("submit", "--question", "q9", "--now", T0 + 60)
        self.assertEqual(code, EXIT_USAGE)
        self.assertIn("q1", err)

    def test_hidden_test_names_never_appear_in_output(self):
        """Counts only. A test name describes the edge case it guards."""
        workspace = self.start()
        (workspace / "q1" / "solution.py").write_text("def solve(entries):\n    return {}\n")
        _, out, err = self.run_session("submit", "--now", T0 + 60)
        _, jout, _ = self.run_session("submit", "--now", T0 + 90, "--json")
        hidden = (self.bank_dir() / "tests_hidden.py").read_text()
        names = [
            line.split("def ")[1].split("(")[0]
            for line in hidden.splitlines()
            if line.strip().startswith("def test_")
        ]
        self.assertGreater(len(names), 10)
        for name in names:
            for stream in (out, err, jout):
                self.assertNotIn(name, stream, "leaked %s" % name)


if __name__ == "__main__":
    unittest.main()
