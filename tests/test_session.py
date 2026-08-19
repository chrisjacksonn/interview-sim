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
EXIT_ENVIRONMENT = 7

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
        env["INTERVIEW_SIM_HOME"] = str(kwargs.get("home", self.root))
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

    def start_with_mutants(self, now=T0):
        """Start a one-question session on a question that ships mutants.

        Basic-tier questions have no mutants/ directory, and which question a
        slot deals is random, so a test needing a known-wrong answer has to ask
        for one rather than assume. Seeds are walked in order so this is
        deterministic.
        """
        for seed in range(40):
            code, out, err = self.run_session(
                "start", "--format", "gca", "--questions", "1",
                "--seed", str(seed), "--now", now, "--force",
            )
            self.assertEqual(code, EXIT_OK, "%s%s" % (out, err))
            if (self.bank_dir(0) / "mutants").is_dir():
                return self.workspace()
        self.fail("no question with mutants was dealt in 40 seeds")

    def install_partial_mutant(self, workspace, index=0):
        """Install a wrong answer that scores some but not all of the suite."""
        question = self.state()["questions"][index]
        target = workspace / question["dir"] / "solution.py"
        mutants = sorted((self.bank_dir(index) / "mutants").glob("*.py"))
        self.assertTrue(mutants, "%s ships no mutants" % (question["id"],))
        for mutant in mutants:
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
        flat = " ".join(out.split())
        self.assertNotIn("200-600 estimate is produced", flat.replace("No 200-600", ""))

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

    def test_forcing_over_an_expired_session_records_it_as_time(self):
        """It ended when the clock ran out, not when it was forced over.

        Recording "abandoned" at the moment of the force stamped the ending
        hours late, so status reported elapsed 11:06:40 on a 1:10:00 session.
        """
        self.run_session("start", "--format", "gca", "--now", T0)
        self.run_session("start", "--format", "gca", "--now", T0 + HOUR * 3, "--force")
        _, out, _ = self.run_session("list", "--now", T0 + HOUR * 4, "--json")
        ended = [row for row in json.loads(out) if row["end_reason"]]
        self.assertTrue(ended)
        self.assertEqual(ended[0]["end_reason"], "time")

        _, payload = self.status_json_for(ended[0]["session_id"], T0 + HOUR * 4)
        self.assertEqual(payload["elapsed_display"], "1:10:00")

    def status_json_for(self, session_id, now):
        code, out, _ = self.run_session(
            "status", "--session", session_id, "--now", now, "--json"
        )
        return code, json.loads(out)

    def test_time_used_never_exceeds_the_time_available(self):
        self.run_session("start", "--format", "gca", "--now", T0)
        self.run_session("start", "--format", "gca", "--now", T0 + HOUR * 3, "--force")
        _, out, _ = self.run_session("list", "--now", T0 + HOUR * 4, "--json")
        ended = [row for row in json.loads(out) if row["end_reason"]]
        _, report, _ = self.run_session(
            "report", "--session", ended[0]["session_id"],
            "--now", T0 + HOUR * 4, "--json",
        )
        payload = json.loads(report)
        self.assertEqual(payload["time_used_display"], payload["duration_display"])

    def test_one_broken_session_does_not_kill_the_listing(self):
        """A file holding valid JSON that is not a session used to exit 1."""
        self.run_session("start", "--format", "gca", "--questions", "1", "--now", T0)
        good = self.state()["session_id"]
        self.run_session(
            "start", "--format", "gca", "--questions", "1",
            "--now", T0 + HOUR, "--force",
        )
        (self.workspace() / ".sim" / "state.json").write_text("[1,2,3]")

        code, out, err = self.run_session("list", "--now", T0 + HOUR * 2)
        self.assertEqual(code, EXIT_OK, err)
        self.assertIn(good, out)
        self.assertIn("unreadable", out)

    def test_interview_mode_is_not_a_warm_up(self):
        """slots[:1] is always slot 1, so the default was an 8 minute question."""
        code, _, err = self.run_session("start", "--mode", "interview", "--now", T0)
        self.assertEqual(code, EXIT_OK, err)
        self.assertNotEqual(self.state()["questions"][0]["difficulty"], "warmup")


class TestOpeningTheEditor(unittest.TestCase):
    """Getting the candidate into the file.

    This went wrong in the way that is hardest to notice from the outside: on a
    machine with VS Code open and running, `which code` found nothing, because
    the "install 'code' command in PATH" step is optional and most people never
    run it. The next candidate in the list was the platform file manager, so
    starting a session opened Finder and threw the candidate out of the editor
    they were working in, at the moment their clock started.
    """

    def module(self):
        sys.path.insert(0, str(SCRIPT.parent))
        try:
            import session

            return session
        finally:
            sys.path.pop(0)

    def test_find_editor_returns_a_real_path_or_nothing(self):
        found = self.module().find_editor()
        if found is None:
            return
        path, family = found
        self.assertTrue(os.path.exists(path), path)
        self.assertIn(family, ("code", "cursor", "subl", "zed"))

    def test_vs_code_is_told_to_reuse_the_window_and_go_to_the_file(self):
        session = self.module()
        launched = []

        def fake_popen(command, **kwargs):
            launched.append(command)

            class Handle(object):
                pass

            return Handle()

        original_find = session.find_editor
        original_popen = session.subprocess.Popen
        session.find_editor = lambda: ("/somewhere/code", "code")
        session.subprocess.Popen = fake_popen
        try:
            workspace = Path(tempfile.mkdtemp())
            target = workspace / "solution.py"
            target.write_text("")
            session.open_in_editor(workspace, target)
        finally:
            session.find_editor = original_find
            session.subprocess.Popen = original_popen
            shutil.rmtree(str(workspace), ignore_errors=True)

        self.assertEqual(launched, [["/somewhere/code", "-r", "-g", str(target)]])

    def test_no_editor_never_means_open_a_file_manager_instead(self):
        """Finder is not a fallback for an editor, it is a different outcome."""
        session = self.module()
        launched = []
        original_find = session.find_editor
        original_popen = session.subprocess.Popen
        session.find_editor = lambda: ("/somewhere/code", "code")
        session.subprocess.Popen = lambda command, **kwargs: launched.append(command)
        try:
            workspace = Path(tempfile.mkdtemp())
            target = workspace / "solution.py"
            target.write_text("")
            session.open_in_editor(workspace, target)
        finally:
            session.find_editor = original_find
            session.subprocess.Popen = original_popen
            shutil.rmtree(str(workspace), ignore_errors=True)
        self.assertNotIn(["open", str(workspace)], launched)


class TestStartIsQuiet(BankAwareTestCase):
    """What a candidate sees when the clock starts.

    The session announces the sitting. It does not explain where the format came
    from, how sure anyone is of it, what the bank holds, or which of their
    requested topics it could not match. All of that is real and all of it is
    available, in `presets` and in the briefing, which is where someone can act
    on it. Recited at the moment the clock starts it reads as a tool apologising
    for itself, and it costs the candidate confidence they need for the next
    forty-five minutes.
    """

    FORBIDDEN = ("bank", "confidence", "researched", "not confirmed", "http")

    def assert_quiet(self, out):
        lowered = out.lower()
        for word in self.FORBIDDEN:
            self.assertNotIn(word, lowered, "start said %r:\n%s" % (word, out))

    def test_a_plain_session_is_quiet(self):
        _, out, _ = self.run_session("start", "--format", "gca", "--now", T0)
        self.assert_quiet(out)

    def test_a_company_session_is_quiet(self):
        _, out, _ = self.run_session(
            "start", "--company", "shopify", "--round", "pairing",
            "--format", "gca", "--mode", "interview", "--now", T0,
        )
        self.assert_quiet(out)
        self.assertIn("pairing round", out)

    def test_it_still_says_what_the_sitting_is(self):
        _, out, _ = self.run_session(
            "start", "--format", "gca", "--mode", "interview", "--now", T0
        )
        self.assertIn("45:00 on the clock", out)


class TestTopics(BankAwareTestCase):
    """Steering the draw by subject.

    This is what replaces copying a company's questions: practise the subjects
    they are reported to ask about, on original problems. So the two things that
    matter are that the steering works, and that what it says about coverage is
    true.
    """

    def topics_of(self, index):
        source = self.state()["questions"][index]["source"]
        with open(str(QUESTIONS / source / "meta.json")) as handle:
            return [tag.lower() for tag in json.load(handle).get("topics", [])]

    def test_a_topic_steers_the_draw(self):
        code, out, err = self.run_session(
            "start", "--format", "gca", "--questions", "2",
            "--topic", "graphs", "--now", T0,
        )
        self.assertEqual(code, EXIT_OK, err)
        drawn = [self.topics_of(index) for index in range(2)]
        self.assertTrue(
            any("graphs" in tags for tags in drawn),
            "asked for graphs, drew %s" % (drawn,),
        )

    def test_several_topics_are_spread_rather_than_stacked(self):
        """Four sliding window questions must not crowd out the graph one."""
        code, out, err = self.run_session(
            "start", "--format", "gca", "--questions", "3",
            "--topic", "graphs", "--topic", "sliding window", "--now", T0,
        )
        self.assertEqual(code, EXIT_OK, err)
        drawn = [self.topics_of(index) for index in range(3)]
        flat = [tag for tags in drawn for tag in tags]
        self.assertIn("graphs", flat)
        self.assertTrue(any("sliding window" in tag for tag in flat), flat)

    def test_a_topic_the_bank_cannot_cover_is_reported_to_everybody(self):
        """This reverses half of an earlier decision, on evidence.

        The original rule was that only the proctor heard about coverage, on the
        grounds that "we had nothing on this so here is something else" reads as
        an apology for the product and is not something a candidate can act on.

        What that produced: somebody preparing for a company's practical
        frontend round was dealt a heap problem and told nothing. The session had
        recorded the topics as uncovered the entire time. They caught it only
        because they knew the company well enough to be suspicious, and most
        people would not have. Silence did not protect their confidence, it
        spent it.

        So the match is now stated. The half of the original rule that stands is
        the other one: never discuss the machinery. The candidate is told what
        subject they are practising, never that a bank exists or what is in it.
        """
        _, out, _ = self.run_session(
            "start", "--format", "gca", "--questions", "2",
            "--topic", "quantum teleportation", "--now", T0, "--json",
        )
        self.assertEqual(
            json.loads(out)["briefing"]["topics"]["uncovered"],
            ["quantum teleportation"],
        )
        _, human, _ = self.run_session(
            "start", "--format", "gca", "--questions", "2",
            "--topic", "quantum teleportation", "--now", T0, "--force",
        )
        # Still never the machinery.
        self.assertNotIn("bank", human.lower())
        # But the subject itself, plainly, where they will see it.
        self.assertIn("topic match: off", human.lower())
        self.assertIn("quantum teleportation", human.lower())

    def test_an_undrawn_topic_is_reported_as_uncovered_by_this_sitting(self):
        """One question, slot 1, and no slot 1 question is a graph question."""
        _, out, _ = self.run_session(
            "start", "--format", "gca", "--questions", "1",
            "--topic", "graphs", "--now", T0, "--json",
        )
        briefing = json.loads(out)["briefing"]
        self.assertEqual(briefing["topics"]["asked"], ["graphs"])
        self.assertEqual(briefing["topics"]["uncovered"], ["graphs"])

    def test_a_topic_never_empties_a_slot(self):
        """Preference, not filter. A full session still appears."""
        code, _, err = self.run_session(
            "start", "--format", "gca", "--topic", "nonsense", "--now", T0
        )
        self.assertEqual(code, EXIT_OK, err)
        self.assertEqual(len(self.state()["questions"]), 4)


class TestCompanyLabels(BankAwareTestCase):
    """Company and round are labels on the record, not keys into anything."""

    def test_they_are_recorded_on_the_session(self):
        code, _, err = self.run_session(
            "start", "--company", "Shopify", "--round", "Pairing",
            "--format", "gca", "--now", T0,
        )
        self.assertEqual(code, EXIT_OK, err)
        state = self.state()
        self.assertEqual(state["company"], "shopify")
        self.assertEqual(state["round"], "pairing")

    def test_an_unknown_company_is_not_a_special_case_any_more(self):
        """Nothing is looked up, so nothing can be missing."""
        code, _, err = self.run_session(
            "start", "--company", "a-company-nobody-has-heard-of",
            "--format", "gca", "--now", T0,
        )
        self.assertEqual(code, EXIT_OK, err)

    def test_the_shape_comes_from_the_flags(self):
        code, _, err = self.run_session(
            "start", "--company", "shopify", "--round", "oa", "--format", "gca",
            "--questions", "2", "--minutes", "60", "--now", T0,
        )
        self.assertEqual(code, EXIT_OK, err)
        state = self.state()
        self.assertEqual(len(state["questions"]), 2)
        self.assertEqual(state["clock"]["duration_seconds"], 60 * 60)

    def test_a_company_without_a_format_still_needs_one(self):
        code, _, err = self.run_session(
            "start", "--company", "shopify", "--now", T0
        )
        self.assertEqual(code, EXIT_USAGE)


class TestSessionDirectoryNames(BankAwareTestCase):
    """The directory is named after the sitting, so a sidebar can be read.

    A column of gca-<timestamp> answered no question anyone had. The company
    and round lead, and the timestamp is a directory below them so repeat
    sittings for one company stack up instead of spreading out.
    """

    def test_the_company_and_round_name_the_group(self):
        workspace = self.start(
            extra=["--company", "Stripe", "--round", "OA", "--force"]
        )
        self.assertEqual(workspace.parent.name, "stripe-oa")
        self.assertEqual(workspace.parent.parent, self.root)
        self.assertEqual(self.state()["session_id"], "stripe-oa/" + workspace.name)

    def test_the_timestamp_is_the_whole_leaf(self):
        """Sorting inside a group has to stay chronological."""
        workspace = self.start(
            extra=["--company", "stripe", "--round", "oa", "--force"]
        )
        self.assertRegex(workspace.name, r"^\d{8}T\d{6}Z$")

    def test_repeat_sittings_share_one_group(self):
        first = self.start(
            now=T0, extra=["--company", "stripe", "--round", "oa", "--force"]
        )
        second = self.start(
            now=T0 + 2 * HOUR,
            extra=["--company", "stripe", "--round", "oa", "--force"],
        )
        self.assertNotEqual(first, second)
        self.assertEqual(first.parent, second.parent)

    def test_the_format_names_the_group_when_no_round_is_given(self):
        """"gca" is our jargon, so it only appears when nothing better exists."""
        workspace = self.start(extra=["--company", "stripe", "--force"])
        self.assertEqual(workspace.parent.name, "stripe-gca")

    def test_a_session_with_no_labels_is_still_grouped(self):
        workspace = self.start(extra=["--force"])
        self.assertEqual(workspace.parent.name, "gca")

    def test_free_text_is_slugged_rather_than_trusted(self):
        """--company is typed by a human and lands in a path."""
        workspace = self.start(
            extra=["--company", "Ernst & Young", "--round", "Take Home", "--force"]
        )
        self.assertEqual(workspace.parent.name, "ernst-young-take-home")

    def test_a_label_that_slugs_to_nothing_falls_back(self):
        """A name of pure punctuation must not produce a "-" directory."""
        workspace = self.start(extra=["--company", "???", "--force"])
        self.assertEqual(workspace.parent.name, "gca")

    def test_a_path_separator_cannot_escape_the_root(self):
        workspace = self.start(
            extra=["--company", "../../etc", "--round", "oa", "--force"]
        )
        self.assertEqual(workspace.parent.parent, self.root)
        self.assertNotIn("..", workspace.parent.name)

    def test_a_non_latin_company_still_names_its_own_folder(self):
        """Stripping to ASCII made the company vanish from its own directory."""
        workspace = self.start(
            extra=["--company", "楽天", "--round", "oa", "--force"]
        )
        self.assertEqual(workspace.parent.name, "楽天-oa")


class TestTwoSittingsInOneSecond(BankAwareTestCase):
    """The name no longer carries the format, so it cannot rely on it to differ.

    Dropping an ICA project into a GCA sitting's directory leaves both sets of
    files in one place and overwrites anything already written there.
    """

    def test_a_second_sitting_does_not_reuse_the_directory(self):
        first = self.start(
            now=T0, extra=["--company", "stripe", "--round", "oa", "--force"]
        )
        second = self.start(
            now=T0, extra=["--company", "stripe", "--round", "oa", "--force"]
        )
        self.assertNotEqual(first, second)
        self.assertEqual(first.parent, second.parent)
        self.assertTrue((first / ".sim" / "state.json").exists())
        self.assertTrue((second / ".sim" / "state.json").exists())

    def test_work_in_the_first_sitting_survives_the_second(self):
        first = self.start(
            now=T0, extra=["--company", "stripe", "--round", "oa", "--force"]
        )
        answer = first / "q1" / "solution.py"
        answer.write_text("# my answer\n")
        self.start(now=T0, extra=["--company", "stripe", "--round", "oa", "--force"])
        self.assertEqual(answer.read_text(), "# my answer\n")

    def test_the_id_matches_where_the_session_actually_is(self):
        self.start(now=T0, extra=["--company", "stripe", "--round", "oa", "--force"])
        second = self.start(
            now=T0, extra=["--company", "stripe", "--round", "oa", "--force"]
        )
        state = json.loads((second / ".sim" / "state.json").read_text())
        self.assertEqual(state["session_id"], "stripe-oa/" + second.name)
        self.assertEqual(Path(state["workspace"]), second)

    def test_two_formats_in_one_second_do_not_share_a_workspace(self):
        """The case the old format-first name got right for free."""
        first = self.start(
            now=T0, extra=["--company", "stripe", "--round", "oa", "--force"]
        )
        code, out, err = self.run_session(
            "start", "--company", "stripe", "--round", "oa", "--format", "ica",
            "--now", T0, "--force",
        )
        self.assertEqual(code, EXIT_OK, "%s%s" % (out, err))
        second = self.workspace()
        self.assertNotEqual(first, second)
        self.assertFalse((second / "q2").exists())


class TestSessionsStayOutOfGit(SessionTestCase):
    """A sitting must not turn into a commit, at any depth."""

    def test_the_root_is_ignored_whole(self):
        import subprocess as sp

        repo = self.root / "repo"
        repo.mkdir()
        for cmd in (
            ["git", "init", "-q", "."],
            ["git", "config", "user.email", "t@t"],
            ["git", "config", "user.name", "t"],
        ):
            sp.check_call(cmd, cwd=str(repo))
        (repo / "README.md").write_text("hi\n")
        sp.check_call(["git", "add", "-A"], cwd=str(repo))
        sp.check_call(["git", "commit", "-qm", "init"], cwd=str(repo))

        code, out, err = self.run_session(
            "start", "--company", "stripe", "--round", "oa", "--format", "gca",
            "--questions", "1", "--now", T0,
            home=repo / "interview-sim-sessions", cwd=str(repo),
        )
        self.assertEqual(code, EXIT_OK, "%s%s" % (out, err))
        status = sp.check_output(
            ["git", "status", "--porcelain"], cwd=str(repo), universal_newlines=True
        )
        self.assertEqual(status, "", "sessions showed up in git:\n%s" % (status,))


class TestSessionLookupByName(BankAwareTestCase):
    """--session takes the id that list prints, and the useful half of it."""

    def test_the_full_id_resolves(self):
        self.start(extra=["--company", "stripe", "--round", "oa", "--force"])
        session_id = self.state()["session_id"]
        code, out, err = self.run_session("status", "--session", session_id, "--now", T0)
        self.assertEqual(code, EXIT_OK, err)
        self.assertIn(session_id, out)

    def test_the_timestamp_alone_resolves_when_it_is_unique(self):
        self.start(extra=["--company", "stripe", "--round", "oa", "--force"])
        session_id = self.state()["session_id"]
        leaf = session_id.split("/")[-1]
        code, out, err = self.run_session("status", "--session", leaf, "--now", T0)
        self.assertEqual(code, EXIT_OK, err)
        self.assertIn(session_id, out)

    def test_an_ambiguous_timestamp_refuses_rather_than_guesses(self):
        """Opening the wrong session silently is worse than saying no."""
        first = self.start(
            now=T0, extra=["--company", "stripe", "--round", "oa", "--force"]
        )
        clone = self.root / "palantir-technical" / first.name
        clone.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(str(first), str(clone))
        code, out, err = self.run_session("status", "--session", first.name, "--now", T0)
        self.assertEqual(code, EXIT_USAGE)
        self.assertIn("stripe-oa/" + first.name, out + err)
        self.assertIn("palantir-technical/" + first.name, out + err)

    def test_an_unknown_name_is_still_an_unknown_name(self):
        self.start(extra=["--force"])
        code, _, _ = self.run_session("status", "--session", "nope", "--now", T0)
        self.assertEqual(code, EXIT_NO_SESSION)


class TestNestedSessionsStayVisible(BankAwareTestCase):
    """History reads directories, and the directories moved a level down."""

    def test_list_finds_a_nested_session(self):
        self.start(extra=["--company", "stripe", "--round", "oa", "--force"])
        session_id = self.state()["session_id"]
        code, out, err = self.run_session("list", "--now", T0)
        self.assertEqual(code, EXIT_OK, err)
        self.assertIn(session_id, out)

    def test_list_still_finds_a_session_sat_before_the_change(self):
        """Flat sessions from an older version are still yours.

        Checked by path rather than by printed id: the id comes out of the
        state file, so a copied session would report the name it was born with
        and prove nothing about where the scan looked.
        """
        workspace = self.start(extra=["--force"])
        legacy = self.root / "gca-20260101T000000Z"
        shutil.copytree(str(workspace), str(legacy))
        shutil.rmtree(str(workspace.parent))
        # A session records its own path and id when it starts, so a copy has to
        # be told where it now lives to stand in for one sat before the change.
        state_file = legacy / ".sim" / "state.json"
        state = json.loads(state_file.read_text())
        state["workspace"] = str(legacy)
        state["session_id"] = legacy.name
        state_file.write_text(json.dumps(state))
        code, out, err = self.run_session("list", "--json", "--now", T0)
        self.assertEqual(code, EXIT_OK, err)
        rows = json.loads(out)
        self.assertEqual([row["session_id"] for row in rows], ["gca-20260101T000000Z"])
        self.assertEqual([Path(row["workspace"]) for row in rows], [legacy])

    def test_scanning_does_not_descend_into_a_session(self):
        """q1/ is not a session, and neither is .sim/."""
        self.start(extra=["--company", "stripe", "--round", "oa", "--force"])
        code, out, err = self.run_session("list", "--json", "--now", T0)
        self.assertEqual(code, EXIT_OK, err)
        self.assertEqual(len(json.loads(out)), 1)


class TestCheck(SessionTestCase):
    """The preflight.

    Its whole value is being right about the environment before a session
    exists, so the failure path matters as much as the happy one.
    """

    def test_a_working_machine_passes(self):
        code, out, err = self.run_session("check")
        self.assertEqual(code, EXIT_OK, err)
        self.assertIn("python", out)
        self.assertIn("Ready", out)
        self.assertNotIn("FAIL", out)

    def test_it_counts_the_bank(self):
        _, out, _ = self.run_session("check", "--json")
        payload = json.loads(out)
        self.assertTrue(payload["ok"])
        bank = [row for row in payload["checks"] if row["name"] == "bank"][0]
        self.assertTrue(bank["ok"])
        self.assertRegex(bank["detail"], r"^\d+ questions? under ")

    def test_an_unwritable_sessions_root_fails_before_a_session_exists(self):
        blocked = self.root / "blocked"
        blocked.mkdir()
        os.chmod(str(blocked), 0o500)
        try:
            code, out, _ = self.run_session(
                "check", home=str(blocked / "sessions")
            )
            self.assertEqual(code, EXIT_ENVIRONMENT)
            self.assertIn("FAIL", out)
            self.assertIn("not writable", out)
        finally:
            os.chmod(str(blocked), 0o700)

    def test_it_hands_over_the_shortcut(self):
        _, out, _ = self.run_session("check", "--json")
        payload = json.loads(out)
        self.assertIn("session.py", payload["shortcut"])
        self.assertTrue(payload["shortcut"].startswith("sim() {"))


class TestProgress(BankAwareTestCase):
    """History across sessions.

    What is being guarded here is honesty as much as arithmetic. Progress is the
    one place a practice tool is tempted to flatter, and every number it prints
    has to be one it actually measured.
    """

    def test_no_sessions(self):
        code, out, _ = self.run_session("progress", cwd=str(self.root))
        self.assertEqual(code, EXIT_OK)
        self.assertIn("No sessions", out)

    def test_a_solved_question_shows_up_with_its_difficulty(self):
        self.run_session("start", "--format", "gca", "--questions", "1", "--now", T0)
        self.install_reference(self.workspace())
        self.run_session("submit", "--question", "q1", "--now", T0 + 600)
        code, out, _ = self.run_session("progress", "--now", T0 + 700, "--json")
        self.assertEqual(code, EXIT_OK)
        payload = json.loads(out)
        self.assertEqual(len(payload["sessions"]), 1)
        row = payload["sessions"][0]
        self.assertEqual(row["solved"], 1)
        self.assertEqual(row["passed"], row["total"])
        self.assertGreater(row["total"], 0)
        self.assertEqual(payload["by_difficulty"][0]["difficulty"], "warmup")
        self.assertEqual(payload["attempted"], 1)

    def test_a_question_never_submitted_is_counted_as_such(self):
        """The number a pass rate hides: what you never reached."""
        self.run_session("start", "--format", "gca", "--now", T0)
        self.install_reference(self.workspace())
        self.run_session("submit", "--question", "q1", "--now", T0 + 600)
        _, out, _ = self.run_session("progress", "--now", T0 + 700, "--json")
        payload = json.loads(out)
        self.assertEqual(payload["attempted"], 1)
        self.assertEqual(payload["never_submitted"], 3)

    def test_time_used_stops_at_the_deadline(self):
        """A session left running overnight did not take nine hours."""
        self.run_session("start", "--format", "gca", "--now", T0)
        _, out, _ = self.run_session("progress", "--now", T0 + HOUR * 9, "--json")
        payload = json.loads(out)
        row = payload["sessions"][0]
        self.assertEqual(row["used_seconds"], row["duration_seconds"])

    def test_sessions_are_newest_first_and_filterable(self):
        self.run_session("start", "--format", "gca", "--now", T0)
        self.run_session("start", "--format", "ica", "--now", T0 + HOUR * 3, "--force")
        _, out, _ = self.run_session("progress", "--now", T0 + HOUR * 4, "--json")
        payload = json.loads(out)
        self.assertEqual([row["format"] for row in payload["sessions"]], ["ica", "gca"])

        _, out, _ = self.run_session(
            "progress", "--format", "gca", "--now", T0 + HOUR * 4, "--json"
        )
        payload = json.loads(out)
        self.assertEqual(len(payload["sessions"]), 1)
        self.assertEqual(payload["sessions"][0]["format"], "gca")

    def test_it_refuses_to_pretend_a_percentage_is_a_score(self):
        self.run_session("start", "--format", "gca", "--questions", "1", "--now", T0)
        self.install_reference(self.workspace())
        self.run_session("submit", "--question", "q1", "--now", T0 + 600)
        _, out, _ = self.run_session("progress", "--now", T0 + 700)
        flat = " ".join(out.split())
        self.assertIn("A history, not a score", flat)
        self.assertNotIn("200-600", flat)


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


class TestWorkspaceReadme(SessionTestCase):
    def test_the_documented_test_command_actually_works(self):
        """The first instruction a candidate follows must not fail.

        It used to say `unittest discover -s q1 -t .` from the workspace root,
        which dies with "Start directory is not importable" because the question
        directory is not a package. Running from inside it is what works.
        """
        workspace = self.start()
        readme = (workspace / "README.md").read_text()
        self.assertIn("cd q1", readme)
        self.assertIn("python3 -m unittest tests_public", readme)
        self.assertNotIn("discover -s", readme)

        proc = subprocess.Popen(
            [sys.executable, "-m", "unittest", "tests_public"],
            cwd=str(workspace / "q1"),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
        )
        _, err = proc.communicate()
        # The starter is unfilled so the tests fail, but they must RUN. The
        # count is not asserted: questions carry different numbers of public
        # tests and the slot draws at random, so a fixed number here is a test
        # that passes or fails on the roll of a die.
        self.assertNotIn("is not importable", err)
        self.assertRegex(err, r"Ran [1-9]\d* tests?")

    def test_the_readme_says_how_to_submit(self):
        workspace = self.start()
        readme = (workspace / "README.md").read_text()
        self.assertIn("submit", readme)
        self.assertIn("report", readme)

    def test_the_ica_readme_explains_gating(self):
        code, _, err = self.run_session(
            "start", "--format", "ica", "--project", "ledger", "--now", T0
        )
        self.assertEqual(code, EXIT_OK, err)
        readme = (self.workspace() / "README.md").read_text()
        self.assertIn("How the levels work", readme)
        self.assertIn("re-runs the levels below", readme)
        self.assertIn("one `solution.py`", readme)
        # It must not talk about several solution files when there is one.
        self.assertNotIn("each `solution.py`", readme)


class TestAuditRegressions(BankAwareTestCase):
    """Bugs found by the six-lens audit. Each one produced a wrong result."""

    PROJECT = REPO / "skills" / "sim" / "questions" / "ica" / "parcel-locker"

    def start_ica(self, now=T0):
        code, _, err = self.run_session(
            "start", "--format", "ica", "--project", "parcel-locker", "--now", now
        )
        self.assertEqual(code, EXIT_OK, err)
        return self.workspace()

    def solve(self, workspace, source=None):
        shutil.copyfile(
            str(source or (self.PROJECT / "reference.py")),
            str(workspace / "parcel-locker" / "solution.py"),
        )

    def test_a_printing_solution_still_scores_correctly(self):
        """Results used to come back on the child's stdout.

        A stray debug print landed in the middle of the JSON and a fully correct
        solution was reported as "0 of 0 hidden tests passed (0%)". A print left
        in the file is the single most likely thing under time pressure.
        """
        workspace = self.start()
        question = self.state()["questions"][0]
        reference = (QUESTIONS / question["source"] / "reference.py").read_text()
        (workspace / question["dir"] / "solution.py").write_text(
            "import sys\nprint('debugging')\nprint('noise', file=sys.stderr)\n" + reference
        )
        code, out, err = self.run_session("submit", "--now", T0 + 60, "--json")
        self.assertEqual(code, EXIT_OK, err)
        report = json.loads(out)
        self.assertEqual(report["outcome"], "pass")
        self.assertEqual(report["passed"], report["total"])
        self.assertGreater(report["total"], 0)

    def test_a_solution_printing_fake_results_cannot_forge_a_score(self):
        workspace = self.start()
        question = self.state()["questions"][0]
        forged = json.dumps(
            {"loaded": True, "load_error": None, "total": 999, "passed": 999,
             "failed": 0, "errored": 0, "skipped": 0, "failing": []}
        )
        (workspace / question["dir"] / "solution.py").write_text(
            "print(%r)\ndef solve(*a, **k):\n    return None\n" % (forged,)
        )
        _, out, _ = self.run_session("submit", "--now", T0 + 60, "--json")
        report = json.loads(out)
        self.assertNotEqual(report["total"], 999)
        self.assertNotEqual(report["outcome"], "pass")

    def test_an_ica_level_that_times_out_is_not_a_pass(self):
        """It used to be reported as 100%, marked passed, and unlock the next.

        A level whose tests never ran reports 0 of 0, which cannot move
        `passed == total`, so the earlier levels' counts declared a pass on
        their own.
        """
        workspace = self.start_ica()
        self.solve(workspace)
        self.run_session("submit", "--now", T0 + 60)

        source = (self.PROJECT / "reference.py").read_text().replace(
            "    def parcel_count(self):",
            "    def parcel_count(self):\n        while True:\n            pass",
        )
        (workspace / "parcel-locker" / "solution.py").write_text(source)

        code, out, _ = self.run_session(
            "submit", "--question", "2", "--timeout", "5", "--now", T0 + 120, "--json"
        )
        self.assertEqual(code, 8, "a level that hung must exit as a timeout")
        report = json.loads(out)
        self.assertEqual(report["outcome"], "timeout")
        self.assertEqual(report["credit"], 0.0, "a level that never ran is a zero")

        states = [q["state"] for q in self.state()["questions"]]
        self.assertNotEqual(states[1], "passed", "a hung level was marked passed")
        self.assertEqual(states[2], "locked", "a hung level unlocked the next one")

    def test_report_reflects_a_regression_rather_than_stale_results(self):
        """submit said regression and report said "passed 3 of 4"."""
        workspace = self.start_ica()
        self.solve(workspace)
        for step in range(3):
            self.run_session("submit", "--now", T0 + 60 * (step + 1))

        self.solve(workspace, self.PROJECT / "mutants" / "l4_breaks_l1.py")
        self.run_session("submit", "--now", T0 + 600)

        _, out, _ = self.run_session("report", "--now", T0 + 700, "--json")
        payload = json.loads(out)
        self.assertLess(payload["solved"], 3, "report still credits broken levels")

        _, text, _ = self.run_session("report", "--now", T0 + 700)
        self.assertIn("regression", text.lower())

    def test_two_overlapping_submits_do_not_lose_a_result(self):
        """Both used to grade, both printed a score, one was discarded."""
        workspace = self.start()
        question = self.state()["questions"][0]
        self.install_reference(workspace)

        env = dict(os.environ)
        env["INTERVIEW_SIM_HOME"] = str(self.root)
        procs = [
            subprocess.Popen(
                [sys.executable, str(SCRIPT), "submit", "--question",
                 question["dir"], "--now", str(T0 + 60 + index)],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                env=env, cwd=str(REPO), universal_newlines=True,
            )
            for index in range(3)
        ]
        for proc in procs:
            proc.communicate()

        recorded = self.state()["questions"][0]
        self.assertEqual(
            recorded["attempts"], 3,
            "concurrent submits were graded but not all recorded",
        )
        self.assertIsNotNone(recorded["result"])


class TestQuestionRotation(SessionTestCase):
    def test_consecutive_sittings_do_not_repeat(self):
        """Drawing independently each time repeated a question 98.7% of runs.

        Measured over the real selector before rotation existed: three sittings
        repeated at least one question almost always, and the warm-up repeated
        back to back a third of the time. That is memory practice.
        """
        seen = []
        for index in range(3):
            code, _, err = self.run_session(
                "start", "--format", "gca", "--force", "--now", T0 + index * 100
            )
            self.assertEqual(code, EXIT_OK, err)
            seen.extend(q["id"] for q in self.state()["questions"])
        self.assertEqual(len(seen), len(set(seen)), "a question repeated: %s" % (seen,))

    def test_a_seed_still_reproduces_regardless_of_history(self):
        """--seed promises the same exam from the same number.

        Letting history shift a seeded draw would make that promise depend on
        what this machine happened to have run before.
        """
        first = None
        for index in range(3):
            self.run_session("start", "--format", "gca", "--force", "--now", T0 + index)
        for _ in range(2):
            self.run_session(
                "start", "--format", "gca", "--seed", "7", "--force", "--now", T0
            )
            ids = [q["id"] for q in self.state()["questions"]]
            if first is None:
                first = ids
            self.assertEqual(ids, first)

    def test_the_bank_starts_over_once_everything_has_been_seen(self):
        """Rotation must never run out of questions to serve."""
        for index in range(6):
            code, _, err = self.run_session(
                "start", "--format", "gca", "--force", "--now", T0 + index * 100
            )
            self.assertEqual(code, EXIT_OK, err)
            self.assertEqual(len(self.state()["questions"]), 4)

    def test_an_unreadable_history_file_does_not_stop_a_session(self):
        (self.root).mkdir(parents=True, exist_ok=True)
        (self.root / "history.json").write_text("{not json")
        code, _, err = self.run_session("start", "--format", "gca", "--now", T0)
        self.assertEqual(code, EXIT_OK, err)


class TestGeneratedQuestions(SessionTestCase):
    """Questions written on the spot, which is now the primary path.

    They pass the same gate the corpus passes in CI, before the clock starts,
    because that is the only moment a rejection is free: the reference must
    pass, the starter must fail, and every mutant must be caught. A generated
    question used to skip the mutation half and disclose it; once generation
    became the default rather than the fallback, that disclosure would have
    covered every sitting.
    """

    GOOD_REFERENCE = (
        "def solve(payments):\n"
        "    totals = {}\n"
        "    for merchant, amount in payments:\n"
        "        if amount < 0:\n"
        "            continue\n"
        "        totals[merchant] = totals.get(merchant, 0) + amount\n"
        "    return totals\n"
    )
    TESTS = (
        "import unittest\n"
        "from solution import solve\n"
        "class T(unittest.TestCase):\n"
        "    def test_sums(self):\n"
        "        self.assertEqual(solve([('a', 1), ('a', 2)]), {'a': 3})\n"
        "    def test_skips_negative(self):\n"
        "        self.assertEqual(solve([('a', -1), ('a', 2)]), {'a': 2})\n"
    )

    def write_question(self, root, reference=None, starter=None, mutants=True):
        question = Path(root) / "generated-one"
        question.mkdir(parents=True, exist_ok=True)
        (question / "meta.json").write_text('{"id": "generated-one", "title": "Generated"}')
        (question / "problem.md").write_text("# Generated\n\nTotal by merchant.\n")
        (question / "starter.py").write_text(
            starter or "def solve(payments):\n    raise NotImplementedError\n"
        )
        (question / "reference.py").write_text(reference or self.GOOD_REFERENCE)
        (question / "tests_public.py").write_text(self.TESTS)
        (question / "tests_hidden.py").write_text(self.TESTS)
        if mutants:
            directory = question / "mutants"
            directory.mkdir(exist_ok=True)
            # Three plausible wrong answers, each caught by the suite above:
            # returns nothing, counts negatives, only keeps the last payment.
            (directory / "empty.py").write_text(
                "def solve(payments):\n    return {}\n"
            )
            (directory / "keeps_negative.py").write_text(
                "def solve(payments):\n"
                "    totals = {}\n"
                "    for merchant, amount in payments:\n"
                "        totals[merchant] = totals.get(merchant, 0) + amount\n"
                "    return totals\n"
            )
            (directory / "last_wins.py").write_text(
                "def solve(payments):\n"
                "    totals = {}\n"
                "    for merchant, amount in payments:\n"
                "        if amount >= 0:\n"
                "            totals[merchant] = amount\n"
                "    return totals\n"
            )
        return Path(root)

    def test_a_generated_question_can_be_sat_and_graded(self):
        root = self.write_question(self.root / "gen")
        code, out, err = self.run_session(
            "start", "--format", "gca", "--questions", "1",
            "--generated", str(root), "--now", T0,
        )
        self.assertEqual(code, EXIT_OK, err)
        # The candidate is not told which shelf their question came off. The
        # proctor is, in the briefing, because it changes how much the grade is
        # worth.
        self.assertNotIn("bank", out.lower())
        self.assertTrue(self.state()["generated"])
        _, brief, _ = self.run_session(
            "start", "--format", "gca", "--questions", "1",
            "--generated", str(root), "--now", T0, "--force", "--json",
        )
        self.assertTrue(json.loads(brief)["briefing"]["generated"])

        workspace = self.workspace()
        (workspace / "q1" / "solution.py").write_text(self.GOOD_REFERENCE)
        code, out, _ = self.run_session("submit", "--question", "q1", "--now", T0 + 60, "--json")
        self.assertEqual(code, EXIT_OK)
        report = json.loads(out)
        self.assertEqual(report["outcome"], "pass")
        self.assertGreater(report["total"], 0)

    def test_hidden_material_still_never_reaches_the_workspace(self):
        root = self.write_question(self.root / "gen")
        self.run_session(
            "start", "--format", "gca", "--questions", "1",
            "--generated", str(root), "--now", T0,
        )
        leaked = [
            str(path) for path in self.workspace().rglob("*")
            if "hidden" in path.name or "reference" in path.name
        ]
        self.assertEqual(leaked, [])

    def test_an_unanswerable_question_is_refused_before_the_clock_starts(self):
        """Its own reference fails its own tests, so nobody could pass it."""
        root = self.write_question(
            self.root / "gen", reference="def solve(payments):\n    return {}\n"
        )
        code, _, err = self.run_session(
            "start", "--format", "gca", "--questions", "1",
            "--generated", str(root), "--now", T0,
        )
        self.assertEqual(code, EXIT_BANK)
        self.assertIn("unanswerable", err)

    def test_no_mutants_is_refused(self):
        """The gate is the quality claim, and generation is the primary path
        now, so a generated suite proves it discriminates or it does not run."""
        root = self.write_question(self.root / "gen", mutants=False)
        code, _, err = self.run_session(
            "start", "--format", "gca", "--questions", "1",
            "--generated", str(root), "--now", T0,
        )
        self.assertEqual(code, EXIT_BANK)
        self.assertIn("mutant", err)

    def test_a_surviving_mutant_is_refused(self):
        """A wrong answer the suite passes means the grade is worthless."""
        root = self.write_question(self.root / "gen")
        # A "wrong" solution that is actually correct survives any honest suite.
        (root / "generated-one" / "mutants" / "survivor.py").write_text(
            self.GOOD_REFERENCE
        )
        code, _, err = self.run_session(
            "start", "--format", "gca", "--questions", "1",
            "--generated", str(root), "--now", T0,
        )
        self.assertEqual(code, EXIT_BANK)
        self.assertIn("cannot discriminate", err)
        self.assertIn("survivor.py", err)

    def test_pytest_style_suites_are_named_as_the_cause(self):
        """Zero collected tests must say why, not just score 0/0.

        The first live run to hit this spent two minutes reading engine source
        to diagnose it: the suites were plain functions, unittest collected
        nothing, and the refusal said only that the reference failed.
        """
        root = self.write_question(self.root / "gen")
        plain = (
            "from solution import solve\n"
            "def test_sums():\n"
            "    assert solve([('a', 1)]) == {'a': 1}\n"
        )
        (root / "generated-one" / "tests_hidden.py").write_text(plain)
        code, _, err = self.run_session(
            "start", "--format", "gca", "--questions", "1",
            "--generated", str(root), "--now", T0,
        )
        self.assertEqual(code, EXIT_BANK)
        self.assertIn("unittest.TestCase", err)
        self.assertIn("pytest-style", err)

    def test_an_empty_public_suite_is_refused(self):
        root = self.write_question(self.root / "gen")
        (root / "generated-one" / "tests_public.py").write_text("# nothing\n")
        code, _, err = self.run_session(
            "start", "--format", "gca", "--questions", "1",
            "--generated", str(root), "--now", T0,
        )
        self.assertEqual(code, EXIT_BANK)
        self.assertIn("no tests in tests_public.py", err)

    def test_a_patch_mutant_is_composed_and_graded(self):
        """One-line breaks declared as OLD/NEW, composed against the reference.

        Re-typing the whole reference to change one line made mutants most of
        the tokens in a generated set, so a patch declares just the break.
        """
        root = self.write_question(self.root / "gen")
        directory = root / "generated-one" / "mutants"
        # Replace one full mutant with an equivalent patch: the reference
        # skips negatives via `continue`; breaking that keeps them.
        (directory / "empty.py").unlink()
        (directory / "keeps_negative.py").unlink()
        (directory / "keeps_negative.py").write_text(
            '# keeps negative amounts\n'
            'OLD = "if amount < 0:"\n'
            'NEW = "if amount < -10**18:"\n'
        )
        code, out, err = self.run_session(
            "start", "--format", "gca", "--questions", "1",
            "--generated", str(root), "--now", T0,
        )
        self.assertEqual(code, EXIT_BANK, err)
        # Two mutants only, so the floor refuses: proves the patch COUNTED.
        self.assertIn("2 mutant(s), needs 3", err)

        (directory / "empty.py").write_text(
            "def solve(payments):\n    return {}\n"
        )
        code, _, err = self.run_session(
            "start", "--format", "gca", "--questions", "1",
            "--generated", str(root), "--now", T0,
        )
        self.assertEqual(code, EXIT_OK, err)

    def test_a_patch_matching_nothing_is_refused_with_the_reason(self):
        root = self.write_question(self.root / "gen")
        (root / "generated-one" / "mutants" / "ghost.py").write_text(
            'OLD = "text that is not in the reference"\nNEW = "something"\n'
        )
        code, _, err = self.run_session(
            "start", "--format", "gca", "--questions", "1",
            "--generated", str(root), "--now", T0,
        )
        self.assertEqual(code, EXIT_BANK)
        self.assertIn("matches nothing", err)

    def test_a_patch_matching_twice_is_refused(self):
        """An ambiguous snippet composes silently into the wrong mutant."""
        root = self.write_question(self.root / "gen")
        question = root / "generated-one"
        (question / "reference.py").write_text(
            "def solve(payments):\n"
            "    totals = {}\n"
            "    for merchant, amount in payments:\n"
            "        if amount < 0:\n"
            "            continue\n"
            "        if amount < 0:\n"
            "            continue\n"
            "        totals[merchant] = totals.get(merchant, 0) + amount\n"
            "    return totals\n"
        )
        (question / "mutants" / "ambiguous.py").write_text(
            'OLD = "if amount < 0:"\nNEW = "if amount <= 0:"\n'
        )
        code, _, err = self.run_session(
            "start", "--format", "gca", "--questions", "1",
            "--generated", str(root), "--now", T0,
        )
        self.assertEqual(code, EXIT_BANK)
        self.assertIn("matches 2 places", err)

    def test_a_patch_equal_to_the_reference_is_refused(self):
        root = self.write_question(self.root / "gen")
        (root / "generated-one" / "mutants" / "noop.py").write_text(
            'OLD = "if amount < 0:"\nNEW = "if amount < 0:"\n'
        )
        code, _, err = self.run_session(
            "start", "--format", "gca", "--questions", "1",
            "--generated", str(root), "--now", T0,
        )
        self.assertEqual(code, EXIT_BANK)
        self.assertIn("identical", err)

    def test_a_surviving_patch_mutant_is_named(self):
        """A break the suite cannot see is still a refusal, composed or not."""
        root = self.write_question(self.root / "gen")
        # Changing a dict literal the tests never exercise: composes fine,
        # passes the suite, and must therefore be refused as a survivor.
        (root / "generated-one" / "reference.py").write_text(
            "UNUSED_LABEL = 'a'\n"
            + self.GOOD_REFERENCE
        )
        (root / "generated-one" / "mutants" / "survivor.py").write_text(
            "OLD = \"UNUSED_LABEL = 'a'\"\nNEW = \"UNUSED_LABEL = 'b'\"\n"
        )
        code, _, err = self.run_session(
            "start", "--format", "gca", "--questions", "1",
            "--generated", str(root), "--now", T0,
        )
        self.assertEqual(code, EXIT_BANK)
        self.assertIn("survivor.py", err)
        self.assertIn("cannot discriminate", err)

    def test_a_question_set_inside_the_working_directory_is_refused(self):
        """The set is the answer key. Built where the candidate works, it shows
        in their file tree one click from the problem, which happened twice."""
        root = self.write_question(self.root / "gen")
        code, _, err = self.run_session(
            "start", "--format", "gca", "--questions", "1",
            "--generated", str(root), "--now", T0, cwd=str(self.root),
        )
        self.assertEqual(code, EXIT_BANK)
        self.assertIn("answer key", err)

    def test_a_question_set_inside_the_working_directory_is_refused(self):
        """The set is the answer key. Built where the candidate works, it shows
        in their file tree one click from the problem, which happened twice."""
        root = self.write_question(self.root / "gen")
        code, _, err = self.run_session(
            "start", "--format", "gca", "--questions", "1",
            "--generated", str(root), "--now", T0, cwd=str(self.root),
        )
        self.assertEqual(code, EXIT_BANK)
        self.assertIn("answer key", err)

    def test_a_question_that_asks_for_nothing_is_refused(self):
        root = self.write_question(self.root / "gen", starter=self.GOOD_REFERENCE)
        code, _, err = self.run_session(
            "start", "--format", "gca", "--questions", "1",
            "--generated", str(root), "--now", T0,
        )
        self.assertEqual(code, EXIT_BANK)
        self.assertIn("asks for nothing", err)

    def test_a_directory_missing_files_is_refused(self):
        root = self.write_question(self.root / "gen")
        (root / "generated-one" / "tests_hidden.py").unlink()
        code, _, err = self.run_session(
            "start", "--format", "gca", "--questions", "1",
            "--generated", str(root), "--now", T0,
        )
        self.assertEqual(code, EXIT_BANK)
        self.assertIn("tests_hidden.py", err)

    def test_an_empty_directory_is_refused(self):
        empty = self.root / "empty"
        empty.mkdir(parents=True, exist_ok=True)
        code, _, err = self.run_session(
            "start", "--format", "gca", "--questions", "1",
            "--generated", str(empty), "--now", T0,
        )
        self.assertEqual(code, EXIT_BANK)

    def test_bank_sessions_are_not_marked_generated(self):
        self.start()
        self.assertFalse(self.state()["generated"])


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
        workspace = self.start_with_mutants()
        report = self.install_partial_mutant(workspace)
        self.assertGreater(report["passed"], 0)
        self.assertLess(report["passed"], report["total"])
        self.assertEqual(report["outcome"], "partial")

    def test_unimportable_solution_is_reported_not_crashed(self):
        workspace = self.start()
        (workspace / "q1" / "solution.py").write_text("def solve(entries)\n    return {}\n")
        code, out, _ = self.run_session("submit", "--now", T0 + 60, "--json")
        self.assertEqual(code, 9, "a file that does not import must not exit 0")
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


class TimeAttributionTests(SessionTestCase):
    """Where the clock went, which is the thing the format actually tests.

    Edits are observed through file mtimes, so these set mtimes explicitly with
    os.utime rather than sleeping. That is the same code path a real edit takes:
    the engine has no watcher and only ever reads st_mtime.
    """

    def start_exam(self, questions=4, now=T0):
        code, out, err = self.run_session(
            "start", "--format", "gca", "--questions", questions, "--now", now
        )
        self.assertEqual(code, EXIT_OK, "start failed: %s%s" % (out, err))
        return self.workspace()

    def touch(self, workspace, directory, at, body="# work\n"):
        path = workspace / directory / "solution.py"
        path.write_text(path.read_text() + body)
        os.utime(str(path), (at, at))

    def report_json(self, now):
        code, out, err = self.run_session("report", "--now", now, "--json")
        self.assertIn(code, (EXIT_OK, EXIT_EXPIRED), err)
        return json.loads(out)

    def line(self, payload, directory):
        for line in payload["detail"]:
            if line["dir"] == directory:
                return line
        raise AssertionError("no line for %s" % (directory,))

    def test_copying_the_starters_is_not_an_edit(self):
        """Otherwise every session opens with its first question already ahead."""
        self.start_exam()
        events = [e for e in self.state()["events"] if e["type"] == "edited"]
        self.assertEqual(events, [])

    def test_an_untouched_question_is_never_opened(self):
        workspace = self.start_exam()
        self.touch(workspace, "q1", T0 + 600)
        payload = self.report_json(T0 + 1200)
        self.assertTrue(self.line(payload, "q1")["opened"])
        self.assertFalse(self.line(payload, "q4")["opened"])
        self.assertIn("q4", payload["timing"]["never_opened"])

    def test_time_lands_on_the_question_that_was_edited(self):
        workspace = self.start_exam()
        self.touch(workspace, "q1", T0 + 300)
        self.run_session("status", "--now", T0 + 310)
        self.touch(workspace, "q2", T0 + 900)
        payload = self.report_json(T0 + 1000)
        # q1 ran from its first edit to q2's: ten minutes.
        self.assertAlmostEqual(self.line(payload, "q1")["seconds"], 600.0, delta=1.0)
        self.assertAlmostEqual(payload["timing"]["reading_seconds"], 300.0, delta=1.0)

    def test_the_opening_stretch_is_reading_not_the_first_question(self):
        """Nothing had been written yet, so it cannot be work on anything."""
        workspace = self.start_exam()
        self.touch(workspace, "q2", T0 + 480)
        payload = self.report_json(T0 + 600)
        self.assertAlmostEqual(payload["timing"]["reading_seconds"], 480.0, delta=1.0)
        # q2 owns only what came after it was touched, not the eight minutes
        # spent reading before anything was written.
        self.assertAlmostEqual(self.line(payload, "q2")["seconds"], 120.0, delta=1.0)

    def test_the_pieces_add_up_to_the_time_used(self):
        workspace = self.start_exam()
        for directory, at in (("q1", 300), ("q2", 1500), ("q1", 2000), ("q3", 3000)):
            self.touch(workspace, directory, T0 + at)
            self.run_session("status", "--now", T0 + at + 5)
        payload = self.report_json(T0 + 70 * 60 + 500)
        total = (
            sum(line["seconds"] for line in payload["detail"])
            + payload["timing"]["reading_seconds"]
        )
        self.assertAlmostEqual(total, 70 * 60, delta=2.0)

    def test_going_back_to_an_earlier_question_adds_to_it(self):
        workspace = self.start_exam()
        self.touch(workspace, "q1", T0 + 300)
        self.run_session("status", "--now", T0 + 310)
        self.touch(workspace, "q2", T0 + 600)
        self.run_session("status", "--now", T0 + 610)
        self.touch(workspace, "q1", T0 + 900)
        payload = self.report_json(T0 + 1000)
        # q1 owns 300->600 and again 900->1000; q2 owns 600->900 in between.
        self.assertAlmostEqual(self.line(payload, "q1")["seconds"], 400.0, delta=1.0)
        self.assertAlmostEqual(self.line(payload, "q2")["seconds"], 300.0, delta=1.0)

    def test_an_edit_with_an_older_mtime_still_counts(self):
        """Editors write through temp files and restores move mtimes backwards.

        A file that is not what it was is an edit whichever way its clock went.
        """
        workspace = self.start_exam()
        self.touch(workspace, "q1", T0 + 900)
        self.run_session("status", "--now", T0 + 910)
        self.touch(workspace, "q1", T0 + 400)
        self.run_session("status", "--now", T0 + 920)
        edits = [e for e in self.state()["events"] if e["type"] == "edited"]
        self.assertEqual(len(edits), 2)

    def test_report_prints_the_section(self):
        workspace = self.start_exam()
        self.touch(workspace, "q1", T0 + 600)
        code, out, _ = self.run_session("report", "--now", T0 + 1200)
        self.assertIn("Where the time went", out)
        self.assertIn("not opened", out)

    def test_never_reading_the_files_says_nothing_rather_than_guessing(self):
        """A sitting where no command ever saw an edit has no timeline, and an
        empty one is better than an invented one."""
        self.start_exam()
        payload = self.report_json(T0 + 1200)
        self.assertFalse(payload["timing"]["observed"])
        code, out, _ = self.run_session("report", "--now", T0 + 1200)
        self.assertNotIn("Where the time went", out)

    def test_gated_levels_are_timed_from_their_unlock(self):
        code, out, err = self.run_session(
            "start", "--format", "ica", "--project", "parcel-locker", "--now", T0
        )
        self.assertEqual(code, EXIT_OK, err)
        workspace = self.workspace()
        project = workspace / "parcel-locker"
        reference = QUESTIONS / "ica" / "parcel-locker" / "reference.py"
        (project / "solution.py").write_text(reference.read_text())
        self.run_session("submit", "--now", T0 + 600)
        payload = self.report_json(T0 + 90 * 60 + 100)
        levels = payload["detail"]
        # Level 1 ran from the start to the moment level 2 unlocked.
        self.assertAlmostEqual(levels[0]["seconds"], 600.0, delta=2.0)
        self.assertTrue(levels[0]["opened"])
        # Level 3 never unlocked, so it was never reached.
        self.assertFalse(levels[2]["opened"])


class TestStartsOnTheProblem(SessionTestCase):
    """The first thing in front of someone is the question, not an empty file.

    Landing in the starter invites typing before reading, which is the habit
    these formats punish hardest.
    """

    def test_the_listing_names_the_problem_not_the_starter(self):
        code, out, err = self.run_session(
            "start", "--format", "gca", "--questions", 2, "--now", T0
        )
        self.assertEqual(code, EXIT_OK, err)
        self.assertIn("q1/problem.md", out)
        self.assertNotIn("q1/solution.py", out)

    def test_it_says_to_read_first_and_write_after(self):
        code, out, err = self.run_session(
            "start", "--format", "gca", "--questions", 2, "--now", T0
        )
        self.assertEqual(code, EXIT_OK, err)
        collapsed = " ".join(out.split())
        self.assertIn("Read a problem.md first", collapsed)
        self.assertIn("solution.py beside it", collapsed)

    def test_a_single_question_names_the_exact_files(self):
        code, out, err = self.run_session(
            "start", "--mode", "interview", "--now", T0
        )
        self.assertEqual(code, EXIT_OK, err)
        collapsed = " ".join(out.split())
        self.assertIn("Read q1/problem.md first", collapsed)
        self.assertIn("q1/solution.py", collapsed)

    def test_a_gated_run_opens_the_level_it_revealed(self):
        code, out, err = self.run_session(
            "start", "--format", "ica", "--project", "parcel-locker", "--now", T0
        )
        self.assertEqual(code, EXIT_OK, err)
        self.assertIn("parcel-locker/level1.md", out)

    def test_the_file_open_would_focus_is_the_problem(self):
        self.run_session("start", "--format", "gca", "--questions", 2, "--now", T0)
        workspace = self.workspace()
        state = self.state()
        sys.path.insert(0, str(SCRIPT.parent))
        try:
            import session
            chosen = session.first_reading(workspace, state)
        finally:
            sys.path.pop(0)
        self.assertEqual(chosen.name, "problem.md")
        self.assertTrue(chosen.exists())


class TestTimer(SessionTestCase):
    """The countdown pane.

    The loop itself is not driven here: it runs until the clock does, so a test
    that entered it would hang. Everything that decides anything is a pure
    function, and `--once` renders a frame without looping, so the parts worth
    testing are reachable without waiting an hour.
    """

    def module(self):
        sys.path.insert(0, str(SCRIPT.parent))
        try:
            import session

            return session
        finally:
            sys.path.pop(0)

    def deadline(self):
        return self.state()["clock"]["deadline_epoch"]

    def test_urgency_thresholds(self):
        session = self.module()
        self.assertEqual(session.urgency(3600), "calm")
        self.assertEqual(session.urgency(601), "calm")
        self.assertEqual(session.urgency(600), "warning")
        self.assertEqual(session.urgency(121), "warning")
        self.assertEqual(session.urgency(120), "critical")
        self.assertEqual(session.urgency(1), "critical")
        self.assertEqual(session.urgency(0), "over")
        self.assertEqual(session.urgency(-5), "over")

    def test_a_milestone_fires_once(self):
        session = self.module()
        fired = set()
        first = session.due_milestones(600, fired)
        self.assertEqual([at for at, _ in first], [1800.0, 600.0])
        fired.update(at for at, _ in first)
        self.assertEqual(session.due_milestones(599, fired), [])

    def test_starting_late_does_not_replay_the_ones_already_passed(self):
        """Opening a pane with five minutes left must not fire thirty and ten."""
        session = self.module()
        remaining = 300.0
        fired = set(at for at, _ in session.MILESTONES if remaining <= at)
        self.assertEqual(session.due_milestones(remaining, fired), [])
        self.assertEqual(
            [at for at, _ in session.due_milestones(120, fired - {120.0})], [120.0]
        )

    def test_once_renders_the_clock_and_the_questions(self):
        self.run_session("start", "--format", "gca", "--questions", 2, "--now", T0)
        code, out, err = self.run_session(
            "timer", "--once", "--plain", "--now", self.deadline() - 900
        )
        self.assertEqual(code, EXIT_OK, err)
        self.assertIn("15:00", out)
        self.assertIn("q1", out)
        self.assertIn("q2", out)

    def test_once_says_time_is_up_and_exits_four(self):
        self.run_session("start", "--format", "gca", "--questions", 1, "--now", T0)
        code, out, _ = self.run_session(
            "timer", "--once", "--plain", "--now", self.deadline() + 10
        )
        self.assertEqual(code, EXIT_EXPIRED)
        self.assertIn("TIME IS UP", out)
        self.assertIn("Nothing more can be submitted", out)

    def test_plain_emits_no_escape_codes(self):
        """Piping it somewhere, or --plain, must not paint anything."""
        self.run_session("start", "--format", "gca", "--questions", 1, "--now", T0)
        _, out, _ = self.run_session(
            "timer", "--once", "--plain", "--now", self.deadline() - 60
        )
        self.assertNotIn("\033", out)

    def test_it_shows_a_result_once_something_is_submitted(self):
        workspace = self.start()
        (workspace / "q1" / "solution.py").write_text(
            "def solve(*a, **k):\n    return None\n"
        )
        self.run_session("submit", "--question", "q1", "--now", T0 + 60)
        _, out, _ = self.run_session(
            "timer", "--once", "--plain", "--now", self.deadline() - 60
        )
        self.assertNotIn("not submitted", out)

    def test_no_session_is_the_usual_exit_code(self):
        code, _, _ = self.run_session("timer", "--once")
        self.assertEqual(code, EXIT_NO_SESSION)

    def test_sampling_never_writes_back_over_a_submission(self):
        """The pane lives for an hour beside the grader.

        It writes the timeline as it goes, so it has to re-read under the lock
        rather than persist whatever it last read. Writing a copy taken before a
        submission landed would erase the submission.
        """
        session = self.module()
        workspace = self.start()
        (workspace / "q1" / "solution.py").write_text(
            "def solve(*a, **k):\n    return None\n"
        )
        self.run_session("submit", "--question", "q1", "--now", T0 + 60)
        before = self.state()["questions"][0]["result"]
        self.assertIsNotNone(before)

        # Stamped explicitly: a test writes both files inside the epsilon that
        # exists so copying a starter does not count as an edit.
        later = workspace / "q1" / "solution.py"
        later.write_text("# edited after submitting\n")
        os.utime(str(later), (T0 + 300, T0 + 300))
        session.sample_edits_locked(workspace)

        after = self.state()
        self.assertEqual(after["questions"][0]["result"], before)
        self.assertTrue(
            [event for event in after["events"] if event["type"] == "edited"],
            "the reading was not recorded at all",
        )


class TestDebrief(BankAwareTestCase):
    """Naming the hidden tests, but only once the clock is out.

    The gate is a timestamp and never a judgement, which is the same rule
    `submit` follows: a proctor that can be talked into it is not a proctor.
    """

    AFTER = T0 + 5000

    def hidden_names(self, index=0):
        return [
            line.split("def ")[1].split("(")[0]
            for line in (self.bank_dir(index) / "tests_hidden.py").read_text().splitlines()
            if line.strip().startswith("def test_")
        ]

    def test_refuses_while_the_clock_is_running(self):
        self.start()
        code, out, err = self.run_session("debrief", "--now", T0 + 60)
        self.assertEqual(code, EXIT_USAGE)
        self.assertIn("still running", out + err)

    def test_the_refusal_leaks_no_test_names(self):
        """The most dangerous moment for this command is the one where it says no."""
        workspace = self.start()
        (workspace / "q1" / "solution.py").write_text(
            "def solve(*a, **k):\n    return None\n"
        )
        _, out, err = self.run_session("debrief", "--now", T0 + 60)
        names = self.hidden_names()
        self.assertGreater(len(names), 10)
        for name in names:
            self.assertNotIn(name, out + err, "leaked %s" % (name,))

    def test_after_time_it_names_what_failed(self):
        workspace = self.start_with_mutants()
        self.install_partial_mutant(workspace)
        code, out, err = self.run_session("debrief", "--now", self.AFTER)
        self.assertEqual(code, EXIT_OK, err)
        self.assertIn("no longer hidden", out)
        # Something real was named, rather than a bare count.
        self.assertIn("  - ", out)

    def test_a_question_never_opened_is_not_a_list_of_failures(self):
        """Never reaching one is a triage result, not a knowledge one."""
        self.run_session("start", "--format", "gca", "--questions", 2, "--now", T0)
        code, out, err = self.run_session("debrief", "--now", self.AFTER)
        self.assertEqual(code, EXIT_OK, err)
        self.assertIn("never opened", out)

    def test_the_costliest_question_is_reported_first(self):
        code, _, err = self.run_session(
            "start", "--format", "gca", "--questions", 2, "--now", T0
        )
        self.assertEqual(code, EXIT_OK, err)
        workspace = self.workspace()
        for directory, at in (("q1", 300), ("q2", 600), ("q2", 3000)):
            path = workspace / directory / "solution.py"
            path.write_text(path.read_text() + "# work\n")
            os.utime(str(path), (T0 + at, T0 + at))
            self.run_session("status", "--now", T0 + at + 5)
        _, out, _ = self.run_session("debrief", "--now", self.AFTER, "--json")
        detail = json.loads(out)["detail"]
        self.assertEqual(detail[0]["dir"], "q2")
        self.assertGreater(detail[0]["seconds"], detail[1]["seconds"])

    def test_one_question_comes_with_a_reference(self):
        workspace = self.start_with_mutants()
        self.install_partial_mutant(workspace)
        _, out, err = self.run_session(
            "debrief", "--question", "q1", "--now", self.AFTER
        )
        self.assertIn("One way to write it", out)
        reference = (self.bank_dir() / "reference.py").read_text()
        anchor = [
            line.strip() for line in reference.splitlines()
            if line.strip().startswith("def ") or line.strip().startswith("class ")
        ]
        self.assertTrue(anchor)
        self.assertIn(anchor[0], out)

    def test_a_hopeless_answer_is_summarised_rather_than_dumped(self):
        """Failing everything should not print the suite back at somebody."""
        code, _, err = self.run_session(
            "start", "--format", "gca", "--questions", 1, "--now", T0
        )
        self.assertEqual(code, EXIT_OK, err)
        workspace = self.workspace()
        path = workspace / "q1" / "solution.py"
        path.write_text("def solve(*a, **k):\n    return None\n")
        # Stamped and then observed, or it reads as never opened: a write inside
        # the copy epsilon is deliberately not counted as an edit.
        os.utime(str(path), (T0 + 600, T0 + 600))
        self.run_session("status", "--now", T0 + 700)
        _, out, _ = self.run_session("debrief", "--now", self.AFTER)
        bullets = [line for line in out.splitlines() if line.startswith("  - ")]
        self.assertLessEqual(len(bullets), 8)
        self.assertIn("and", out)
        self.assertIn("more", out)

    def test_the_whole_debrief_does_not_ship_a_reference_by_default(self):
        """Four references at once is a wall nobody reads, and it makes the
        failing-test list harder to find than the answer."""
        workspace = self.start_with_mutants()
        self.install_partial_mutant(workspace)
        _, out, _ = self.run_session("debrief", "--now", self.AFTER)
        self.assertNotIn("One way to write it", out)


class TestNothingIsRemembered(SessionTestCase):
    """Research is not cached, so the commands that used to cache it are gone.

    They were removed because the second sitting for a company began by saying
    the search agreed with the last one, which is a claim about a hiring process
    nobody had checked, dressed up as continuity.
    """

    def test_recall_is_gone(self):
        code, _, err = self.run_session("recall", "shopify")
        self.assertEqual(code, EXIT_USAGE)
        self.assertIn("invalid choice", err)

    def test_learn_is_gone(self):
        code, _, err = self.run_session("learn", "shopify", "--source", "https://x")
        self.assertEqual(code, EXIT_USAGE)
        self.assertIn("invalid choice", err)

    def test_start_no_longer_takes_a_source(self):
        code, _, err = self.run_session(
            "start", "--format", "gca", "--questions", 1,
            "--company", "shopify", "--source", "https://x", "--now", T0,
        )
        self.assertEqual(code, EXIT_USAGE)

    def test_a_session_writes_no_research_log(self):
        self.run_session(
            "start", "--format", "gca", "--questions", 1,
            "--company", "shopify", "--now", T0,
        )
        self.assertEqual(list(self.root.rglob("researched.json")), [])


class TestTopicMatchIsStated(SessionTestCase):
    """Whether the question is on the subject you asked for, said out loud.

    Written after a session researched a company's practical frontend round,
    found nothing in the bank covering it, and dealt a heap problem anyway
    without a word. The topics were recorded as uncovered the whole time; the
    only thing missing was saying so where a person would see it.

    Deliberately three words and not a percentage. The signal is which topic
    tags overlap, and "68% match" would invent a precision the data has not got.
    """

    def start_with(self, *topics, **kwargs):
        args = ["start", "--format", "gca", "--mode", "interview",
                "--seed", kwargs.get("seed", 3), "--force", "--now", T0]
        for topic in topics:
            args += ["--topic", topic]
        code, out, err = self.run_session(*(args + ["--json"]))
        self.assertEqual(code, EXIT_OK, err)
        return json.loads(out)["briefing"]

    def test_nothing_asked_for_means_no_claim_made(self):
        self.assertIsNone(self.start_with()["match"])

    def test_a_subject_the_bank_does_not_have_is_off(self):
        briefing = self.start_with("react", "spreadsheet")
        self.assertEqual(briefing["match"], "off")
        self.assertEqual(sorted(briefing["topics"]["uncovered"]), ["react", "spreadsheet"])

    def test_some_of_it_is_partial(self):
        briefing = self.start_with("rate limiting", "react")
        self.assertEqual(briefing["match"], "partial")

    def test_all_of_it_is_on(self):
        self.assertEqual(self.start_with("rate limiting")["match"], "on")

    def test_a_written_question_states_its_provenance_without_any_flags(self):
        """The first live run of the write-the-question flow printed nothing.

        The agent wrote the question and started without --topic, so there were
        no asked topics to match against and the line vanished entirely, in the
        one case where the answer was most reassuring. Provenance comes from the
        question's own metadata now, so it does not depend on the caller having
        remembered a flag.
        """
        root = self.root / "gen"
        question = root / "written-one"
        question.mkdir(parents=True)
        (question / "meta.json").write_text(
            '{"id": "written-one", "title": "Written", '
            '"topics": ["formula parsing", "cycles"]}'
        )
        (question / "problem.md").write_text("# Written\n")
        (question / "starter.py").write_text("def solve(x):\n    raise NotImplementedError\n")
        (question / "reference.py").write_text("def solve(x):\n    return sorted(x)\n")
        tests = (
            "import unittest\n"
            "from solution import solve\n"
            "class T(unittest.TestCase):\n"
            "    def test_sorts(self):\n"
            "        self.assertEqual(solve([2, 1]), [1, 2])\n"
            "    def test_empty(self):\n"
            "        self.assertEqual(solve([]), [])\n"
        )
        (question / "tests_public.py").write_text(tests)
        (question / "tests_hidden.py").write_text(tests)
        mutants = question / "mutants"
        mutants.mkdir()
        (mutants / "unsorted.py").write_text("def solve(x):\n    return list(x)\n")
        (mutants / "reversed.py").write_text("def solve(x):\n    return sorted(x, reverse=True)\n")
        (mutants / "empty.py").write_text("def solve(x):\n    return []\n")

        code, out, err = self.run_session(
            "start", "--format", "gca", "--questions", "1",
            "--generated", str(root), "--now", T0,
        )
        self.assertEqual(code, EXIT_OK, err)
        self.assertIn("Written for this round", out)
        self.assertIn("formula parsing", out)
        self.assertIn("same grading gate", out)

    def test_the_candidate_is_told_on_screen(self):
        """The JSON already knew. Nobody reads the JSON."""
        args = ["start", "--format", "gca", "--mode", "interview", "--seed", 3,
                "--force", "--now", T0, "--topic", "react", "--topic", "spreadsheet"]
        code, out, err = self.run_session(*args)
        self.assertEqual(code, EXIT_OK, err)
        self.assertIn("Topic match: off", out)
        self.assertIn("react", out)

    def test_it_still_starts(self):
        """Never refuse. Saying so is the fix; blocking is not."""
        code, _, err = self.run_session(
            "start", "--format", "gca", "--mode", "interview", "--seed", 3,
            "--force", "--now", T0, "--topic", "nothing the bank has",
        )
        self.assertEqual(code, EXIT_OK, err)

    def test_the_report_says_it_again(self):
        """By the debrief, whether it was even the right subject matters as
        much as the score, and by then nobody remembers what was asked for."""
        self.run_session(
            "start", "--format", "gca", "--mode", "interview", "--seed", 3,
            "--force", "--now", T0, "--topic", "react",
        )
        _, out, _ = self.run_session("report", "--now", T0 + 99999)
        self.assertIn("Topic match: off", out)
        self.assertIn("not on the subject you asked to practise", " ".join(out.split()))

    def test_the_match_survives_in_the_session_record(self):
        self.run_session(
            "start", "--format", "gca", "--mode", "interview", "--seed", 3,
            "--force", "--now", T0, "--topic", "react",
        )
        self.assertEqual(self.state()["briefing"]["match"], "off")


class TestEndingOnPurpose(SessionTestCase):
    """Giving up is a legitimate ending, and it opens the debrief.

    Without a door to the abandoned state, somebody who stopped caring still
    had a live clock holding the debrief and its reference solution shut."""

    def test_end_stops_an_active_session_as_abandoned(self):
        self.start()
        code, out, _ = self.run_session("end", "--now", T0 + 600)
        self.assertEqual(code, EXIT_OK)
        self.assertIn("abandoned", out)
        clock = self.state()["clock"]
        self.assertEqual(clock["end_reason"], "abandoned")

    def test_end_twice_says_already_over(self):
        self.start()
        self.run_session("end", "--now", T0 + 600)
        code, out, _ = self.run_session("end", "--now", T0 + 700)
        self.assertEqual(code, EXIT_OK)
        self.assertIn("already over", out)

    def test_end_with_no_session_is_the_usual_exit(self):
        code, _, _ = self.run_session("end")
        self.assertEqual(code, EXIT_NO_SESSION)

    def test_no_submission_after_an_end(self):
        workspace = self.start()
        self.run_session("end", "--now", T0 + 600)
        (workspace / "q1" / "solution.py").write_text("def solve(x):\n    return x\n")
        code, _, err = self.run_session("submit", "--question", "q1", "--now", T0 + 700)
        self.assertEqual(code, EXIT_EXPIRED)

    def test_the_answer_is_reachable_after_giving_up(self):
        """The whole point: end, then debrief prints the reference, engine-gated."""
        self.start()
        code, out, err = self.run_session(
            "debrief", "--question", "q1", "--now", T0 + 60
        )
        self.assertEqual(code, EXIT_USAGE)  # clock running: still refused
        self.run_session("end", "--now", T0 + 600)
        code, out, err = self.run_session(
            "debrief", "--question", "q1", "--now", T0 + 700
        )
        self.assertEqual(code, EXIT_OK, err)
        self.assertIn("One way to write it", out)


class TestEveryCommandInEveryState(SessionTestCase):
    """No command, in any session state, may crash or invent an exit code.

    Written because three separate bugs this week were found by running the
    tool rather than by the suite, and one of them was of exactly this shape: a
    closed pane made `timer` print a BrokenPipeError traceback. Every existing
    test asserts a behaviour somebody thought to check. Nothing asserted the
    floor, which is that a command in an odd state fails like a program rather
    than like a stack trace.

    This cannot catch a bad-looking answer, only a broken one. The wall of
    twenty-six bullet points the debrief used to print would sail through here,
    because it was correct and merely useless. That half still needs a person.
    """

    # The contract SKILL.md branches on. Anything outside this set means the
    # agent has no documented way to react to whatever just happened.
    DOCUMENTED = {0, 2, 3, 4, 5, 6, 7, 8, 9}

    COMMANDS = (
        ("status", ()),
        ("report", ()),
        ("debrief", ()),
        ("timer", ("--once", "--plain")),
        ("list", ()),
        ("progress", ()),
        ("check", ()),
        ("submit", ("--question", "q1")),
        ("unlock", ()),
        ("hint", ("--note", "a nudge")),
        ("start", ("--format", "gca", "--questions", "1")),
    )

    def states(self):
        """Each situation a command can arrive in, as (name, extra setup)."""
        return (
            ("no session", self._nothing),
            ("active", self._active),
            ("active, one submitted", self._submitted),
            ("expired but unobserved", self._expired),
            ("ended, observed", self._ended),
            ("gated, levels locked", self._gated),
            ("interview mode", self._interview),
        )

    def _nothing(self):
        return T0 + 60

    def _active(self):
        self.run_session("start", "--format", "gca", "--questions", 1, "--now", T0)
        return T0 + 60

    def _submitted(self):
        self._active()
        workspace = self.workspace()
        (workspace / "q1" / "solution.py").write_text(
            "def solve(*a, **k):\n    return None\n"
        )
        self.run_session("submit", "--question", "q1", "--now", T0 + 90)
        return T0 + 120

    def _expired(self):
        self._active()
        # Past the deadline, but nothing has run since, so the ending has not
        # been written down yet. Every command has to cope with observing it.
        return T0 + 99999

    def _ended(self):
        self._active()
        self.run_session("status", "--now", T0 + 99999)
        return T0 + 99999

    def _gated(self):
        self.run_session(
            "start", "--format", "ica", "--project", "parcel-locker", "--now", T0
        )
        return T0 + 60

    def _interview(self):
        self.run_session("start", "--mode", "interview", "--now", T0)
        return T0 + 60

    def test_a_reader_that_walks_away_is_not_a_crash(self):
        """Closing the pane must not print a stack trace into the terminal.

        This is the one that actually happened. `timer` died with a
        BrokenPipeError the first time its output was piped into something that
        stopped reading, which is what closing a split does. Nothing in the
        suite could see it, because a test that captures output reads all of it,
        and a reader that never leaves is the one case that cannot reproduce it.
        """
        # A live session, on the real clock. `--now` is not honoured by the
        # loop (deliberately: SKILL.md forbids rewinding a running session), so
        # an injected deadline in the past would make timer print one frame and
        # exit before the reader ever went away, which is the whole condition.
        code, _, err = self.run_session("start", "--format", "gca", "--questions", 1)
        self.assertEqual(code, EXIT_OK, err)
        env = dict(os.environ)
        env["INTERVIEW_SIM_HOME"] = str(self.root)
        env.pop("INTERVIEW_SIM_NOW", None)
        env.pop("INTERVIEW_SIM_SESSION", None)

        for command, extra in (("timer", ["--plain"]), ("status", []), ("report", [])):
            reader = subprocess.Popen(["head", "-2"], stdin=subprocess.PIPE,
                                      stdout=subprocess.PIPE, universal_newlines=True)
            writer = subprocess.Popen(
                [sys.executable, str(SCRIPT), command] + extra,
                stdout=reader.stdin, stderr=subprocess.PIPE,
                env=env, cwd=str(REPO), universal_newlines=True,
            )
            reader.stdin.close()
            _, err = writer.communicate(timeout=60)
            reader.stdout.read()
            reader.wait(timeout=10)
            self.assertNotIn(
                "Traceback", err, "%s traced back when its reader closed" % (command,)
            )

    def test_nothing_crashes_and_no_exit_code_is_invented(self):
        problems = []
        for label, setup in self.states():
            for command, extra in self.COMMANDS:
                self.setUp()  # a fresh sessions root per combination
                now = setup()
                code, out, err = self.run_session(
                    command, *(list(extra) + ["--now", now])
                )
                where = "%s / %s" % (label, command)
                if "Traceback" in out + err:
                    problems.append("%s: traceback\n%s" % (where, (out + err)[-400:]))
                if code not in self.DOCUMENTED:
                    problems.append("%s: undocumented exit %d" % (where, code))
        self.assertEqual(problems, [], "\n\n".join(problems))


if __name__ == "__main__":
    unittest.main()
