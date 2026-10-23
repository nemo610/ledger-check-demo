"""Read-only Solana RPC verifier for AgenC Task accounts.

This module only reads public account data. It never creates transactions, loads
keys, signs, claims tasks, or sends payments. Unknown/malformed layouts fail closed.
"""
from __future__ import annotations

import base64
import json
import re
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen
from typing import Callable

PROGRAM_ID = "HJsZ53Zb27b8QMRbQpuDngE44AdwCGxvEZr61Zmxw1xK"
TASK_DISCRIMINATOR = bytes([79, 34, 229, 55, 88, 90, 55, 84])
MAX_RPC_RESPONSE_BYTES = 2 * 1024 * 1024


class OnChainVerificationError(RuntimeError):
    """The task could not be independently verified from its Solana account."""


def _b58decode(value: str) -> bytes:
    alphabet = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
    if not isinstance(value, str) or not value:
        raise OnChainVerificationError("Task PDA must be a non-empty base58 string")
    number = 0
    for char in value:
        if char not in alphabet:
            raise OnChainVerificationError("Task PDA is not valid base58")
        number = number * 58 + alphabet.index(char)
    raw = number.to_bytes((number.bit_length() + 7) // 8, "big") if number else b""
    leading_zeroes = len(value) - len(value.lstrip("1"))
    decoded = b"\\x00" * leading_zeroes + raw
    if len(decoded) != 32:
        raise OnChainVerificationError("Task PDA must decode to exactly 32 bytes")
    return decoded


class _Reader:
    def __init__(self, data: bytes):
        self.data = data
        self.offset = 0

    def take(self, count: int) -> bytes:
        if count < 0 or self.offset + count > len(self.data):
            raise OnChainVerificationError("Task account data is truncated")
        value = self.data[self.offset:self.offset + count]
        self.offset += count
        return value

    def uint(self, count: int, *, signed: bool = False) -> int:
        return int.from_bytes(self.take(count), "little", signed=signed)

    def option_pubkey(self) -> bytes | None:
        tag = self.uint(1)
        if tag == 0:
            return None
        if tag == 1:
            return self.take(32)
        raise OnChainVerificationError("Invalid Borsh Option<Pubkey> tag")


def parse_task_account(data: bytes, *, owner: str, expected_task_id: str | None = None,
                       now_unix: int | None = None) -> dict:
    """Decode the verified prefix of the official generated Task account layout."""
    if owner != PROGRAM_ID:
        raise OnChainVerificationError("Task account owner is not the official AgenC program")
    if not isinstance(data, bytes):
        raise OnChainVerificationError("Task account data must be bytes")
    reader = _Reader(data)
    discriminator = reader.take(8)
    if discriminator != TASK_DISCRIMINATOR:
        raise OnChainVerificationError("Task account discriminator mismatch")
    task_id_bytes = reader.take(32)
    creator = reader.take(32)
    capabilities = reader.uint(8)
    description = reader.take(64)
    constraint_hash = reader.take(32)
    reward_lamports = reader.uint(8)
    max_workers = reader.uint(1)
    current_workers = reader.uint(1)
    status = reader.uint(1)
    task_type = reader.uint(1)
    created_at = reader.uint(8, signed=True)
    deadline = reader.uint(8, signed=True)
    completed_at = reader.uint(8, signed=True)
    escrow = reader.take(32)
    result = reader.take(64)
    completions = reader.uint(1)
    required_completions = reader.uint(1)
    bump = reader.uint(1)
    protocol_fee_bps = reader.uint(2)
    depends_on = reader.option_pubkey()
    dependency_type = reader.uint(1)
    min_reputation = reader.uint(2)
    reward_mint = reader.option_pubkey()

    if expected_task_id is not None and _b58decode(expected_task_id) != task_id_bytes:
        raise OnChainVerificationError("Task PDA does not match the account's embedded task_id")
    if status != 0:
        raise OnChainVerificationError("On-chain task status is not Open")
    if reward_lamports <= 0:
        raise OnChainVerificationError("On-chain reward is not positive")
    if deadline < 0:
        raise OnChainVerificationError("On-chain deadline is invalid")
    if now_unix is not None and deadline != 0 and deadline <= int(now_unix):
        raise OnChainVerificationError("On-chain task deadline has passed")
    if reward_mint is not None:
        raise OnChainVerificationError("On-chain task reward is an SPL token, not SOL")
    if capabilities >> 10:
        raise OnChainVerificationError("Task requires reserved/unknown capability bits")
    if capabilities != 0:
        raise OnChainVerificationError("Nonzero capability mapping is not enabled for live execution")

    return {
        "task_id_bytes_hex": task_id_bytes.hex(),
        "status": "open",
        "reward_lamports": reward_lamports,
        "deadline_unix": deadline,
        "required_capabilities_bitmask": str(capabilities),
        "required_capabilities": [],
        "reward_mint": None,
        "max_workers": max_workers,
        "current_workers": current_workers,
        "min_reputation": min_reputation,
        "program_owner": owner,
        "account_discriminator_verified": True,
        "account_layout_verified_through_reward_mint": True,
        "job_spec_hash_verified_on_chain": False,
        "note": "On-chain Task fields verified read-only; jobSpecHash/URI are not proven by this account decoder.",
    }


def _no_redirect(req, **kwargs):
    # urllib's default redirect handler follows redirects. Do not follow RPC redirects.
    from urllib.request import HTTPRedirectHandler, build_opener
    class NoRedirect(HTTPRedirectHandler):
        def redirect_request(self, req, fp, code, msg, headers, newurl):
            return None
    opener = build_opener(NoRedirect)
    return opener.open(req, **kwargs)


def _rpc_json(url: str, payload: dict, *, timeout: float = 10.0,
              opener: Callable = _no_redirect) -> dict:
    try:
        parsed = urlsplit(url)
        if (parsed.scheme != "https" or not parsed.hostname or parsed.username is not None
                or parsed.password is not None or parsed.fragment):
            raise OnChainVerificationError("RPC URL must be HTTPS without credentials or fragment")
        parsed.port
    except ValueError as exc:
        raise OnChainVerificationError("Malformed RPC URL") from exc
    if not 0 < timeout <= 20:
        raise OnChainVerificationError("RPC timeout must be greater than 0 and at most 20 seconds")
    request = Request(url, data=json.dumps(payload).encode("utf-8"), method="POST",
                      headers={"Content-Type": "application/json", "Accept": "application/json",
                               "User-Agent": "ledger-check-readonly-verifier/0.1"})
    try:
        with opener(request, timeout=timeout) as response:
            raw = response.read(MAX_RPC_RESPONSE_BYTES + 1)
            if len(raw) > MAX_RPC_RESPONSE_BYTES:
                raise OnChainVerificationError("Solana RPC response exceeds size limit")
            result = json.loads(raw.decode("utf-8"))
    except OnChainVerificationError:
        raise
    except (HTTPError, URLError, TimeoutError, UnicodeDecodeError, json.JSONDecodeError, OSError) as exc:
        raise OnChainVerificationError(f"Solana RPC read failed: {exc}") from exc
    if not isinstance(result, dict) or result.get("error") is not None:
        raise OnChainVerificationError("Solana RPC returned an error or unexpected schema")
    return result


def verify_task_on_chain(candidate: dict, *, rpc_url: str, now_unix: int | None = None,
                         timeout: float = 10.0, rpc_call: Callable = _rpc_json) -> dict:
    """Read one Task account using getAccountInfo; never signs or writes."""
    if not isinstance(candidate, dict):
        raise OnChainVerificationError("Candidate must be an object")
    pda = candidate.get("task_id")
    _b58decode(pda)
    response = rpc_call(rpc_url, {
        "jsonrpc": "2.0", "id": 1, "method": "getAccountInfo",
        "params": [pda, {"encoding": "base64", "commitment": "confirmed"}],
    }, timeout=timeout)
    try:
        value = response["result"]["value"]
        if not isinstance(value, dict):
            raise OnChainVerificationError("Task account does not exist on-chain")
        owner = value.get("owner")
        encoded = value["data"]
        if not isinstance(encoded, list) or len(encoded) != 2 or encoded[1] != "base64":
            raise OnChainVerificationError("Unexpected Solana account data encoding")
        raw = base64.b64decode(encoded[0], validate=True)
    except OnChainVerificationError:
        raise
    except (KeyError, TypeError, ValueError) as exc:
        raise OnChainVerificationError("Solana RPC account response has unexpected schema") from exc
    account = parse_task_account(raw, owner=owner, expected_task_id=pda, now_unix=now_unix)
    try:
        expected_reward = int(candidate["reward_gross_sol"].replace(".", "").ljust(10, "0"))
    except (KeyError, AttributeError, ValueError) as exc:
        raise OnChainVerificationError("Candidate reward is malformed") from exc
    # Avoid trusting float math: convert SOL text to integer lamports exactly.
    from decimal import Decimal, InvalidOperation
    try:
        decimal_reward = Decimal(str(candidate["reward_gross_sol"]))
        expected_reward = decimal_reward * Decimal(1_000_000_000)
    except (InvalidOperation, ValueError) as exc:
        raise OnChainVerificationError("Candidate reward is malformed") from exc
    if not expected_reward.is_finite() or expected_reward != expected_reward.to_integral_value():
        raise OnChainVerificationError("Candidate reward cannot be represented exactly in lamports")
    if int(expected_reward) != account["reward_lamports"]:
        raise OnChainVerificationError("API candidate reward disagrees with on-chain reward")
    if candidate.get("deadline_unix") != account["deadline_unix"]:
        raise OnChainVerificationError("API candidate deadline disagrees with on-chain deadline")
    account["pda"] = pda
    account["rpc_commitment"] = "confirmed"
    account["read_only"] = True
    account["transactions_signed"] = 0
    account["claims_made"] = 0
    account["payments_made"] = 0
    return account
