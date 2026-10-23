import csv
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "validate_files.py"


class ValidatorTests(unittest.TestCase):
    def run_validator(self, root, fail_empty="false"):
        env = os.environ.copy()
        env["INPUT_PATH"] = str(root)
        env["FAIL_ON_EMPTY_CSV"] = fail_empty
        return subprocess.run(
            [sys.executable, str(SCRIPT)],
            env=env,
            text=True,
            capture_output=True,
            check=False,
        )

    def test_valid_csv_and_json(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "ok.csv").write_text("a,b\n1,2\n", encoding="utf-8")
            (root / "ok.json").write_text('{"ok": true}', encoding="utf-8")
            result = self.run_validator(root)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("2 file(s), 0 failure(s)", result.stdout)

    def test_csv_wrong_row_width_fails(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "bad.csv").write_text("a,b\n1\n", encoding="utf-8")
            result = self.run_validator(root)
            self.assertEqual(result.returncode, 1)
            self.assertIn("expected 2", result.stdout)

    def test_duplicate_header_fails(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "bad.csv").write_text("a,a\n1,2\n", encoding="utf-8")
            result = self.run_validator(root)
            self.assertEqual(result.returncode, 1)
            self.assertIn("duplicate column", result.stdout)

    def test_invalid_json_fails(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "bad.json").write_text('{"x": }', encoding="utf-8")
            result = self.run_validator(root)
            self.assertEqual(result.returncode, 1)

    def test_empty_csv_can_be_rejected_by_option(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "empty.csv").write_text("a,b\n", encoding="utf-8")
            result = self.run_validator(root, "true")
            self.assertEqual(result.returncode, 1)
            self.assertIn("no data rows", result.stdout)

    def test_missing_path_fails(self):
        with tempfile.TemporaryDirectory() as temp:
            missing = Path(temp) / "missing"
            result = self.run_validator(missing)
            self.assertEqual(result.returncode, 2)
            self.assertIn("does not exist", result.stdout)


if __name__ == "__main__":
    unittest.main()
