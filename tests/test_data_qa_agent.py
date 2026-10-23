import csv
import json
import tempfile
import unittest
from pathlib import Path

from data_qa_agent.core import MAX_INPUT_BYTES, inspect_file


class DataQAAgentTests(unittest.TestCase):
    def test_csv_clean_file_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "clean.csv"
            path.write_text("id,value\n1,ok\n2,fine\n", encoding="utf-8")
            report = inspect_file(path)
            self.assertEqual(report["status"], "passed")
            self.assertEqual(report["rows"], 2)
            self.assertEqual(report["columns"], 2)

    def test_csv_finds_duplicate_rows_and_width_mismatch(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "issues.csv"
            path.write_text("id,value\n1,x\n1,x\n2\n", encoding="utf-8")
            report = inspect_file(path)
            codes = {item["code"] for item in report["findings"]}
            self.assertEqual(report["status"], "needs_review")
            self.assertIn("EXACT_DUPLICATE_ROWS", codes)
            self.assertIn("ROW_WIDTH_MISMATCH", codes)

    def test_csv_finds_duplicate_headers_without_echoing_names(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "headers.csv"
            path.write_text("customer_secret,customer_secret\n1,2\n", encoding="utf-8")
            report = inspect_file(path)
            self.assertIn("DUPLICATE_HEADERS", {f["code"] for f in report["findings"]})
            self.assertNotIn("customer_secret", json.dumps(report))

    def test_csv_blank_headers_and_rows_are_reported(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "blank.csv"
            path.write_text(",value\n\n1,ok\n", encoding="utf-8")
            report = inspect_file(path)
            codes = {item["code"] for item in report["findings"]}
            self.assertIn("BLANK_HEADERS", codes)
            self.assertIn("BLANK_ROWS", codes)

    def test_json_valid_object_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "input.json"
            path.write_text(json.dumps({"ok": True}), encoding="utf-8")
            report = inspect_file(path)
            self.assertEqual(report["status"], "passed")
            self.assertEqual(report["root_type"], "object")

    def test_invalid_json_is_error_without_echoing_content(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bad.json"
            path.write_text('{"secret":"do-not-echo",}', encoding="utf-8")
            report = inspect_file(path)
            self.assertEqual(report["status"], "error")
            self.assertNotIn("do-not-echo", json.dumps(report))

    def test_oversized_csv_is_rejected_before_parsing(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "large.csv"
            path.write_bytes(b"x" * (MAX_INPUT_BYTES + 1))
            report = inspect_file(path)
            self.assertEqual(report["status"], "error")
            self.assertEqual(report["findings"][0]["code"], "INPUT_TOO_LARGE")

    def test_oversized_json_is_rejected_before_parsing(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "large.json"
            path.write_bytes(b" " * (MAX_INPUT_BYTES + 1))
            report = inspect_file(path)
            self.assertEqual(report["status"], "error")
            self.assertEqual(report["findings"][0]["code"], "INPUT_TOO_LARGE")

    def test_unreadable_or_missing_file_returns_safe_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            report = inspect_file(Path(tmp) / "missing.csv")
            self.assertEqual(report["status"], "error")
            self.assertNotIn("secret", json.dumps(report))

    def test_rejects_unsupported_format(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "input.xlsx"
            path.write_text("dummy", encoding="utf-8")
            with self.assertRaises(ValueError):
                inspect_file(path)


if __name__ == "__main__":
    unittest.main()
