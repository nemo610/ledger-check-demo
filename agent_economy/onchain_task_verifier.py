"""Read-only Solana RPC verifier for AgenC Task and TaskJobSpec accounts.

Only public account reads are performed. This module never loads keys, signs,
claims tasks, builds transactions, or sends payments. Unknown layouts fail closed.
"""
from __future__ import annotations

import base64
import hashlib
import json
from decimal import Decimal, InvalidOperation
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request
from typing import Callable

PROGRAM_ID = "HJsZ53Zb27b8QMRbQpuDngE44AdwCGxvEZr61Zmxw1xK"
TASK_DISCRIMINATOR = bytes([79, 34, 229, 55, 88, 90, 55, 84])
JOB_SPEC_DISCRIMINATOR = hashlib.sha256(b"account:TaskJobSpec").digest()[:8]
MAX_RPC_RESPONSE_BYTES = 2 * 1024 * 1024
LAMPORTS_PER_SOL = Decimal(1_000_000_000)
_B58 = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
_P = 2**255 - 19
_D = (-121665 * pow(121666, _P - 2, _P)) % _P
_PDA_MARKER = b"ProgramDerivedAddress"


class OnChainVerificationError(RuntimeError):
    """The task could not be independently verified from its Solana account."""


def _b58decode(value: str) -> bytes:
    if not isinstance(value, str) or not value:
        raise OnChainVerificationError("Public key must be a non-empty base58 string")
    number = 0
    for char in value:
        if char not in _B58:
            raise OnChainVerificationError("Public key is not valid base58")
        number = number * 58 + _B58.index(char)
    raw = number.to_bytes((number.bit_length() + 7) // 8, "big") if number else b""
    decoded = b"\x00" * (len(value) - len(value.lstrip("1"))) + raw
    if len(decoded) != 32:
        raise OnChainVerificationError("Public key must decode to exactly 32 bytes")
    return decoded


def _b58encode(raw: bytes) -> str:
    zeros = len(raw) - len(raw.lstrip(b"\x00"))
    number = int.from_bytes(raw, "big")
    chars = []
    while number:
        number, remainder = divmod(number, 58)
        chars.append(_B58[remainder])
    return "1" * zeros + "".join(reversed(chars))


def _is_ed25519_point(compressed: bytes) -> bool:
    """Match Solana's compressed Edwards-Y decompression check."""
    if len(compressed) != 32:
        return False
    encoded = int.from_bytes(compressed, "little")
    sign = encoded >> 255
    y = encoded & ((1 << 255) - 1)
    if y >= _P:
        return False
    y2 = y * y % _P
    denominator = (_D * y2 + 1) % _P
    if denominator == 0:
        return False
    x2 = (y2 - 1) * pow(denominator, _P - 2, _P) % _P
    x = pow(x2, (_P + 3) // 8, _P)
    if (x * x - x2) % _P:
        x = x * pow(2, (_P - 1) // 4, _P) % _P
    if (x * x - x2) % _P:
        return False
    if x == 0 and sign:
        return False
    return True


def _create_program_address(seeds: list[bytes], program_id: bytes) -> bytes:
    if len(seeds) > 16 or any(len(seed) > 32 for seed in seeds):
        raise OnChainVerificationError("PDA seeds exceed Solana limits")
    digest = hashlib.sha256(b"".join(seeds) + program_id + _PDA_MARKER).digest()
    if _is_ed25519_point(digest):
        raise OnChainVerificationError("PDA bump produces an on-curve address")
    return digest


def _find_program_address(seeds: list[bytes], program_id: bytes) -> tuple[bytes, int]:
    for bump in range(255, -1, -1):
        try:
            return _create_program_address(seeds + [bytes([bump])], program_id), bump
        except OnChainVerificationError as exc:
            if "on-curve" not in str(exc):
                raise
    raise OnChainVerificationError("Could not derive a valid program-derived address")


def derive_task_pda(creator: bytes, task_id: bytes) -> tuple[str, int]:
    if len(creator) != 32 or len(task_id) != 32:
        raise OnChainVerificationError("Task creator and task_id must each be 32 bytes")
    address, bump = _find_program_address([b"task", creator, task_id], _b58decode(PROGRAM_ID))
    return _b58encode(address), bump


def derive_task_job_spec_pda(task_pubkey: str) -> tuple[str, int]:
    address, bump = _find_program_address([b"task_job_spec", _b58decode(task_pubkey)], _b58decode(PROGRAM_ID))
    return _b58encode(address), bump


class _Reader:
    def __init__(self, data: bytes):
        self.data = data
        self.offset = 0

    def take(self, count: int) -> bytes:
        if count < 0 or self.offset + count > len(self.data):
            raise OnChainVerificationError("Account data is truncated")
        value = self.data[self.offset:self.offset + count]
        self.offset += count
        return value

    def uint(self, count: int, *, signed: bool = False) -> int:
        return int.from_bytes(self.take(count), "little", signed=signed)

    def borsh_string(self) -> str:
        length = self.uint(4)
        if length > 4096:
            raise OnChainVerificationError("TaskJobSpec URI exceeds safe size limit")
        try:
            return self.take(length).decode("utf-8")
        except UnicodeDecodeError as exc:
            raise OnChainVerificationError("TaskJobSpec URI is not valid UTF-8") from exc

    def option_pubkey(self) -> bytes | None:
        tag = self.uint(1)
        if tag == 0:
            return None
        if tag == 1:
            return self.take(32)
        raise OnChainVerificationError("Invalid Borsh Option<Pubkey> tag")


def parse_task_account(data: bytes, *, owner: str, now_unix: int | None = None) -> dict:
    """Decode the official Task account prefix and reject unsupported task features."""
    if owner != PROGRAM_ID:
        raise OnChainVerificationError("Task account owner is not the official AgenC program")
    if not isinstance(data, bytes):
        raise OnChainVerificationError("Task account data must be bytes")
    reader = _Reader(data)
    if reader.take(8) != TASK_DISCRIMINATOR:
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
    if task_type != 0 or max_workers != 1:
        raise OnChainVerificationError("Only exclusive single-worker tasks are enabled for this first execution")
    if current_workers >= max_workers:
        raise OnChainVerificationError("Task has no remaining worker slots")
    return {
        "task_id_bytes": task_id_bytes,
        "creator_bytes": creator,
        "description_bytes": description,
        "task_id_bytes_hex": task_id_bytes.hex(),
        "canonical_pda_derivation_verified": False,
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
        "task_id_pda_derivation_verified": False,
        "note": "Read-only Task fields parsed; canonical PDA and TaskJobSpec binding are verified separately.",
    }


def parse_job_spec_account(data: bytes, *, owner: str) -> dict:
    if owner != PROGRAM_ID:
        raise OnChainVerificationError("TaskJobSpec account owner is not the official AgenC program")
    reader = _Reader(data)
    if reader.take(8) != JOB_SPEC_DISCRIMINATOR:
        raise OnChainVerificationError("TaskJobSpec account discriminator mismatch")
    task = reader.take(32)
    creator = reader.take(32)
    job_spec_hash = reader.take(32)
    job_spec_uri = reader.borsh_string()
    return {
        "task_bytes": task,
        "creator_bytes": creator,
        "job_spec_hash": job_spec_hash.hex(),
        "job_spec_uri": job_spec_uri,
    }


def _no_redirect(req, **kwargs):
    from urllib.request import HTTPRedirectHandler, build_opener
    class NoRedirect(HTTPRedirectHandler):
        def redirect_request(self, req, fp, code, msg, headers, newurl):
            return None
    return build_opener(NoRedirect).open(req, **kwargs)


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
                               "User-Agent": "ledger-check-readonly-verifier/0.2"})
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


def _get_account(rpc_url: str, address: str, *, timeout: float, rpc_call: Callable) -> tuple[bytes, str]:
    response = rpc_call(rpc_url, {
        "jsonrpc": "2.0", "id": 1, "method": "getAccountInfo",
        "params": [address, {"encoding": "base64", "commitment": "confirmed"}],
    }, timeout=timeout)
    try:
        value = response["result"]["value"]
        if not isinstance(value, dict):
            raise OnChainVerificationError(f"Account {address} does not exist on-chain")
        owner = value.get("owner")
        encoded = value["data"]
        if not isinstance(encoded, list) or len(encoded) != 2 or encoded[1] != "base64":
            raise OnChainVerificationError("Unexpected Solana account data encoding")
        return base64.b64decode(encoded[0], validate=True), owner
    except OnChainVerificationError:
        raise
    except (KeyError, TypeError, ValueError) as exc:
        raise OnChainVerificationError("Solana RPC account response has unexpected schema") from exc


def verify_task_on_chain(candidate: dict, *, rpc_url: str, now_unix: int | None = None,
                         timeout: float = 10.0, rpc_call: Callable = _rpc_json) -> dict:
    """Verify canonical Task PDA, reward/deadline and its on-chain TaskJobSpec pointer."""
    if not isinstance(candidate, dict):
        raise OnChainVerificationError("Candidate must be an object")
    pda = candidate.get("task_id")
    try:
        parsed = urlsplit(rpc_url)
        if (parsed.scheme != "https" or not parsed.hostname or parsed.username is not None
                or parsed.password is not None or parsed.fragment):
            raise OnChainVerificationError("RPC URL must be HTTPS without credentials or fragment")
        parsed.port
    except ValueError as exc:
        raise OnChainVerificationError("Malformed RPC URL") from exc
    _b58decode(pda)
    raw, owner = _get_account(rpc_url, pda, timeout=timeout, rpc_call=rpc_call)
    account = parse_task_account(raw, owner=owner, now_unix=now_unix)
    derived_task, task_bump = derive_task_pda(account["creator_bytes"], account["task_id_bytes"])
    if derived_task != pda:
        raise OnChainVerificationError("Task account address does not match canonical Task PDA derivation")
    if account["description_bytes"][32:] != b"\x00" * 32:
        raise OnChainVerificationError("Task description is not a canonical 32-byte content hash")
    expected_reward = Decimal(str(candidate.get("reward_gross_sol", ""))) * LAMPORTS_PER_SOL
    if not expected_reward.is_finite() or expected_reward != expected_reward.to_integral_value():
        raise OnChainVerificationError("Candidate reward cannot be represented exactly in lamports")
    if int(expected_reward) != account["reward_lamports"]:
        raise OnChainVerificationError("API candidate reward disagrees with on-chain reward")
    if candidate.get("deadline_unix") != account["deadline_unix"]:
        raise OnChainVerificationError("API candidate deadline disagrees with on-chain deadline")

    spec_pda, spec_bump = derive_task_job_spec_pda(pda)
    spec_raw, spec_owner = _get_account(rpc_url, spec_pda, timeout=timeout, rpc_call=rpc_call)
    spec = parse_job_spec_account(spec_raw, owner=spec_owner)
    if spec["task_bytes"] != _b58decode(pda):
        raise OnChainVerificationError("TaskJobSpec is bound to a different task")
    if spec["creator_bytes"] != account["creator_bytes"]:
        raise OnChainVerificationError("TaskJobSpec creator disagrees with Task creator")
    expected_hash = candidate.get("job_spec_hash")
    expected_uri = candidate.get("job_spec_uri")
    if not isinstance(expected_hash, str) or len(expected_hash) != 64:
        raise OnChainVerificationError("Candidate job_spec_hash is malformed")
    try:
        bytes.fromhex(expected_hash)
    except ValueError as exc:
        raise OnChainVerificationError("Candidate job_spec_hash is malformed") from exc
    if spec["job_spec_hash"].lower() != expected_hash.lower():
        raise OnChainVerificationError("API jobSpecHash disagrees with on-chain TaskJobSpec")
    if spec["job_spec_uri"] != expected_uri:
        raise OnChainVerificationError("API jobSpecUri disagrees with on-chain TaskJobSpec")
    description_hash = account["description_bytes"][:32]
    if description_hash != b"\x00" * 32 and description_hash.hex() != spec["job_spec_hash"]:
        raise OnChainVerificationError("Task description commitment disagrees with on-chain jobSpecHash")

    account.update({
        "pda": pda,
        "task_bump": task_bump,
        "task_job_spec_pda": spec_pda,
        "task_job_spec_bump": spec_bump,
        "canonical_pda_derivation_verified": True,
        "task_id_pda_derivation_verified": True,
        "job_spec_hash_verified_on_chain": True,
        "job_spec_uri_verified_on_chain": True,
        "job_spec_hash_on_chain": spec["job_spec_hash"],
        "job_spec_uri_on_chain": spec["job_spec_uri"],
        "rpc_commitment": "confirmed",
        "read_only": True,
        "transactions_signed": 0,
        "claims_made": 0,
        "payments_made": 0,
    })
    # Remove raw binary fields from the public JSON result.
    for key in ("task_id_bytes", "creator_bytes", "description_bytes"):
        account.pop(key, None)
    return account
