"""Onur Keskin: local project test verification, compatible with Python 3.9+."""

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET


def verify_project(project, timeout=300):
    """Run the project's tests using this interpreter; never infer cluster health."""
    root = Path(project).resolve()
    result = {
        "agent": "Onur Keskin",
        "protocol": 888,
        "project": str(root),
        "python": sys.executable,
        "status": "HOLD",
        "pytest_exit_code": None,
        "tests": 0,
        "passed": 0,
        "failed": 0,
        "skipped": 0,
        "reason": "",
        "output": "",
    }
    if not (root / "tests").is_dir():
        result["reason"] = "TESTS_DIRECTORY_MISSING"
        return result

    env = os.environ.copy()
    env.pop("PYTEST_ADDOPTS", None)
    env["PYTHONPATH"] = str(root)
    try:
        with tempfile.TemporaryDirectory(prefix="onur_888_") as temp:
            report = Path(temp) / "pytest.xml"
            command = [
                sys.executable, "-m", "pytest", "tests", "-q",
                "-o", "addopts=", "-o", "junit_family=xunit2",
                "--junitxml=" + str(report),
            ]
            completed = subprocess.run(
                command, cwd=str(root), env=env, stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT, text=True, encoding="utf-8",
                errors="replace", timeout=timeout, check=False,
            )
            result["pytest_exit_code"] = completed.returncode
            result["output"] = completed.stdout or ""
            if completed.returncode != 0:
                result["status"] = "FAIL"
                result["reason"] = "PYTEST_NONZERO_EXIT"
                return result

            cases = list(ET.parse(str(report)).getroot().iter("testcase"))
            result["tests"] = len(cases)
            result["failed"] = sum(
                any(child.tag in ("failure", "error") for child in case)
                for case in cases
            )
            result["skipped"] = sum(
                any(child.tag == "skipped" for child in case) for case in cases
            )
            result["passed"] = sum(
                not any(child.tag in ("failure", "error", "skipped") for child in case)
                for case in cases
            )
            if cases and result["passed"] == result["tests"]:
                result["status"] = "PASS"
                result["reason"] = "ALL_EXECUTED_TESTS_PASSED"
            else:
                result["reason"] = "EMPTY_OR_NOT_ALL_TESTS_PASSED"
    except subprocess.TimeoutExpired:
        result["reason"] = "TEST_TIMEOUT"
    except (OSError, ET.ParseError) as error:
        result["reason"] = "VERIFICATION_ERROR: " + str(error)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", default=str(Path(__file__).resolve().parents[1]))
    args = parser.parse_args()
    result = verify_project(args.project)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
