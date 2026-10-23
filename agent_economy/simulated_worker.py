"""Fail-closed dry-run worker for normalized AgenC job envelopes.

This module is deliberately offline: it never fetches task specs, claims work,
loads a wallet, signs transactions, uploads artifacts, or executes instructions
embedded in a job spec. A future provider adapter must normalize and verify
on-chain/API fields before calling this boundary.
"""
from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Any, Iterable


class JobRejected(ValueError):
    """A candidate does not meet the dry-run worker's safety gates."""


@dataclass(frozen=True)
class ValidatedJob:
    task_id: str
    listing_id: str
    reward_lamports: int
    deadline_unix: int
    spec_sha256: str
    required_capabilities: tuple[str, ...]


def validate_job_envelope(
    task: dict[str, Any],
    spec_bytes: bytes,
    *,
    expected_agent_id: str,
    expected_listing_id: str,
    supported_capabilities: Iterable[str],
    now_unix: int | None = None,
    max_spec_bytes: int = 256 * 1024,
) -> ValidatedJob:
    """Validate a normalized task and its exact spec bytes without executing it.

    Required normalized task keys: task_id, agent_id, listing_id, status,
    verified, deadline_unix, reward_lamports, spec_sha256, required_capabilities.
    The adapter must derive these from verified provider data; this function
    intentionally rejects missing or differently shaped values.
    """
    if not isinstance(task, dict):
        raise JobRejected("Task envelope must be an object")
    if not expected_agent_id or not expected_listing_id:
        raise JobRejected("Expected agent and listing identifiers are required")
    if not isinstance(spec_bytes, bytes) or not spec_bytes or len(spec_bytes) > max_spec_bytes:
        raise JobRejected("Job spec is empty or exceeds the configured limit")

    task_id = task.get("task_id")
    listing_id = task.get("listing_id")
    if not isinstance(task_id, str) or not task_id.strip():
        raise JobRejected("Missing task identity")
    if task.get("agent_id") != expected_agent_id:
        raise JobRejected("Task is not attributed to the configured agent")
    if listing_id != expected_listing_id:
        raise JobRejected("Task is not attributed to the configured listing")
    if task.get("status") != "open" or task.get("verified") is not True:
        raise JobRejected("Task is not verified and open")

    now = int(time.time()) if now_unix is None else int(now_unix)
    try:
        deadline = int(task.get("deadline_unix"))
        reward_decimal = Decimal(str(task.get("reward_lamports")))
    except (TypeError, ValueError, InvalidOperation) as exc:
        raise JobRejected("Invalid deadline or reward") from exc
    if deadline <= now:
        raise JobRejected("Task deadline has passed")
    if not reward_decimal.is_finite() or reward_decimal <= 0 or reward_decimal != reward_decimal.to_integral_value():
        raise JobRejected("Reward must be a positive integer number of lamports")

    expected_hash = task.get("spec_sha256")
    actual_hash = hashlib.sha256(spec_bytes).hexdigest()
    if not isinstance(expected_hash, str) or expected_hash.lower() != actual_hash:
        raise JobRejected("Job spec SHA-256 mismatch")

    try:
        spec = json.loads(spec_bytes.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise JobRejected("Job spec must be valid UTF-8 JSON") from exc
    if not isinstance(spec, dict):
        raise JobRejected("Job spec root must be an object")

    # Allow only one explicit, implemented operation. Never execute free-form
    # instructions, shell commands, URLs, code, or tool requests from the spec.
    if spec.get("operation") != "data_qa.inspect":
        raise JobRejected("Unsupported job operation")
    required = task.get("required_capabilities")
    if not isinstance(required, list) or any(not isinstance(x, str) or not x for x in required):
        raise JobRejected("Required capabilities must be a list of non-empty strings")
    supported = set(supported_capabilities)
    if not set(required).issubset(supported):
        raise JobRejected("Worker lacks one or more required capabilities")

    # The input path is intentionally not read from the untrusted job spec.
    return ValidatedJob(
        task_id=task_id,
        listing_id=listing_id,
        reward_lamports=int(reward_decimal),
        deadline_unix=deadline,
        spec_sha256=actual_hash,
        required_capabilities=tuple(sorted(set(required))),
    )


def run_dry_run(
    task: dict[str, Any],
    spec_bytes: bytes,
    *,
    expected_agent_id: str,
    expected_listing_id: str,
    supported_capabilities: Iterable[str],
    processed_task_ids: set[str],
    now_unix: int | None = None,
) -> dict[str, Any]:
    """Return a simulation receipt; does not read customer files or move funds."""
    validated = validate_job_envelope(
        task,
        spec_bytes,
        expected_agent_id=expected_agent_id,
        expected_listing_id=expected_listing_id,
        supported_capabilities=supported_capabilities,
        now_unix=now_unix,
    )
    if validated.task_id in processed_task_ids:
        raise JobRejected("Duplicate task: already processed in this run")
    # Idempotency is recorded only after every validation succeeds.
    processed_task_ids.add(validated.task_id)
    return {
        "mode": "dry_run",
        "status": "validated_not_executed",
        "task_id": validated.task_id,
        "listing_id": validated.listing_id,
        "spec_sha256": validated.spec_sha256,
        "required_capabilities": list(validated.required_capabilities),
        "reward_lamports_gross": str(validated.reward_lamports),
        "deadline_unix": validated.deadline_unix,
        "input_processed": False,
        "artifact_uploaded": False,
        "claim_made": False,
        "transaction_signed": False,
        "payment_made": False,
    }
