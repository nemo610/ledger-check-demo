"""Synthetic end-to-end test: adapter -> dry-run worker -> local QA -> artifact hash.

No network, provider API, wallet, task claim, upload, signature, or payment is used.
"""
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from agent_economy.simulated_worker import run_dry_run
from agent_economy.task_adapter import normalize_candidate_for_dry_run
from data_qa_agent.artifact_server import ArtifactStore
from data_qa_agent.core import inspect_file


NOW = 2_000_000_000
AGENT = "agent-synthetic-e2e"
LISTING = "listing-synthetic-e2e"
CAPABILITIES = ["csv.inspect"]


class SyntheticAgentEndToEndTests(unittest.TestCase):
    def test_discovery_adapter_worker_report_and_artifact_integrity(self):
        spec_bytes = json.dumps(
            {"operation": "data_qa.inspect", "format": "csv"},
            separators=(",", ":"),
        ).encode("utf-8")
        spec_hash = hashlib.sha256(spec_bytes).hexdigest()
        candidate = {
            "task_id": "task-synthetic-e2e",
            "status": "open",
            "verified": True,
            "reward_gross_sol": "0.010000000",
            "deadline_unix": NOW + 600,
            "job_spec_hash": spec_hash,
            "required_capabilities": CAPABILITIES,
        }
        provider_record = {
            "task_id": "task-synthetic-e2e",
            "agent_id": AGENT,
            "listing_id": LISTING,
            "status": "open",
            "verified": True,
            "deadline_unix": NOW + 600,
            "reward_lamports": 10_000_000,
            "spec_sha256": spec_hash,
            "required_capabilities": CAPABILITIES,
        }

        envelope = normalize_candidate_for_dry_run(
            candidate,
            provider_record,
            expected_agent_id=AGENT,
            expected_listing_id=LISTING,
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source_path = root / "synthetic.csv"
            source_bytes = b"id,value\\n1,alpha\\n2,beta\\n"
            source_path.write_bytes(source_bytes)

            receipt = run_dry_run(
                envelope,
                spec_bytes,
                expected_agent_id=AGENT,
                expected_listing_id=LISTING,
                supported_capabilities=set(CAPABILITIES),
                processed_task_ids=set(),
                now_unix=NOW,
            )
            self.assertEqual(receipt["status"], "validated_not_executed")
            self.assertFalse(receipt["input_processed"])
            self.assertFalse(receipt["artifact_uploaded"])
            self.assertFalse(receipt["claim_made"])
            self.assertFalse(receipt["transaction_signed"])
            self.assertFalse(receipt["payment_made"])

            qa_report = inspect_file(source_path)
            self.assertEqual(qa_report["status"], "passed")
            artifact_payload = {
                "schema_version": "1.0",
                "source": {
                    "filename": source_path.name,
                    "size_bytes": len(source_bytes),
                    "sha256": hashlib.sha256(source_bytes).hexdigest(),
                },
                "report": qa_report,
                "simulation": receipt,
            }
            raw_artifact = (json.dumps(artifact_payload, sort_keys=True) + "\\n").encode("utf-8")
            store = ArtifactStore(root / "artifacts")
            created = store.put(raw_artifact)
            downloaded, downloaded_hash = store.get(created["artifact_id"])

            self.assertEqual(downloaded_hash, created["sha256"])
            self.assertEqual(downloaded_hash, hashlib.sha256(downloaded).hexdigest())
            parsed = json.loads(downloaded)
            self.assertEqual(parsed["source"]["sha256"], hashlib.sha256(source_bytes).hexdigest())
            self.assertEqual(parsed["report"]["status"], "passed")
            self.assertEqual(parsed["simulation"]["task_id"], "task-synthetic-e2e")
            self.assertFalse(parsed["simulation"]["payment_made"])


if __name__ == "__main__":
    unittest.main()
