import base64
import unittest

from agent_economy.onchain_task_verifier import (
    OnChainVerificationError, PROGRAM_ID, TASK_DISCRIMINATOR,
    parse_task_account, verify_task_on_chain,
)

# A 32-byte base58 string representing 32 zero bytes is a valid synthetic task id.
PDA = "1" * 32
NOW = 2_000_000_000


def _u(value, size, signed=False):
    return int(value).to_bytes(size, "little", signed=signed)


def fixture(*, status=0, reward=1_000_000_000, deadline=NOW + 3600,
            reward_mint=None, capabilities=0, depends_on=None, discriminator=None,
            task_id=None):
    b = bytearray(discriminator if discriminator is not None else TASK_DISCRIMINATOR)
    b.extend(task_id if task_id is not None else b"\x00" * 32)
    b.extend(b"\x11" * 32)  # creator
    b.extend(_u(capabilities, 8))
    b.extend(b"\x00" * 64)  # description
    b.extend(b"\x00" * 32)  # constraint hash
    b.extend(_u(reward, 8))
    b.extend(bytes([1, 0, status, 0]))
    b.extend(_u(NOW, 8, signed=True))
    b.extend(_u(deadline, 8, signed=True))
    b.extend(_u(0, 8, signed=True))
    b.extend(b"\x22" * 32)  # escrow
    b.extend(b"\x00" * 64)  # result
    b.extend(bytes([0, 1, 1]))
    b.extend(_u(500, 2))
    if depends_on is None:
        b.extend(b"\x00")
    else:
        b.extend(b"\x01" + depends_on)
    b.extend(b"\x00")  # dependency type
    b.extend(_u(0, 2))  # min reputation
    if reward_mint is None:
        b.extend(b"\x00")
    else:
        b.extend(b"\x01" + reward_mint)
    return bytes(b)


class OnChainTaskVerifierTests(unittest.TestCase):
    def test_parses_open_sol_task_with_none_options(self):
        result = parse_task_account(fixture(), owner=PROGRAM_ID, now_unix=NOW)
        self.assertEqual(result["reward_lamports"], 1_000_000_000)
        self.assertEqual(result["status"], "open")
        self.assertIsNone(result["reward_mint"])

    def test_handles_variable_depends_on_option_layout(self):
        result = parse_task_account(
            fixture(depends_on=b"\x33" * 32), owner=PROGRAM_ID, now_unix=NOW
        )
        self.assertEqual(result["reward_lamports"], 1_000_000_000)

    def test_rejects_spl_token_mint(self):
        with self.assertRaisesRegex(OnChainVerificationError, "SPL token"):
            parse_task_account(fixture(reward_mint=b"\x44" * 32), owner=PROGRAM_ID, now_unix=NOW)

    def test_rejects_wrong_owner_and_discriminator(self):
        with self.assertRaisesRegex(OnChainVerificationError, "owner"):
            parse_task_account(fixture(), owner="not-program", now_unix=NOW)
        with self.assertRaisesRegex(OnChainVerificationError, "discriminator"):
            parse_task_account(fixture(discriminator=b"\xff" * 8), owner=PROGRAM_ID, now_unix=NOW)

    def test_rejects_non_open_expired_and_zero_reward(self):
        for data in (fixture(status=1), fixture(deadline=NOW), fixture(reward=0)):
            with self.assertRaises(OnChainVerificationError):
                parse_task_account(data, owner=PROGRAM_ID, now_unix=NOW)

    def test_rejects_truncated_data_invalid_option_and_unknown_capabilities(self):
        with self.assertRaisesRegex(OnChainVerificationError, "truncated"):
            parse_task_account(fixture()[:50], owner=PROGRAM_ID, now_unix=NOW)
        bad_option = bytearray(fixture())
        # dependsOn tag is after the fixed Task prefix through protocolFeeBps.
        bad_option[8 + 32 + 32 + 8 + 64 + 32 + 8 + 4 + 24 + 32 + 64 + 3 + 2] = 2
        with self.assertRaisesRegex(OnChainVerificationError, "Option"):
            parse_task_account(bytes(bad_option), owner=PROGRAM_ID, now_unix=NOW)
        with self.assertRaisesRegex(OnChainVerificationError, "capability"):
            parse_task_account(fixture(capabilities=1), owner=PROGRAM_ID, now_unix=NOW)
        with self.assertRaisesRegex(OnChainVerificationError, "reserved"):
            parse_task_account(fixture(capabilities=1 << 10), owner=PROGRAM_ID, now_unix=NOW)

    def test_rpc_cross_checks_account_against_candidate(self):
        raw = fixture()
        def rpc(url, payload, *, timeout):
            self.assertEqual(payload["method"], "getAccountInfo")
            return {"result": {"value": {"owner": PROGRAM_ID, "data": [base64.b64encode(raw).decode(), "base64"]}}}
        result = verify_task_on_chain(
            {"task_id": PDA, "reward_gross_sol": "1.000000000", "deadline_unix": NOW + 3600},
            rpc_url="https://rpc.example.org", now_unix=NOW, rpc_call=rpc,
        )
        self.assertTrue(result["read_only"])
        self.assertEqual(result["claims_made"], 0)

    def test_rpc_rejects_mismatched_reward_or_deadline(self):
        raw = fixture()
        def rpc(url, payload, *, timeout):
            return {"result": {"value": {"owner": PROGRAM_ID, "data": [base64.b64encode(raw).decode(), "base64"]}}}
        with self.assertRaisesRegex(OnChainVerificationError, "reward"):
            verify_task_on_chain(
                {"task_id": PDA, "reward_gross_sol": "2.000000000", "deadline_unix": NOW + 3600},
                rpc_url="https://rpc.example.org", now_unix=NOW, rpc_call=rpc,
            )
        with self.assertRaisesRegex(OnChainVerificationError, "deadline"):
            verify_task_on_chain(
                {"task_id": PDA, "reward_gross_sol": "1.000000000", "deadline_unix": NOW + 99},
                rpc_url="https://rpc.example.org", now_unix=NOW, rpc_call=rpc,
            )

    def test_rejects_insecure_rpc_url(self):
        with self.assertRaisesRegex(OnChainVerificationError, "HTTPS"):
            verify_task_on_chain(
                {"task_id": PDA, "reward_gross_sol": "1.000000000", "deadline_unix": NOW + 3600},
                rpc_url="http://rpc.example.org", now_unix=NOW, rpc_call=lambda *a, **k: {},
            )


if __name__ == "__main__":
    unittest.main()
