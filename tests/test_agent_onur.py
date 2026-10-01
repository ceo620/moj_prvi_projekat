"""Pytest-compatible tests; also runnable with standard-library unittest."""

from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from src.agent_onur import main, verify_project


class TestOnurAgent(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "tests").mkdir()

    def simulate(self, xml, returncode=0):
        def run(command, **kwargs):
            self.assertEqual(command[:4], [sys.executable, "-m", "pytest", "tests"])
            self.assertEqual(kwargs["cwd"], str(self.root.resolve()))
            self.assertEqual(kwargs["env"]["PYTHONPATH"], str(self.root.resolve()))
            self.assertNotIn("PYTEST_ADDOPTS", kwargs["env"])
            report = next(arg.split("=", 1)[1] for arg in command if arg.startswith("--junitxml="))
            if xml is not None:
                Path(report).write_text(xml, encoding="utf-8")
            return subprocess.CompletedProcess(command, returncode, "pytest diagnostic output")
        with patch("src.agent_onur.subprocess.run", side_effect=run):
            return verify_project(self.root)

    def test_pass_uses_current_interpreter_and_counts_tests(self):
        with patch.dict("os.environ", {"PYTEST_ADDOPTS": "-k unrelated"}):
            result = self.simulate("<testsuites><testsuite><testcase/><testcase/></testsuite></testsuites>")
        self.assertEqual(result["status"], "PASS")
        self.assertEqual((result["tests"], result["passed"]), (2, 2))
        self.assertEqual(result["agent"], "Onur Keskin")

    def test_nonzero_exit_blocks_even_with_passing_report(self):
        result = self.simulate("<testsuite><testcase/></testsuite>", returncode=1)
        self.assertEqual(result["status"], "FAIL")
        self.assertEqual(result["pytest_exit_code"], 1)
        self.assertEqual(result["output"], "pytest diagnostic output")

    def test_missing_tests_does_not_launch_process(self):
        with patch("src.agent_onur.subprocess.run") as run:
            result = verify_project(self.root / "missing")
        run.assert_not_called()
        self.assertEqual(result["reason"], "TESTS_DIRECTORY_MISSING")

    def test_no_test_cases_blocks_success(self):
        self.assertEqual(self.simulate("<testsuite/>")["status"], "HOLD")

    def test_skipped_or_failed_cases_block_success(self):
        for tag in ("skipped", "failure", "error"):
            with self.subTest(tag=tag):
                result = self.simulate("<testsuite><testcase><" + tag + "/></testcase></testsuite>")
                self.assertEqual(result["status"], "HOLD")
                self.assertEqual(result["passed"], 0)

    def test_missing_or_malformed_report_blocks_success(self):
        for xml in (None, "<broken"):
            with self.subTest(xml=xml):
                self.assertEqual(self.simulate(xml)["status"], "HOLD")

    def test_timeout_blocks_success(self):
        with patch("src.agent_onur.subprocess.run", side_effect=subprocess.TimeoutExpired("pytest", 300)):
            result = verify_project(self.root)
        self.assertEqual(result["status"], "HOLD")
        self.assertEqual(result["reason"], "TEST_TIMEOUT")

    def test_process_error_blocks_success(self):
        with patch("src.agent_onur.subprocess.run", side_effect=OSError("cannot launch")):
            result = verify_project(self.root)
        self.assertEqual(result["status"], "HOLD")

    def test_cli_exit_code_reflects_verification(self):
        for status, expected in (("PASS", 0), ("FAIL", 1), ("HOLD", 1)):
            with self.subTest(status=status):
                with patch.object(sys, "argv", ["agent_onur"]), patch("src.agent_onur.verify_project", return_value={"status": status}), patch("builtins.print"):
                    self.assertEqual(main(), expected)


if __name__ == "__main__":
    unittest.main()
