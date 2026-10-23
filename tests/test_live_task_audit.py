import hashlib
import unittest
from unittest.mock import patch

from agent_economy.live_task_audit import (
    SpecVerificationError,
    audit_snapshot,
    fetch_spec_bytes,
)

NOW = 2_000_000_000
SPEC = b'{"operation":"data_qa.inspect"}'
HASH = hashlib.sha256(SPEC).hexdigest()


def snapshot():
    return {
        "candidates": [{
            "task_id": "11111111111111111111111111111111",
            "title": "Inspect CSV",
            "reward_gross_sol": "0.100000000",
            "deadline_unix": NOW + 600,
            "denomination": "sol_unconfirmed",
            "job_spec_uri": "https://example.org/spec.json",
            "job_spec_hash": HASH,
        }]
    }


class LiveTaskAuditTests(unittest.TestCase):
    def test_without_rpc_stays_unverified_and_non_actionable(self):
        result = audit_snapshot(snapshot(), rpc_url=None, now_unix=NOW)
        item = result["audited_candidates"][0]
        self.assertEqual(item["status"], "unverified")
        self.assertFalse(item["actionable"])
        self.assertEqual(result["claims_made"], 0)
        self.assertFalse(result["live_execution_enabled"])

    def test_rpc_and_spec_hash_success_is_still_not_actionable(self):
        account = {
            "read_only": True,
            "reward_lamports": 100_000_000,
            "deadline_unix": NOW + 600,
            "canonical_pda_derivation_verified": False,
            "job_spec_hash_verified_on_chain": False,
        }
        with patch("agent_economy.live_task_audit.verify_task_on_chain", return_value=account):
            result = audit_snapshot(
                snapshot(), rpc_url="https://rpc.example.org", now_unix=NOW,
                spec_fetcher=lambda uri: SPEC,
            )
        item = result["audited_candidates"][0]
        self.assertEqual(item["status"], "partial_verified_not_actionable")
        self.assertTrue(item["spec_sha256_matches"])
        self.assertFalse(item["canonical_pda_verified"])
        self.assertFalse(item["actionable"])
        self.assertEqual(item["transactions_signed"], 0)

    def test_spec_hash_mismatch_rejects_candidate(self):
        account = {"read_only": True, "reward_lamports": 100_000_000, "deadline_unix": NOW + 600}
        with patch("agent_economy.live_task_audit.verify_task_on_chain", return_value=account):
            result = audit_snapshot(
                snapshot(), rpc_url="https://rpc.example.org", now_unix=NOW,
                spec_fetcher=lambda uri: b'{"operation":"different"}',
            )
        item = result["audited_candidates"][0]
        self.assertEqual(item["status"], "rejected")
        self.assertFalse(item["spec_sha256_matches"])

    def test_onchain_failure_rejects_without_fetching_spec(self):
        from agent_economy.onchain_task_verifier import OnChainVerificationError
        with patch(
            "agent_economy.live_task_audit.verify_task_on_chain",
            side_effect=OnChainVerificationError("bad account"),
        ):
            result = audit_snapshot(
                snapshot(), rpc_url="https://rpc.example.org", now_unix=NOW,
                spec_fetcher=lambda uri: self.fail("must not fetch spec after RPC failure"),
            )
        self.assertEqual(result["audited_candidates"][0]["status"], "rejected")

    def test_spec_url_blocks_http_credentials_fragment_and_private_ip(self):
        for uri in (
            "http://example.org/spec",
            "https://user:pass@example.org/spec",
            "https://example.org/spec#frag",
            "https://127.0.0.1/spec",
        ):
            with self.subTest(uri=uri), self.assertRaises(SpecVerificationError):
                fetch_spec_bytes(uri)

    def test_spec_body_limit(self):
        class Response:
            status = 200
            def __enter__(self):
                return self
            def __exit__(self, *args):
                return False
            def read(self, size):
                self.asserted_size = size
                return b"x" * (256 * 1024 + 1)
        response = Response()
        with self.assertRaisesRegex(SpecVerificationError, "256 KiB"):
            fetch_spec_bytes("https://example.org/spec", opener=lambda *a, **k: response)
        self.assertEqual(response.asserted_size, 256 * 1024 + 1)


if __name__ == "__main__":
    unittest.main()
