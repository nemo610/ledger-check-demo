import base64
import hashlib
import unittest

from agent_economy.onchain_task_verifier import (
    JOB_SPEC_DISCRIMINATOR, OnChainVerificationError, PROGRAM_ID,
    TASK_DISCRIMINATOR, _b58decode, derive_task_job_spec_pda, derive_task_pda,
    parse_task_account, verify_task_on_chain,
)

NOW = 2_000_000_000
CREATOR = b"\x11" * 32
TASK_ID = b"\x00" * 32
SPEC = b'{"operation":"data_qa.inspect"}'
SPEC_HASH = hashlib.sha256(SPEC).hexdigest()
SPEC_URI = "https://example.org/spec.json"
PDA, TASK_BUMP = derive_task_pda(CREATOR, TASK_ID)
JOB_PDA, JOB_BUMP = derive_task_job_spec_pda(PDA)


def _u(value, size, signed=False):
    return int(value).to_bytes(size, "little", signed=signed)


def task_fixture(*, status=0, reward=1_000_000_000, deadline=NOW + 3600,
                 reward_mint=None, capabilities=0, depends_on=None, discriminator=None,
                 creator=CREATOR, task_id=TASK_ID, description=None, task_type=0,
                 max_workers=1, current_workers=0):
    b = bytearray(discriminator if discriminator is not None else TASK_DISCRIMINATOR)
    b.extend(task_id)
    b.extend(creator)
    b.extend(_u(capabilities, 8))
    b.extend(description if description is not None else b"\x00" * 64)
    b.extend(b"\x00" * 32)  # constraint hash
    b.extend(_u(reward, 8))
    b.extend(bytes([max_workers, current_workers, status, task_type]))
    b.extend(_u(NOW, 8, signed=True))
    b.extend(_u(deadline, 8, signed=True))
    b.extend(_u(0, 8, signed=True))
    b.extend(b"\x22" * 32)
    b.extend(b"\x00" * 64)
    b.extend(bytes([0, 1, TASK_BUMP]))
    b.extend(_u(500, 2))
    b.extend(b"\x00" if depends_on is None else b"\x01" + depends_on)
    b.extend(b"\x00")
    b.extend(_u(0, 2))
    b.extend(b"\x00" if reward_mint is None else b"\x01" + reward_mint)
    return bytes(b)


def job_spec_fixture(*, task=PDA, creator=CREATOR, job_hash=SPEC_HASH, uri=SPEC_URI,
                     discriminator=JOB_SPEC_DISCRIMINATOR):
    encoded_uri = uri.encode("utf-8")
    return (discriminator + _b58decode(task) + creator + bytes.fromhex(job_hash)
            + len(encoded_uri).to_bytes(4, "little") + encoded_uri)


def rpc_for(task_data=None, spec_data=None, *, task_owner=PROGRAM_ID, spec_owner=PROGRAM_ID):
    task_data = task_data or task_fixture()
    spec_data = spec_data or job_spec_fixture()
    def rpc(url, payload, *, timeout):
        address = payload["params"][0]
        if address == PDA:
            raw, owner = task_data, task_owner
        elif address == JOB_PDA:
            raw, owner = spec_data, spec_owner
        else:
            return {"result": {"value": None}}
        return {"result": {"value": {"owner": owner, "data": [base64.b64encode(raw).decode(), "base64"]}}}
    return rpc


def candidate(**overrides):
    value = {
        "task_id": PDA,
        "reward_gross_sol": "1.000000000",
        "deadline_unix": NOW + 3600,
        "job_spec_uri": SPEC_URI,
        "job_spec_hash": SPEC_HASH,
    }
    value.update(overrides)
    return value


class OnChainTaskVerifierTests(unittest.TestCase):
    def test_parses_open_sol_task(self):
        result = parse_task_account(task_fixture(), owner=PROGRAM_ID, now_unix=NOW)
        self.assertEqual(result["reward_lamports"], 1_000_000_000)
        self.assertEqual(result["status"], "open")
        self.assertFalse(result["canonical_pda_derivation_verified"])

    def test_handles_variable_depends_on_option_layout(self):
        result = parse_task_account(task_fixture(depends_on=b"\x33" * 32), owner=PROGRAM_ID, now_unix=NOW)
        self.assertEqual(result["reward_lamports"], 1_000_000_000)

    def test_rejects_spl_token_wrong_owner_and_discriminator(self):
        with self.assertRaisesRegex(OnChainVerificationError, "SPL token"):
            parse_task_account(task_fixture(reward_mint=b"\x44" * 32), owner=PROGRAM_ID, now_unix=NOW)
        with self.assertRaisesRegex(OnChainVerificationError, "owner"):
            parse_task_account(task_fixture(), owner="not-program", now_unix=NOW)
        with self.assertRaisesRegex(OnChainVerificationError, "discriminator"):
            parse_task_account(task_fixture(discriminator=b"\xff" * 8), owner=PROGRAM_ID, now_unix=NOW)

    def test_rejects_non_open_expired_zero_reward_and_unsupported_worker_mode(self):
        for data in (task_fixture(status=1), task_fixture(deadline=NOW), task_fixture(reward=0),
                     task_fixture(task_type=1), task_fixture(max_workers=2)):
            with self.subTest(data=data), self.assertRaises(OnChainVerificationError):
                parse_task_account(data, owner=PROGRAM_ID, now_unix=NOW)

    def test_rejects_truncated_invalid_option_and_unknown_capabilities(self):
        with self.assertRaisesRegex(OnChainVerificationError, "truncated"):
            parse_task_account(task_fixture()[:50], owner=PROGRAM_ID, now_unix=NOW)
        bad = bytearray(task_fixture())
        option_offset = 8 + 32 + 32 + 8 + 64 + 32 + 8 + 4 + 24 + 32 + 64 + 3 + 2
        bad[option_offset] = 2
        with self.assertRaisesRegex(OnChainVerificationError, "Option"):
            parse_task_account(bytes(bad), owner=PROGRAM_ID, now_unix=NOW)
        with self.assertRaisesRegex(OnChainVerificationError, "capability"):
            parse_task_account(task_fixture(capabilities=1), owner=PROGRAM_ID, now_unix=NOW)
        with self.assertRaisesRegex(OnChainVerificationError, "reserved"):
            parse_task_account(task_fixture(capabilities=1 << 10), owner=PROGRAM_ID, now_unix=NOW)

    def test_derives_canonical_task_and_job_spec_pdas(self):
        self.assertEqual(derive_task_pda(CREATOR, TASK_ID)[0], PDA)
        self.assertEqual(derive_task_job_spec_pda(PDA)[0], JOB_PDA)

    def test_verifies_canonical_task_pda_and_job_spec_binding(self):
        result = verify_task_on_chain(candidate(), rpc_url="https://rpc.example.org",
                                      now_unix=NOW, rpc_call=rpc_for())
        self.assertTrue(result["canonical_pda_derivation_verified"])
        self.assertTrue(result["task_id_pda_derivation_verified"])
        self.assertTrue(result["job_spec_hash_verified_on_chain"])
        self.assertEqual(result["task_job_spec_pda"], JOB_PDA)
        self.assertTrue(result["read_only"])
        self.assertEqual(result["claims_made"], 0)
        self.assertEqual(result["payments_made"], 0)

    def test_rejects_wrong_task_address_even_when_account_data_is_valid(self):
        with self.assertRaisesRegex(OnChainVerificationError, "canonical Task PDA"):
            verify_task_on_chain(candidate(task_id="1" * 32), rpc_url="https://rpc.example.org",
                                 now_unix=NOW, rpc_call=rpc_for())

    def test_rejects_job_spec_hash_uri_or_creator_mismatch(self):
        cases = [
            (job_spec_fixture(job_hash="ab" * 32), candidate(), "jobSpecHash"),
            (job_spec_fixture(uri="https://example.org/other.json"), candidate(), "jobSpecUri"),
            (job_spec_fixture(creator=b"\x33" * 32), candidate(), "creator"),
        ]
        for spec_data, cand, message in cases:
            with self.subTest(message=message), self.assertRaisesRegex(OnChainVerificationError, message):
                verify_task_on_chain(cand, rpc_url="https://rpc.example.org", now_unix=NOW,
                                     rpc_call=rpc_for(spec_data=spec_data))

    def test_rejects_mismatched_reward_or_deadline(self):
        with self.assertRaisesRegex(OnChainVerificationError, "reward"):
            verify_task_on_chain(candidate(reward_gross_sol="2.000000000"),
                                 rpc_url="https://rpc.example.org", now_unix=NOW, rpc_call=rpc_for())
        with self.assertRaisesRegex(OnChainVerificationError, "deadline"):
            verify_task_on_chain(candidate(deadline_unix=NOW + 99),
                                 rpc_url="https://rpc.example.org", now_unix=NOW, rpc_call=rpc_for())

    def test_rejects_insecure_rpc_url(self):
        with self.assertRaisesRegex(OnChainVerificationError, "HTTPS"):
            verify_task_on_chain(candidate(), rpc_url="http://rpc.example.org",
                                 now_unix=NOW, rpc_call=lambda *a, **k: {})


if __name__ == "__main__":
    unittest.main()
