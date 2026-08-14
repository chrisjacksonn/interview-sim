"""Tests for the repository guards in tools/.

Both of these exist because of a bug that shipped, and both are the kind of check
that can quietly stop working: if the detection breaks, everything goes green and
looks better than before. So the guards get tested on inputs that are known to be
bad, not only on the repository, which is currently clean by construction.
"""

import contextlib
import importlib.util
import io
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
TOOLS = REPO / "tools"


def load(name):
    """Import a tool by path. They are scripts, not an installed package."""
    spec = importlib.util.spec_from_file_location(name, TOOLS / (name + ".py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


check_symbols = load("check_symbols")
check_repo = load("check_repo")


def quietly(main):
    """Run a tool's main() without its report landing in the test output."""
    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        return main([])


class SymbolGuardTests(unittest.TestCase):
    def setUp(self):
        self.dir = Path(tempfile.mkdtemp(prefix="guard-test-"))
        self.addCleanup(shutil.rmtree, str(self.dir), True)

    def write(self, source):
        path = self.dir / "sample.py"
        path.write_text(source)
        return path

    def test_catches_a_function_defined_twice(self):
        path = self.write("def a():\n    pass\n\n\ndef a():\n    pass\n")
        found = check_symbols.duplicates(path)
        self.assertEqual([name for name, _ in found], ["a"])

    def test_catches_a_redefined_constant(self):
        path = self.write("LEVELS = (1,)\nother = 2\nLEVELS = (1, 2)\n")
        self.assertEqual([name for name, _ in check_symbols.duplicates(path)], ["LEVELS"])

    def test_methods_in_different_classes_are_fine(self):
        """Only module-level names shadow each other."""
        path = self.write(
            "class A:\n    def run(self):\n        pass\n\n\n"
            "class B:\n    def run(self):\n        pass\n"
        )
        self.assertEqual(check_symbols.duplicates(path), [])

    def test_a_conditional_fallback_is_fine(self):
        """The usual way to write an optional import must not trip it."""
        path = self.write(
            "try:\n    from fast import parse\nexcept ImportError:\n"
            "    def parse(text):\n        return text\n"
        )
        self.assertEqual(check_symbols.duplicates(path), [])

    def test_reports_every_line_the_name_was_bound_on(self):
        path = self.write("def a():\n    pass\n\n\ndef a():\n    pass\n")
        self.assertEqual(check_symbols.duplicates(path)[0][1], [1, 5])

    def test_the_repository_is_clean(self):
        self.assertEqual(quietly(check_symbols.main), 0)


class RepoGuardTests(unittest.TestCase):
    # Assembled at runtime rather than written out. This file is itself tracked
    # and therefore itself checked, so a literal home path here would fail the
    # guard, correctly. That is not a reason to give the guard an exemption
    # list: an exemption is a hole, and the fixture reads fine built from parts.
    LEAKED = "/".join(("", "Users", "chris", "interview-sim", "current"))
    LINUX = "/".join(("", "home", "dev", "interview-sim", "current"))

    def test_matches_the_path_that_actually_leaked(self):
        self.assertTrue(check_repo.HOME_PATH.search(self.LEAKED))

    def test_matches_a_linux_home(self):
        self.assertTrue(check_repo.HOME_PATH.search(self.LINUX))

    def test_catches_a_home_path_in_a_file(self):
        """End to end, not just the pattern: a tracked file carrying one fails."""
        directory = Path(tempfile.mkdtemp(prefix="guard-test-"))
        self.addCleanup(shutil.rmtree, str(directory), True)
        sample = directory / "sample.txt"
        sample.write_text("workspace = %s\n" % (self.LEAKED,))
        self.assertTrue(check_repo.HOME_PATH.search(sample.read_text()))

    def test_a_tilde_path_is_fine(self):
        """Documentation uses ~ deliberately. It is true on every machine."""
        self.assertIsNone(check_repo.HOME_PATH.search("~/interview-sim/scripts"))

    def test_a_bare_users_directory_is_not_a_home_path(self):
        self.assertIsNone(check_repo.HOME_PATH.search("see /Users for details"))

    def test_session_state_filenames_are_known(self):
        for name in ("history.json", "state.json"):
            self.assertIn(name, check_repo.SESSION_FILES)

    def test_the_repository_is_clean(self):
        self.assertEqual(quietly(check_repo.main), 0)


class StrangerTests(unittest.TestCase):
    """A clone, with none of this machine's state, must still work.

    The bug this comes from was invisible to every other job because they all run
    from a checkout that already had the leftover files in it.
    """

    @classmethod
    def setUpClass(cls):
        cls.dir = Path(tempfile.mkdtemp(prefix="stranger-test-"))
        cls.clone = cls.dir / "clone"
        result = subprocess.run(
            ["git", "clone", "--quiet", str(REPO), str(cls.clone)],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        )
        if result.returncode != 0:
            raise unittest.SkipTest("git clone unavailable: %s" % (result.stderr,))
        # Pin the exact commit rather than the clone's idea of a default branch,
        # because a pull request builds from a detached HEAD. The existence check
        # below is the important half: an empty working tree would pass every
        # assertion here by having nothing in it to fail.
        head = subprocess.check_output(
            ["git", "-C", str(REPO), "rev-parse", "HEAD"], universal_newlines=True
        ).strip()
        subprocess.check_call(
            ["git", "-C", str(cls.clone), "checkout", "--quiet", "--detach", head],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        )
        cls.script = cls.clone / "skills" / "sim" / "scripts" / "session.py"
        if not cls.script.exists():
            raise AssertionError("the clone has no working tree")

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(str(cls.dir), ignore_errors=True)

    def setUp(self):
        # A sessions directory per test. Sharing one made the first test to run
        # alphabetically leave a live session behind for the others, so the
        # "no history" check found history and failed for the wrong reason.
        self.home = self.dir / ("sessions-" + self.id().rsplit(".", 1)[-1])

    def run_in_clone(self, *args):
        import os
        env = dict(os.environ)
        env["INTERVIEW_SIM_HOME"] = str(self.home)
        env.pop("INTERVIEW_SIM_SESSION", None)
        env.pop("INTERVIEW_SIM_NOW", None)
        proc = subprocess.Popen(
            [sys.executable, str(self.script)] + [str(a) for a in args],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            env=env, cwd=str(self.clone), universal_newlines=True,
        )
        out, err = proc.communicate()
        return proc.returncode, out, err

    def test_the_clone_carries_no_session_state(self):
        for leftover in ("interview-sim-sessions", "sessions", ".sim"):
            self.assertFalse(
                (self.clone / leftover).exists(),
                "a fresh clone carries %s" % (leftover,),
            )

    def test_no_questions_are_pre_served(self):
        """The committed history.json made a first sitting draw around four
        questions it had never actually shown anyone."""
        self.assertFalse((self.clone / "interview-sim-sessions" / "history.json").exists())

    def test_reading_commands_do_not_fall_over_with_no_history(self):
        for command, expected in (("list", 0), ("progress", 0), ("status", 3), ("report", 3)):
            code, out, err = self.run_in_clone(command)
            self.assertNotIn("Traceback", out + err, "%s traced back" % (command,))
            self.assertEqual(code, expected, "%s exited %d: %s%s" % (command, code, out, err))

    def test_a_stranger_can_sit_a_session(self):
        code, out, err = self.run_in_clone("start", "--format", "gca")
        self.assertEqual(code, 0, err)
        workspace = Path((self.home / "current").read_text().strip())
        for slot in ("q1", "q2", "q3", "q4"):
            self.assertTrue(
                (workspace / slot / "solution.py").exists(),
                "a fresh clone could not build %s" % (slot,),
            )


if __name__ == "__main__":
    unittest.main()
