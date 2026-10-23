"""Read-only live audit for AgenC tasks; this module never claims or pays."""
from __future__ import annotations

import argparse
import hashlib
import ipaddress
import json
import os
import sys
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener, urlopen

from agent_economy.onchain_task_verifier import (
    OnChainVerificationError,
    verify_task_on_chain,
)
from agent_economy.task_discovery import DiscoveryError, discover_tasks

MAX_SPEC_BYTES = 256 * 1024


class SpecVerificationError(RuntimeError):
    """A task specification could not be safely retrieved or verified."""


def fetch_spec_bytes(uri: str, *, timeout: float = 8.0, opener=None) -> bytes:
    """Fetch a small HTTPS spec without redirects; reject literal private IPs."""
    try:
        parsed = urlsplit(uri)
        if (parsed.scheme != "https" or not parsed.hostname or parsed.username is not None
                or parsed.password is not None or parsed.fragment):
            raise SpecVerificationError("Spec URI must be HTTPS without credentials or fragment")
        parsed.port
        try:
            address = ipaddress.ip_address(parsed.hostname)
        except ValueError:
            address = None
        if address is not None and (not address.is_global or address.is_multicast):
            raise SpecVerificationError("Spec URI must not target a non-public IP address")
    except ValueError as exc:
        raise SpecVerificationError("Malformed spec URI") from exc
    if not 0 < timeout <= 15:
        raise SpecVerificationError("Spec timeout must be greater than 0 and at most 15 seconds")

    class NoRedirect(HTTPRedirectHandler):
        def redirect_request(self, req, fp, code, msg, headers, newurl):
            return None

    if opener is None:
        opener = build_opener(NoRedirect).open
    request = Request(uri, headers={
        "Accept": "application/json",
        "User-Agent": "ledger-check-readonly-spec-audit/0.1",
    })
    try:
        with opener(request, timeout=timeout) as response:
            if response.status != 200:
                raise SpecVerificationError(f"Spec server returned HTTP {response.status}")
            body = response.read(MAX_SPEC_BYTES + 1)
            if len(body) > MAX_SPEC_BYTES:
                raise SpecVerificationError("Spec exceeds 256 KiB size limit")
            return body
    except SpecVerificationError:
        raise
    except (HTTPError, URLError, TimeoutError, OSError) as exc:
        raise SpecVerificationError(f"Could not safely fetch task spec: {exc}") from exc


def audit_snapshot(snapshot: dict, *, rpc_url: str | None,
                   now_unix: int | None = None, spec_fetcher=fetch_spec_bytes) -> dict:
    """Add verification evidence to candidates; never labels a task executable."""
    audited = []
    for candidate in snapshot.get("candidates", []):
        record = {
            "task_id": candidate.get("task_id"),
            "title": candidate.get("title", ""),
            "gross_reward_sol": candidate.get("reward_gross_sol"),
            "deadline_unix": candidate.get("deadline_unix"),
            "denomination": candidate.get("denomination", "unknown"),
            "actionable": False,
            "status": "unverified",
            "onchain": None,
            "spec_sha256_matches": False,
            "canonical_pda_verified": False,
            "job_spec_hash_verified_on_chain": False,
            "transactions_signed": 0,
            "claims_made": 0,
            "payments_made": 0,
        }
        if not rpc_url:
            record["reason"] = "No SOLANA_RPC_URL/--rpc-url supplied; on-chain denomination and account not verified."
            audited.append(record)
            continue
        try:
            onchain = verify_task_on_chain(candidate, rpc_url=rpc_url, now_unix=now_unix)
            record["onchain"] = onchain
            record["denomination"] = "SOL_confirmed_on_chain"
        except (OnChainVerificationError, ValueError, KeyError, TypeError) as exc:
            record["status"] = "rejected"
            record["reason"] = f"On-chain verification failed: {exc}"
            audited.append(record)
            continue
        try:
            spec_bytes = spec_fetcher(candidate["job_spec_uri"])
            actual_hash = hashlib.sha256(spec_bytes).hexdigest()
            expected_hash = candidate["job_spec_hash"].lower()
            record["spec_sha256"] = actual_hash
            record["spec_sha256_matches"] = actual_hash == expected_hash
            if not record["spec_sha256_matches"]:
                record["status"] = "rejected"
                record["reason"] = "Downloaded specification SHA-256 does not match indexer hash."
            elif not onchain.get("canonical_pda_derivation_verified") or not onchain.get("job_spec_hash_verified_on_chain"):
                record["status"] = "partial_verified_not_actionable"
                record["reason"] = (
                    "Downloaded spec hash matches the indexer, but canonical Task PDA or on-chain "
                    "TaskJobSpec binding is missing. Human review and execution safeguards remain mandatory."
                )
            else:
                record["canonical_pda_verified"] = True
                record["job_spec_hash_verified_on_chain"] = True
                record["status"] = "verified_not_actionable"
                record["reason"] = (
                    "Canonical Task PDA, reward, deadline, TaskJobSpec hash/URI and downloaded spec "
                    "bytes are independently consistent at confirmed commitment. This is still not "
                    "authorization to claim: inspect the work, net reward, costs and settlement terms."
                )
        except (SpecVerificationError, KeyError, ValueError, TypeError) as exc:
            record["status"] = "partial_unverified_not_actionable"
            record["reason"] = f"On-chain account checked, but spec could not be verified: {exc}"
        audited.append(record)

    return {
        "provider": "agenc",
        "mode": "read_only_audit",
        "candidate_count": len(audited),
        "audited_candidates": audited,
        "write_operations_enabled": False,
        "transactions_signed": 0,
        "claims_made": 0,
        "payments_made": 0,
        "live_execution_enabled": False,
        "limitations": [
            "This audit does not claim, execute, submit, or pay for tasks.",
            "Verified candidates remain non-actionable; a human must review the complete task, eligibility, deadline, costs and settlement terms.",
            "This audit does not prove task acceptance or eventual payout; only a confirmed settlement transaction proves payment.",
            "A verified gross reward is not net income; fees, rejection, execution costs, reputation and acceptance terms may reduce payout.",
        ],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Read-only AgenC live task audit; no claims/signatures/payments.")
    parser.add_argument("--out", default="output/agenc_live_task_audit.json")
    parser.add_argument("--page-size", type=int, default=100)
    parser.add_argument("--rpc-url", default=os.environ.get("SOLANA_RPC_URL"))
    args = parser.parse_args(argv)
    try:
        snapshot = discover_tasks(page_size=args.page_size)
        result = audit_snapshot(snapshot, rpc_url=args.rpc_url)
    except (DiscoveryError, ValueError) as exc:
        print(f"Live audit unavailable: {exc}", file=sys.stderr)
        return 2
    output = Path(args.out)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    verified = sum(item["status"] == "verified_not_actionable"
                    for item in result["audited_candidates"])
    print(f"Read-only audit saved: {output}; candidates={result['candidate_count']}; verified_not_actionable={verified}")
    print("No task claimed; no transaction signed; no payment made; live execution remains disabled.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
