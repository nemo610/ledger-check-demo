"""Read-only AgenC account/listing readiness check.

This checks the public indexer only. It never signs, claims, publishes, pays,
or treats an indexer response as proof of settlement.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import HTTPRedirectHandler, Request, build_opener

API_BASE = "https://api.agenc.ag"
MAX_RESPONSE_BYTES = 2 * 1024 * 1024
WALLET_RE = re.compile(r"^[1-9A-HJ-NP-Za-km-z]{32,44}$")


class ReadinessError(RuntimeError):
    """A public AgenC response could not be safely interpreted."""


def _open_no_redirect(request: Request, *, timeout: float):
    class NoRedirect(HTTPRedirectHandler):
        def redirect_request(self, req, fp, code, msg, headers, newurl):
            return None

    return build_opener(NoRedirect).open(request, timeout=timeout)


def fetch_json(path: str, *, timeout: float = 10.0) -> dict:
    """Fetch bounded JSON from the official public read API over HTTPS."""
    if not path.startswith("/api/") or path.startswith("//"):
        raise ReadinessError("Only official AgenC /api/ read endpoints are allowed")
    url = API_BASE + path
    request = Request(url, headers={
        "Accept": "application/json",
        "User-Agent": "ledger-check-agenc-readiness/0.1",
    })
    try:
        with _open_no_redirect(request, timeout=timeout) as response:
            if response.status != 200:
                raise ReadinessError(f"AgenC returned HTTP {response.status} for {path}")
            raw = response.read(MAX_RESPONSE_BYTES + 1)
            if len(raw) > MAX_RESPONSE_BYTES:
                raise ReadinessError("AgenC response exceeded the 2 MiB safety limit")
            payload = json.loads(raw.decode("utf-8"))
    except ReadinessError:
        raise
    except (HTTPError, URLError, TimeoutError, UnicodeDecodeError, json.JSONDecodeError, OSError) as exc:
        raise ReadinessError(f"Could not read {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise ReadinessError(f"AgenC returned an unexpected JSON shape for {path}")
    return payload


def _items(payload: dict, label: str) -> list[dict]:
    items = payload.get("items")
    if not isinstance(items, list) or any(not isinstance(item, dict) for item in items):
        raise ReadinessError(f"AgenC {label} response has no valid items list")
    return items


def inspect_wallet(wallet: str, *, getter=fetch_json) -> dict:
    """Inspect registration, listings and storefront for a public wallet."""
    wallet = str(wallet).strip()
    if not WALLET_RE.fullmatch(wallet):
        raise ValueError("wallet must be a valid-looking Solana base58 public address")

    encoded = quote(wallet, safe="")
    report = {
        "provider": "AgenC",
        "checked_at_utc": datetime.now(timezone.utc).isoformat(),
        "wallet": wallet,
        "source": "public read API; indexer snapshot, not direct transaction proof",
        "read_only": True,
        "transactions_signed": 0,
        "claims_made": 0,
        "payments_made": 0,
        "checks": {},
        "blockers": [],
    }

    def run_check(name: str, path: str, parse):
        try:
            value = parse(getter(path))
            report["checks"][name] = {"status": "ok", **value}
        except (ReadinessError, ValueError, TypeError, KeyError) as exc:
            report["checks"][name] = {"status": "unknown", "reason": str(exc)}
            report["blockers"].append(f"{name}: {exc}")

    def agents(payload):
        rows = _items(payload, "agents")
        matches = [row for row in rows if row.get("authority") == wallet]
        return {
            "registered": bool(matches),
            "count": len(matches),
            "agents": [{
                "pda": row.get("pda"),
                "status": row.get("status"),
                "stake_lamports": row.get("stake"),
                "reputation": row.get("reputation"),
                "tasks_completed": row.get("tasksCompleted"),
            } for row in matches],
        }

    def listings(payload):
        rows = _items(payload, "listings")
        matches = [row for row in rows if row.get("authority") == wallet or row.get("creator") == wallet]
        # The API's wallet filter is the primary selector. Preserve the returned
        # rows if the current view does not expose its authority field.
        if not matches and rows and all("authority" not in row and "creator" not in row for row in rows):
            matches = rows
        return {
            "count": len(matches),
            "listings": [{
                "pda": row.get("pda"),
                "name": row.get("name"),
                "state": row.get("state"),
                "provider_agent": row.get("providerAgent"),
                "price_lamports": row.get("priceLamports"),
                "moderation": row.get("moderation"),
            } for row in matches],
        }

    def hireable(payload):
        rows = _items(payload, "hireable listings")
        return {"count": len(rows), "listing_pdas": [row.get("pda") for row in rows]}

    def store(payload):
        value = payload.get("store")
        if value is None and any(key in payload for key in ("handle", "wallet", "manifestUri")):
            value = payload
        if value is not None and not isinstance(value, dict):
            raise ReadinessError("AgenC store response has an unexpected schema")
        return {
            "registered": isinstance(value, dict),
            "handle": value.get("handle") if isinstance(value, dict) else None,
            "public_manifest": value.get("manifestUri") if isinstance(value, dict) else None,
        }

    run_check("agent_registration", f"/api/agents?authority={encoded}&page=1&pageSize=100", agents)
    run_check("owned_listings", f"/api/listings?wallet={encoded}&page=1&pageSize=100", listings)
    run_check("hireable_listings", f"/api/listings?wallet={encoded}&hireable=1&page=1&pageSize=100", hireable)
    run_check("storefront", f"/api/stores?wallet={encoded}&optional=1", store)

    checks = report["checks"]
    registration = checks.get("agent_registration", {})
    owned = checks.get("owned_listings", {})
    hireable_result = checks.get("hireable_listings", {})
    storefront = checks.get("storefront", {})
    report["readiness"] = {
        "worker_registered": registration.get("registered") is True,
        "provider_listing_exists": (owned.get("count", 0) or 0) > 0,
        "provider_listing_hireable": (hireable_result.get("count", 0) or 0) > 0,
        "storefront_registered": storefront.get("registered") is True,
    }
    if all(item["status"] == "ok" for item in checks.values()):
        if report["readiness"]["worker_registered"] and report["readiness"]["provider_listing_hireable"]:
            report["status"] = "PROVIDER_API_READY_REQUIRES_RUNTIME_AND_SIGNED_FLOW_TEST"
        elif report["readiness"]["worker_registered"]:
            report["status"] = "AGENT_REGISTERED_BUT_LISTING_NOT_HIREABLE"
        else:
            report["status"] = "REGISTRATION_OR_LISTING_PENDING"
    else:
        report["status"] = "INCOMPLETE_API_CHECK"
    report["note"] = (
        "A positive API result is only an indexer snapshot. It does not prove that "
        "the worker endpoint is publicly reachable, that a listing passes every "
        "moderation/runtime check, or that any settlement was received."
    )
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Read-only AgenC registration/listing readiness check")
    parser.add_argument("--wallet", default=os.getenv("AGENC_WALLET", ""),
                        help="Public Solana wallet; defaults to AGENC_WALLET")
    parser.add_argument("--out", default="output/agenc_readiness.json")
    args = parser.parse_args()
    if not args.wallet:
        report = {
            "provider": "AgenC",
            "status": "WALLET_NOT_CONFIGURED",
            "read_only": True,
            "transactions_signed": 0,
            "claims_made": 0,
            "payments_made": 0,
            "note": "Set AGENC_WALLET to the public wallet to query registration and listings. Never provide a private key or seed phrase.",
        }
        exit_code = 0
    else:
        try:
            report = inspect_wallet(args.wallet)
            exit_code = 0
        except (ReadinessError, ValueError) as exc:
            report = {
                "provider": "AgenC",
                "status": "READINESS_CHECK_FAILED",
                "error": str(exc),
                "read_only": True,
                "transactions_signed": 0,
                "claims_made": 0,
                "payments_made": 0,
            }
            exit_code = 0  # Reporting must not silently turn a public API outage into a deployment failure.
    import pathlib
    output = pathlib.Path(args.out)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    print(f"Read-only AgenC readiness report written to {output}")
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
