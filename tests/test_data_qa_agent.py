import csv
import json
import tempfile
import unittest
from pathlib import Path

from data_qa_agent.core import inspect_file


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

    def test_csv_finds_duplicate_headers(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "headers.csv"
            path.write_text("id,id\n1,2\n", encoding="utf-8")
            report = inspect_file(path)
            self.assertIn("DUPLICATE_HEADERS", {f["code"] for f in report["findings"]})

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

    def test_rejects_unsupported_format(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "input.xlsx"
            path.write_text("dummy", encoding="utf-8")
            with self.assertRaises(ValueError):
                inspect_file(path)


if __name__ == "__main__":
    unittest.main()
