import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from data_qa_agent.artifacts import ArtifactError, create_report_artifact


class DataQAArtifactTests(unittest.TestCase):
    def test_creates_report_with_verifiable_hashes_without_input_contents(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "input.csv"
            destination = root / "out" / "report.json"
            source.write_text("id,value\n1,ok\n", encoding="utf-8")
            result = create_report_artifact(source, destination)
            payload = json.loads(destination.read_text(encoding="utf-8"))
            self.assertEqual(result["artifact_sha256"], hashlib.sha256(destination.read_bytes()).hexdigest())
            self.assertEqual(payload["source"]["sha256"], hashlib.sha256(source.read_bytes()).hexdigest())
            self.assertEqual(payload["report"]["status"], "passed")
            self.assertNotIn("1,ok", destination.read_text(encoding="utf-8"))
            self.assertEqual(result["status"], "passed")

    def test_rejects_oversized_input_before_inspection(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "large.csv"
            source.write_text("id\n12345\n", encoding="utf-8")
            with self.assertRaisesRegex(ArtifactError, "exceeds"):
                create_report_artifact(source, root / "report.json", max_input_bytes=2)

    def test_rejects_same_input_and_output_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "input.json"
            source.write_text('{"ok":true}', encoding="utf-8")
            with self.assertRaisesRegex(ArtifactError, "overwrite"):
                create_report_artifact(source, source)

    def test_rejects_non_json_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "input.json"
            source.write_text('{"ok":true}', encoding="utf-8")
            with self.assertRaisesRegex(ArtifactError, "extension"):
                create_report_artifact(source, Path(tmp) / "report.txt")


if __name__ == "__main__":
    unittest.main()
