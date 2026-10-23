"""Fail-closed verification for untrusted, pinned marketplace job specs.

This module validates bytes and integrity only. It never executes instructions,
fetches URLs, invokes an LLM, claims tasks, or signs transactions.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import re
from typing import Any

MAX_JOB_SPEC_BYTES = 256 * 1024
_SHA256 = re.compile(r"^[a-fA-F0-9]{64}$")


class JobSpecError(ValueError):
    """A job specification is too large, malformed, or fails its pinned hash."""


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise JobSpecError("Job spec JSON contains duplicate object keys")
        result[key] = value
    return result


def _reject_constant(value: str) -> None:
    raise JobSpecError(f"Job spec JSON contains non-standard constant {value}")


def verify_job_spec(
    raw: bytes,
    expected_sha256: str,
    *,
    max_bytes: int = MAX_JOB_SPEC_BYTES,
) -> dict[str, Any]:
    """Verify the exact raw-byte SHA-256 and parse a JSON object safely.

    The returned object explicitly marks the content as untrusted and not
    approved for execution. Callers must separately validate task attribution,
    capabilities, deadline, reward, scope, and acceptance conditions.
    """
    if not isinstance(raw, bytes):
        raise JobSpecError("Job spec must be supplied as raw bytes")
    if max_bytes <= 0 or max_bytes > MAX_JOB_SPEC_BYTES:
        raise JobSpecError(f"max_bytes must be between 1 and {MAX_JOB_SPEC_BYTES}")
    if not raw:
        raise JobSpecError("Job spec is empty")
    if len(raw) > max_bytes:
        raise JobSpecError("Job spec exceeds the size limit")
    if not isinstance(expected_sha256, str) or not _SHA256.fullmatch(expected_sha256):
        raise JobSpecError("Expected job spec hash must be a 64-character SHA-256 hex digest")

    actual = hashlib.sha256(raw).hexdigest()
    if not hmac.compare_digest(actual, expected_sha256.lower()):
        raise JobSpecError("Job spec SHA-256 does not match the pinned hash")
    try:
        payload = json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=_unique_object,
            parse_constant=_reject_constant,
        )
    except (UnicodeDecodeError, json.JSONDecodeError, RecursionError) as exc:
        raise JobSpecError("Job spec must be valid UTF-8 JSON") from exc
    if not isinstance(payload, dict):
        raise JobSpecError("Job spec JSON root must be an object")
    return {
        "sha256": actual,
        "size_bytes": len(raw),
        "spec": payload,
        "trusted": False,
        "execution_approved": False,
        "next_step": "Human review and task-field cross-check required; no execution is authorized.",
    }
