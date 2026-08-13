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


class TestResearchLog(BankAwareTestCase):
    """The dated note a search leaves behind.

    It is a log and never an answer. The guarantee that matters is the last
    test here: starting a session does not read it, so nothing recorded months
    ago can quietly shape a sitting today.
    """

    def learn(self, *extra):
        args = [
            "learn", "shopify", "--confidence", "low",
            "--source", "https://example.com/thread",
        ]
        return self.run_session(*(args + list(extra)))

    def test_a_claim_without_a_source_is_refused(self):
        code, _, err = self.run_session("learn", "shopify", "--confidence", "low")
        self.assertEqual(code, EXIT_USAGE)
        self.assertIn("source", err)

    def test_a_source_that_is_not_a_link_is_refused(self):
        code, _, err = self.run_session(
            "learn", "shopify", "--confidence", "low", "--source", "someone told me"
        )
        self.assertEqual(code, EXIT_USAGE)
        self.assertIn("Not a link", err)

    def test_what_was_found_can_be_recalled(self):
        code, _, err = self.learn("--round", "pairing", "--minutes", "45")
        self.assertEqual(code, EXIT_OK, err)
        code, out, _ = self.run_session("recall", "shopify")
        self.assertEqual(code, EXIT_OK)
        flat = " ".join(out.split())
        self.assertIn("pairing", flat)
        self.assertIn("https://example.com/thread", flat)

    def test_recall_says_it_is_not_current(self):
        self.learn()
        _, out, _ = self.run_session("recall", "shopify")
        flat = " ".join(out.split())
        self.assertIn("not current", flat)
        self.assertIn("Look it up again", flat)

    def test_recalling_something_never_researched(self):
        code, out, _ = self.run_session("recall", "nintendo")
        self.assertEqual(code, EXIT_OK)
        self.assertIn("Nothing recorded", out)

    def test_a_second_round_adds_rather_than_replaces(self):
        self.learn("--round", "oa", "--format", "gca")
        self.learn("--round", "pairing", "--mode", "interview")
        _, out, _ = self.run_session("recall", "shopify", "--json")
        rounds = json.loads(out)["rounds"]
        self.assertEqual([item["name"] for item in rounds], ["oa", "pairing"])

    def test_the_file_is_valid_json_with_its_sources(self):
        self.learn()
        with open(str(self.root / "researched.json")) as handle:
            payload = json.load(handle)
        entry = payload["presets"]["shopify"]
        self.assertEqual(entry["sources"], ["https://example.com/thread"])
        self.assertRegex(entry["last_confirmed"], r"^\d{4}-\d{2}-\d{2}$")

    def test_a_session_records_what_it_actually_ran(self):
        """One command, and the note cannot describe a sitting nobody had."""
        code, _, err = self.run_session(
            "start", "--company", "shopify", "--round", "pairing",
            "--format", "gca", "--mode", "interview", "--minutes", "45",
            "--topic", "rate limiting", "--confidence", "medium",
            "--source", "https://example.com/blind", "--now", T0,
        )
        self.assertEqual(code, EXIT_OK, err)
        _, out, _ = self.run_session("recall", "shopify", "--json")
        entry = json.loads(out)
        self.assertEqual(entry["sources"], ["https://example.com/blind"])
        self.assertEqual(entry["confidence"], "medium")
        recorded = entry["rounds"][0]
        self.assertEqual(recorded["name"], "pairing")
        self.assertEqual(recorded["mode"], "interview")
        self.assertEqual(recorded["minutes"], 45)
        self.assertEqual(recorded["topics"], ["rate limiting"])

    def test_a_session_without_sources_records_nothing(self):
        self.run_session(
            "start", "--company", "shopify", "--format", "gca", "--now", T0
        )
        _, out, _ = self.run_session("recall", "shopify", "--json")
        self.assertFalse(json.loads(out)["found"])

    def test_a_source_with_nobody_to_attach_it_to_is_refused(self):
        code, _, err = self.run_session(
            "start", "--format", "gca", "--source", "https://example.com/x", "--now", T0
        )
        self.assertEqual(code, EXIT_USAGE)
        self.assertIn("--company", err)

    def test_starting_a_session_does_not_consult_it(self):
        """The whole point of the design. A note is not a source of truth.

        Something recorded months ago must not shape a sitting today, so the
        shape comes from the flags the caller passes after looking it up, and
        the log is never read on the way past.
        """
        self.learn("--round", "pairing", "--mode", "interview", "--minutes", "45",
                   "--format", "gca", "--topic", "graphs")
        code, out, err = self.run_session(
            "start", "--company", "shopify", "--format", "gca", "--now", T0, "--json"
        )
        self.assertEqual(code, EXIT_OK, err)
        payload = json.loads(out)
        state = self.state()
        # None of the recorded shape leaked in: not the mode, not the minutes,
        # not the topics.
        self.assertEqual(state["mode"], "exam")
        self.assertEqual(state["clock"]["duration_seconds"], 70 * 60)
        self.assertEqual(len(state["questions"]), 4)
        self.assertEqual(payload["briefing"]["topics"]["asked"], [])


class TestStaleness(BankAwareTestCase):
    """A note has a date on it, and the date has to mean something."""

    YEAR = 400 * 24 * 3600

    def learn(self, now=T0):
        code, _, err = self.run_session(
            "learn", "shopify", "--round", "oa", "--format", "gca",
            "--confidence", "medium", "--source", "https://example.com/a",
            "--now", now,
        )
        self.assertEqual(code, EXIT_OK, err)

    def test_recall_reports_the_age(self):
        self.learn()
        _, out, _ = self.run_session("recall", "shopify", "--now", T0 + self.YEAR, "--json")
        self.assertGreater(json.loads(out)["age_days"], 365)

    def test_a_year_old_note_says_so_in_words(self):
        self.learn()
        _, out, _ = self.run_session("recall", "shopify", "--now", T0 + self.YEAR)
        self.assertIn("days ago", " ".join(out.split()))

    def test_learning_again_restamps_it_and_keeps_both_sources(self):
        self.learn()
        self.run_session(
            "learn", "shopify", "--round", "oa", "--format", "gca",
            "--confidence", "medium", "--source", "https://example.com/b",
            "--now", T0 + self.YEAR,
        )
        _, out, _ = self.run_session("recall", "shopify", "--now", T0 + self.YEAR + 60, "--json")
        entry = json.loads(out)
        self.assertEqual(entry["age_days"], 0)
        self.assertEqual(
            entry["sources"], ["https://example.com/a", "https://example.com/b"]
        )

    def test_an_undated_note_reports_no_age_rather_than_zero(self):
        self.learn()
        path = self.root / "researched.json"
        payload = json.loads(path.read_text())
        del payload["presets"]["shopify"]["last_confirmed"]
        path.write_text(json.dumps(payload))
        _, out, _ = self.run_session("recall", "shopify", "--now", T0 + 60, "--json")
        self.assertIsNone(json.loads(out)["age_days"])


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

    def test_a_topic_the_bank_cannot_cover_is_reported_to_the_proctor(self):
        """And to nobody else.

        A candidate hearing "we had nothing on this so here is something else"
        loses confidence in the sitting, and cannot act on it either. The
        proctor can: an uncovered topic is the cue to write a question for it.
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
        self.assertNotIn("bank", human.lower())
        self.assertNotIn("quantum", human.lower())

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
    """Questions written on the spot rather than taken from the bank.

    They skip the mutation gate by design. They do not skip the two checks that
    decide whether an hour is worth spending, and those run before the clock
    starts because that is the only moment they are free.
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

    def write_question(self, root, reference=None, starter=None):
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


if __name__ == "__main__":
    unittest.main()
