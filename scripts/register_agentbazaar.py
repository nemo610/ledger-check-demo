#!/usr/bin/env python3
"""Read-only preflight for the Data Check AgentBazaar webhook.

Registration is intentionally not implemented here: current official
AgentBazaar documentation conflicts on whether registration requires wallet
signature authentication. Do not send a registration request until that is
resolved through the official onboarding flow.
"""
from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request

DEFAULT_ENDPOINT = "https://data-check-agentbazaar.onrender.com"


def main() -> int:
    endpoint = DEFAULT_ENDPOINT.rstrip("/")
    request = urllib.request.Request(
        endpoint + "/health",
        headers={"Accept": "application/json", "User-Agent": "data-check-preflight/1.0"},
        method="GET",
    )
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            health = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, ValueError) as exc:
        print(f"PRECHECK FAILED: {exc}", file=sys.stderr)
        return 2

    if not isinstance(health, dict) or health.get("marketplace_webhook") is not True:
        print("PRECHECK FAILED: endpoint does not report marketplace_webhook=true.", file=sys.stderr)
        return 2

    print("PRECHECK PASSED: HTTPS health endpoint advertises marketplace webhook support.")
    print(f"Endpoint: {endpoint}")
    print("Registration NOT submitted. No account, wallet, or credentials were created.")
    print("Next blocker: confirm the current official registration authentication and push-job payload.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
