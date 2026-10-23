import hashlib
import os
import json
import tempfile
import time
import unittest
from unittest.mock import patch
from pathlib import Path

from data_qa_agent.artifact_server import ArtifactStore, ArtifactStoreError


def valid_report():
    return json.dumps({
        "schema_version": "1.0",
        "source": {"filename": "sample.csv", "size_bytes": 12, "sha256": "a" * 64},
        "report": {"status": "passed", "findings": []},
    }).encode("utf-8")


class ArtifactStoreTests(unittest.TestCase):
    def test_put_and_get_returns_server_computed_hash(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = ArtifactStore(tmp)
            created = store.put(valid_report())
            raw, digest = store.get(created["artifact_id"])
            self.assertEqual(digest, hashlib.sha256(raw).hexdigest())
            self.assertEqual(created["sha256"], digest)
            self.assertEqual(json.loads(raw)["schema_version"], "1.0")
            self.assertTrue(created["path"].startswith("/v1/artifacts/"))

    def test_failed_expiry_metadata_replace_leaves_no_partial_artifact(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = ArtifactStore(tmp)
            real_replace = os.replace
            calls = 0

            def fail_second_replace(source, destination):
                nonlocal calls
                calls += 1
                if calls == 2:
                    raise OSError("simulated metadata replace failure")
                return real_replace(source, destination)

            with patch(
                "data_qa_agent.artifact_server.os.replace",
                side_effect=fail_second_replace,
            ):
                with self.assertRaisesRegex(OSError, "metadata replace"):
                    store.put(valid_report())

            self.assertEqual(list(Path(tmp).iterdir()), [])

    def test_rejects_invalid_report_schema(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = ArtifactStore(tmp)
            with self.assertRaisesRegex(ArtifactStoreError, "schema"):
                store.put(b'{"schema_version":"1.0","source":{},"report":{}}')

    def test_rejects_oversized_and_empty_artifacts(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = ArtifactStore(tmp, max_bytes=128)
            with self.assertRaisesRegex(ArtifactStoreError, "empty or exceeds"):
                store.put(b"")
            with self.assertRaisesRegex(ArtifactStoreError, "empty or exceeds"):
                store.put(b"x" * 129)

    def test_expired_artifact_is_not_retrievable_and_cleanup_removes_it(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = ArtifactStore(tmp, ttl_seconds=1)
            created = store.put(valid_report())
            time.sleep(1.1)
            self.assertEqual(store.cleanup_expired(), 1)
            with self.assertRaisesRegex(ArtifactStoreError, "not found"):
                store.get(created["artifact_id"])

    def test_delete_removes_artifact_and_unknown_id_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = ArtifactStore(tmp)
            created = store.put(valid_report())
            store.delete(created["artifact_id"])
            with self.assertRaisesRegex(ArtifactStoreError, "not found"):
                store.get(created["artifact_id"])
            with self.assertRaisesRegex(ArtifactStoreError, "Invalid artifact ID"):
                store.get("../secret")


if __name__ == "__main__":
    unittest.main()
