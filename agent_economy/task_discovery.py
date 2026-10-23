"""Read-only, conservative discovery of public AgenC tasks.

Uses the documented GET /api/tasks read endpoint. It never claims tasks,
connects a signer, builds transactions, or spends funds.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlsplit
from urllib.request import Request, urlopen
from typing import Callable

API_BASE = "https://api.agenc.ag"
MAX_API_RESPONSE_BYTES = 2 * 1024 * 1024
LAMPORTS_PER_SOL = Decimal("1000000000")


class DiscoveryError(RuntimeError):
    """A public task snapshot could not be safely interpreted."""


def _fetch_json(url: str, *, timeout: float = 10.0, opener: Callable = urlopen) -> dict:
    request = Request(url, headers={
        "Accept": "application/json",
        "User-Agent": "ledger-check-agent-task-discovery/0.1",
    })
    try:
        with opener(request, timeout=timeout) as response:
            if response.status != 200:
                raise DiscoveryError(f"AgenC read API returned HTTP {response.status}")
            # Bound memory use even if the public endpoint returns an unexpectedly
            # large body. Read one extra byte so truncation cannot look like JSON.
            raw = response.read(MAX_API_RESPONSE_BYTES + 1)
            if len(raw) > MAX_API_RESPONSE_BYTES:
                raise DiscoveryError(
                    f"AgenC task response exceeds {MAX_API_RESPONSE_BYTES} bytes"
                )
            payload = json.loads(raw.decode("utf-8"))
    except (HTTPError, URLError, TimeoutError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise DiscoveryError(f"Could not read AgenC tasks: {exc}") from exc
    if not isinstance(payload, dict) or not isinstance(payload.get("items"), list):
        raise DiscoveryError("AgenC task response has an unexpected schema")
    return payload


def _rank_task(task: dict, *, now_unix: int) -> dict | None:
    """Return a conservative candidate summary, or None when not eligible."""
    if not isinstance(task, dict):
        return None
    if task.get("status") != "open":
        return None
    # The documented TaskView omits rewardMint. Absence is UNKNOWN, not proof
    # of SOL denomination; only an explicit null mint is eligible here.
    if "rewardMint" not in task or task.get("rewardMint") is not None:
        return None
    try:
        reward_lamports = Decimal(str(task.get("rewardLamports", "")))
        deadline = int(task.get("deadlineUnix", 0))
    except (InvalidOperation, ValueError, TypeError):
        return None
    if (
        not reward_lamports.is_finite()
        or reward_lamports <= 0
        or reward_lamports != reward_lamports.to_integral_value()
        or deadline <= now_unix
    ):
        return None
    # Be conservative: require the strongest public evidence and a pinned HTTPS spec.
    if task.get("verified") is not True:
        return None
    # A missing provider identity must never become an apparently actionable
    # candidate. Keep discovery read-only and fail closed on malformed IDs.
    task_id = task.get("pda")
    if not isinstance(task_id, str) or not task_id.strip():
        return None
    spec_uri = task.get("jobSpecUri")
    spec_hash = task.get("jobSpecHash")
    if not isinstance(spec_uri, str):
        return None
    try:
        parsed_uri = urlsplit(spec_uri)
        if (parsed_uri.scheme != "https" or not parsed_uri.hostname
                or parsed_uri.username is not None or parsed_uri.password is not None
                or parsed_uri.fragment):
            return None
        parsed_uri.port  # Force validation of malformed ports.
    except ValueError:
        return None
    if not isinstance(spec_hash, str) or not re.fullmatch(r"[a-fA-F0-9]{64}", spec_hash):
        return None
    gross_sol = reward_lamports / LAMPORTS_PER_SOL
    # Official AgenC TaskView contract documents requiredCapabilities as a
    # decimal-string u64 bitmask; the AgentCard schema explicitly defines "0"
    # as no capability requirement. Normalize only that unambiguous case.
    # Nonzero bitmasks remain opaque until every bit has a verified mapping.
    raw_capabilities = task.get("requiredCapabilities")
    normalized_capabilities = [] if raw_capabilities == "0" else raw_capabilities
    # Fee splits vary by task; gross reward is the only safe upper bound without
    # verified fee-leg fields from the live task account.
    return {
        "task_id": task_id,
        "title": str(task.get("title", "")),
        "status": "open",
        "verified": True,
        "reward_gross_sol": str(gross_sol.quantize(Decimal("0.000000001"))),
        "gross_reward_upper_bound_sol": str(gross_sol.quantize(Decimal("0.000000001"))),
        "deadline_unix": deadline,
        "seconds_to_deadline": deadline - now_unix,
        "job_spec_uri": spec_uri,
        "job_spec_hash": spec_hash,
        "required_capabilities": normalized_capabilities,
        "min_reputation": task.get("minReputation"),
        "max_workers": task.get("maxWorkers"),
        "current_workers": task.get("currentWorkers"),
        "note": "Gross reward only, not a net payout estimate. Task-specific protocol/operator/referrer fees, execution costs, eligibility gates and acceptance may reduce or eliminate earnings.",
    }


def discover_tasks(*, page_size: int = 100, timeout: float = 10.0,
                   now_unix: int | None = None, fetcher: Callable = _fetch_json) -> dict:
    if not 1 <= page_size <= 100:
        raise ValueError("page_size must be between 1 and 100")
    if not 0 < timeout <= 30:
        raise ValueError("timeout must be greater than 0 and at most 30 seconds")
    now = int(time.time()) if now_unix is None else int(now_unix)
    query = urlencode({"status": "open", "page": 1, "pageSize": page_size})
    payload = fetcher(f"{API_BASE}/api/tasks?{query}", timeout=timeout)
    if not isinstance(payload, dict) or not isinstance(payload.get("items"), list):
        raise DiscoveryError("AgenC task response has an unexpected schema")
    ranked = []
    for task in payload["items"]:
        summary = _rank_task(task, now_unix=now)
        if summary is not None:
            ranked.append(summary)
    # Prefer higher gross rewards, then the nearest deadline; never rank urgency backwards.
    ranked.sort(key=lambda item: (-Decimal(item["gross_reward_upper_bound_sol"]), item["seconds_to_deadline"]))
    return {
        "provider": "agenc",
        "mode": "read_only",
        "queried_at_utc": datetime.fromtimestamp(now, timezone.utc).isoformat(),
        "source": f"{API_BASE}/api/tasks?{query}",
        "source_total_reported": payload.get("total"),
        "candidate_count": len(ranked),
        "candidates": ranked,
        "write_operations_enabled": False,
        "claims_made": 0,
        "transactions_signed": 0,
        "payments_made": 0,
        "limitations": [
            "Public indexer snapshot can be delayed by about 45 seconds.",
            "The documented TaskView omits rewardMint; candidates are admitted only if an explicit null mint is present, otherwise denomination remains unknown and the task is rejected.",
            "A candidate is not a commitment that our agent qualifies or can complete the work.",
            "Gross reward is not net payout; fee splits vary by task, and execution costs or rejection may eliminate earnings.",
            "No task is claimed, no wallet is loaded, and no transaction is built or signed.",
            "A human must inspect the full specification, deadline, reward, eligibility, costs and acceptance terms before any action.",
        ],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Read-only AgenC task scan; never claims or signs.")
    parser.add_argument("--out", default="output/agenc_task_candidates.json")
    parser.add_argument("--page-size", type=int, default=100)
    args = parser.parse_args(argv)
    try:
        snapshot = discover_tasks(page_size=args.page_size)
    except (DiscoveryError, ValueError) as exc:
        print(f"Discovery unavailable: {exc}", file=sys.stderr)
        return 2
    output = Path(args.out)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(snapshot, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Read-only snapshot saved: {output}; candidates={snapshot['candidate_count']}")
    print("No task claimed; no wallet signature or payment.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
