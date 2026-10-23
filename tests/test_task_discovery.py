import unittest
from decimal import Decimal

from agent_economy.task_discovery import DiscoveryError, MAX_API_RESPONSE_BYTES, _fetch_json, _rank_task, discover_tasks


NOW = 2_000_000_000


def task(**overrides):
    value = {
        "pda": "task-1",
        "title": "Validate a small CSV",
        "status": "open",
        "verified": True,
        "rewardLamports": "1000000000",
        "deadlineUnix": NOW + 3600,
        "jobSpecUri": "https://example.org/spec.json",
        "jobSpecHash": "a" * 64,
        "rewardMint": None,
        "requiredCapabilities": "0",
        "minReputation": 0,
        "maxWorkers": 1,
        "currentWorkers": 0,
        "actionability": {"actionable": True},
    }
    value.update(overrides)
    return value


class TaskDiscoveryTests(unittest.TestCase):
    def test_ranks_verified_open_sol_task_and_does_not_assume_fee_split(self):
        result = _rank_task(task(), now_unix=NOW)
        self.assertIsNotNone(result)
        self.assertEqual(result["reward_gross_sol"], "1.000000000")
        self.assertEqual(result["gross_reward_upper_bound_sol"], "1.000000000")
        self.assertIn("not a net payout estimate", result["note"].lower())

    def test_rejects_unverified_task(self):
        self.assertIsNone(_rank_task(task(verified=False), now_unix=NOW))

    def test_only_official_zero_capability_bitmask_maps_to_empty_list(self):
        zero = _rank_task(task(requiredCapabilities="0"), now_unix=NOW)
        self.assertEqual(zero["required_capabilities"], [])
        # Nonzero bitmasks are kept opaque; the adapter must reject them until
        # each bit has a verified, implemented mapping.
        nonzero = _rank_task(task(requiredCapabilities="1"), now_unix=NOW)
        self.assertEqual(nonzero["required_capabilities"], "1")

    def test_rejects_missing_task_identity(self):
        self.assertIsNone(_rank_task(task(pda=""), now_unix=NOW))
        self.assertIsNone(_rank_task(task(pda=None), now_unix=NOW))

    def test_api_response_size_is_bounded(self):
        class FakeResponse:
            status = 200
            def __enter__(self):
                return self
            def __exit__(self, *args):
                return False
            def read(self, size=-1):
                self.asserted_size = size
                return b" " * (MAX_API_RESPONSE_BYTES + 1)
        response = FakeResponse()
        with self.assertRaisesRegex(DiscoveryError, "exceeds"):
            _fetch_json("https://api.agenc.ag/api/tasks", opener=lambda *a, **k: response)
        self.assertEqual(response.asserted_size, MAX_API_RESPONSE_BYTES + 1)

    def test_rejects_non_sol_reward(self):
        self.assertIsNone(_rank_task(task(rewardMint="some-token"), now_unix=NOW))

    def test_rejects_expired_or_zero_reward(self):
        self.assertIsNone(_rank_task(task(deadlineUnix=NOW - 1), now_unix=NOW))
        self.assertIsNone(_rank_task(task(rewardLamports="0"), now_unix=NOW))
        self.assertIsNone(_rank_task(task(rewardLamports="1.5"), now_unix=NOW))

    def test_unknown_denomination_is_retained_but_never_actionable(self):
        missing_mint = task()
        del missing_mint["rewardMint"]
        result = _rank_task(missing_mint, now_unix=NOW)
        self.assertIsNotNone(result)
        self.assertEqual(result["denomination"], "sol_unconfirmed")
        self.assertTrue(result["onchain_verification_required"])
        self.assertFalse(result["actionable"])
        self.assertIsNone(_rank_task(task(rewardMint="some-token"), now_unix=NOW))
        explicit_null = _rank_task(task(rewardMint=None), now_unix=NOW)
        self.assertEqual(explicit_null["denomination"], "sol_api_claimed")
        self.assertFalse(explicit_null["actionable"])

    def test_rejects_missing_https_spec_or_hash(self):
        self.assertIsNone(_rank_task(task(jobSpecUri="http://example.org/spec"), now_unix=NOW))
        self.assertIsNone(_rank_task(task(jobSpecHash=None), now_unix=NOW))
        self.assertIsNone(_rank_task(task(jobSpecHash="abc123"), now_unix=NOW))
        self.assertIsNone(_rank_task(task(jobSpecUri="https://user:pass@example.org/spec"), now_unix=NOW))
        self.assertIsNone(_rank_task(task(jobSpecUri="https://example.org/spec#fragment"), now_unix=NOW))

    def test_discovery_is_read_only_and_uses_documented_query(self):
        seen = {}
        def fake_fetch(url, *, timeout):
            seen["url"] = url
            return {"items": [task()], "total": 1}
        result = discover_tasks(now_unix=NOW, fetcher=fake_fetch)
        self.assertIn("/api/tasks?", seen["url"])
        self.assertIn("status=open", seen["url"])
        self.assertIn("pageSize=100", seen["url"])
        self.assertNotIn("actionable=", seen["url"])
        self.assertEqual(result["candidate_count"], 1)
        self.assertFalse(result["write_operations_enabled"])
        self.assertEqual(result["claims_made"], 0)
        self.assertEqual(result["payments_made"], 0)

    def test_equal_rewards_prioritize_nearest_deadline(self):
        later = task(pda="later", deadlineUnix=NOW + 7200)
        sooner = task(pda="sooner", deadlineUnix=NOW + 600)
        result = discover_tasks(
            now_unix=NOW,
            fetcher=lambda url, timeout: {"items": [later, sooner], "total": 2},
        )
        self.assertEqual([item["task_id"] for item in result["candidates"]], ["sooner", "later"])

    def test_unexpected_schema_fails_closed(self):
        with self.assertRaises(DiscoveryError):
            discover_tasks(now_unix=NOW, fetcher=lambda url, timeout: {"tasks": []})

    def test_invalid_page_size_rejected(self):
        with self.assertRaises(ValueError):
            discover_tasks(page_size=101, now_unix=NOW, fetcher=lambda *a, **k: {"items": []})


if __name__ == "__main__":
    unittest.main()
