"""Fail-closed adapter from discovery summaries to the dry-run worker.

This adapter accepts only an explicitly normalized provider record. It does not
guess AgenC field names, decode capability bitmasks, fetch specs, or infer task
attribution. A provider-specific mapper must be implemented from verified
official schema before this can be used against live task data.
"""
from __future__ import annotations

from decimal import Decimal, InvalidOperation
import re
from typing import Any

from agent_economy.simulated_worker import JobRejected


def normalize_candidate_for_dry_run(
    candidate: dict[str, Any],
    provider_record: dict[str, Any],
    *,
    expected_agent_id: str,
    expected_listing_id: str,
) -> dict[str, Any]:
    """Build the worker envelope only when two snapshots agree on critical fields.

    provider_record is a normalized, independently verified record with keys:
    task_id, agent_id, listing_id, status, verified, deadline_unix,
    reward_lamports, spec_sha256, required_capabilities.
    """
    if not isinstance(candidate, dict) or not isinstance(provider_record, dict):
        raise JobRejected("Candidate and normalized provider record must be objects")
    if (not isinstance(expected_agent_id, str) or not expected_agent_id.strip()
            or not isinstance(expected_listing_id, str) or not expected_listing_id.strip()):
        raise JobRejected("Configured agent and listing IDs must be non-empty strings")

    task_id = provider_record.get("task_id")
    if not isinstance(task_id, str) or not task_id.strip() or candidate.get("task_id") != task_id:
        raise JobRejected("Discovery candidate and provider task identity do not match")
    if provider_record.get("agent_id") != expected_agent_id:
        raise JobRejected("Provider record is not attributed to the configured agent")
    if provider_record.get("listing_id") != expected_listing_id:
        raise JobRejected("Provider record is not attributed to the configured listing")
    if provider_record.get("status") != "open" or provider_record.get("verified") is not True:
        raise JobRejected("Provider record is not verified and open")

    deadline = provider_record.get("deadline_unix")
    reward = provider_record.get("reward_lamports")
    spec_hash = provider_record.get("spec_sha256")
    caps = provider_record.get("required_capabilities")
    if isinstance(deadline, bool) or not isinstance(deadline, int):
        raise JobRejected("Provider deadline must be an integer Unix timestamp")
    if isinstance(reward, bool) or not isinstance(reward, int) or reward <= 0:
        raise JobRejected("Provider reward must be a positive integer number of lamports")
    if not isinstance(spec_hash, str) or not re.fullmatch(r"[a-fA-F0-9]{64}", spec_hash):
        raise JobRejected("Provider spec hash must be a 64-character SHA-256 hex digest")
    if not isinstance(caps, list) or any(not isinstance(x, str) or not x for x in caps):
        raise JobRejected("Capabilities must be an explicit list of non-empty strings")

    # Compare exact decimal SOL to lamports, without floating-point conversion.
    try:
        discovered_lamports = Decimal(str(candidate.get("reward_gross_sol"))) * Decimal("1000000000")
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise JobRejected("Discovery reward is missing or malformed") from exc
    if not discovered_lamports.is_finite() or discovered_lamports != Decimal(reward):
        raise JobRejected("Discovery reward and provider record disagree")
    if candidate.get("deadline_unix") != deadline:
        raise JobRejected("Discovery deadline and provider record disagree")
    if candidate.get("job_spec_hash") != spec_hash:
        raise JobRejected("Discovery spec hash and provider record disagree")
    if candidate.get("status") != "open" or candidate.get("verified") is not True:
        raise JobRejected("Discovery candidate is not verified and open")
    if candidate.get("required_capabilities") != caps:
        # Never interpret a provider bitmask such as "0" as a capability list
        # without an official, tested mapping.
        raise JobRejected("Discovery capabilities are not an explicit matching list")

    return {
        "task_id": task_id,
        "agent_id": expected_agent_id,
        "listing_id": expected_listing_id,
        "status": "open",
        "verified": True,
        "deadline_unix": deadline,
        "reward_lamports": reward,
        "spec_sha256": spec_hash,
        "required_capabilities": list(caps),
    }
