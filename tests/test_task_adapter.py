import unittest

from agent_economy.simulated_worker import JobRejected
from agent_economy.task_adapter import normalize_candidate_for_dry_run


AGENT = "agent-synthetic"
LISTING = "listing-synthetic"
NOW = 2_000_000_000
SPEC_HASH = "a" * 64


def candidate(**overrides):
    value = {
        "task_id": "task-synthetic",
        "status": "open",
        "verified": True,
        "reward_gross_sol": "0.250000000",
        "deadline_unix": NOW + 600,
        "job_spec_hash": SPEC_HASH,
        "required_capabilities": ["csv.inspect"],
    }
    value.update(overrides)
    return value


def provider_record(**overrides):
    value = {
        "task_id": "task-synthetic",
        "agent_id": AGENT,
        "listing_id": LISTING,
        "status": "open",
        "verified": True,
        "deadline_unix": NOW + 600,
        "reward_lamports": 250_000_000,
        "spec_sha256": SPEC_HASH,
        "required_capabilities": ["csv.inspect"],
    }
    value.update(overrides)
    return value


class TaskAdapterTests(unittest.TestCase):
    def adapt(self, c=None, p=None):
        return normalize_candidate_for_dry_run(
            c or candidate(), p or provider_record(),
            expected_agent_id=AGENT, expected_listing_id=LISTING,
        )

    def test_normalizes_matching_explicit_record(self):
        result = self.adapt()
        self.assertEqual(result["task_id"], "task-synthetic")
        self.assertEqual(result["reward_lamports"], 250_000_000)
        self.assertEqual(result["required_capabilities"], ["csv.inspect"])
        self.assertEqual(result["agent_id"], AGENT)
        self.assertEqual(result["listing_id"], LISTING)

    def test_rejects_raw_bitmask_at_normalized_adapter_boundary(self):
        with self.assertRaisesRegex(JobRejected, "capabilities"):
            self.adapt(candidate(required_capabilities="0"))

    def test_rejects_attribution_mismatch(self):
        with self.assertRaisesRegex(JobRejected, "attributed"):
            self.adapt(p=provider_record(agent_id="different-agent"))
        with self.assertRaisesRegex(JobRejected, "attributed"):
            self.adapt(p=provider_record(listing_id="different-listing"))

    def test_rejects_candidate_provider_mismatch(self):
        with self.assertRaisesRegex(JobRejected, "deadline"):
            self.adapt(c=candidate(deadline_unix=NOW + 900))
        with self.assertRaisesRegex(JobRejected, "reward"):
            self.adapt(c=candidate(reward_gross_sol="0.250000001"))
        with self.assertRaisesRegex(JobRejected, "spec hash"):
            self.adapt(c=candidate(job_spec_hash="b" * 64))

    def test_rejects_malformed_capability_or_reward(self):
        with self.assertRaisesRegex(JobRejected, "explicit list"):
            self.adapt(p=provider_record(required_capabilities="0"))
        with self.assertRaisesRegex(JobRejected, "positive integer"):
            self.adapt(p=provider_record(reward_lamports=True))

    def test_rejects_non_hex_hash_and_invalid_configured_ids(self):
        with self.assertRaisesRegex(JobRejected, "SHA-256 hex"):
            self.adapt(p=provider_record(spec_sha256="g" * 64))
        with self.assertRaisesRegex(JobRejected, "non-empty strings"):
            normalize_candidate_for_dry_run(
                candidate(), provider_record(),
                expected_agent_id=123, expected_listing_id=LISTING,
            )
        with self.assertRaisesRegex(JobRejected, "non-empty strings"):
            normalize_candidate_for_dry_run(
                candidate(), provider_record(),
                expected_agent_id=AGENT, expected_listing_id=" ",
            )


if __name__ == "__main__":
    unittest.main()
