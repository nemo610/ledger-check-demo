#!/usr/bin/env python3
"""Safely register Data Check with AgentBazaar after the webhook is deployed.

This script is intentionally opt-in: pass --register and type REGISTER.
Secrets returned by the platform are written locally with mode 0600 and are
never printed or committed to Git.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

API_BASE = "https://agentbazaar.dev"
DEFAULT_ENDPOINT = "https://data-check-agentbazaar.onrender.com"

def request_json(url: str, *, data: dict | None = None, timeout: int = 20) -> dict:
    headers = {"Accept": "application/json", "User-Agent": "data-check-agentbazaar-onboarding/1.0"}
    body = None
    if data is not None:
        headers["Content-Type"] = "application/json"
        body = json.dumps(data).encode("utf-8")
    req = urllib.request.Request(url, data=body, headers=headers, method="POST" if body is not None else "GET")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            parsed = json.loads(response.read().decode("utf-8"))
            if not isinstance(parsed, dict):
                raise RuntimeError("Unexpected non-object JSON response.")
            return parsed
    except urllib.error.HTTPError as exc:
        detail = exc.read(1000).decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {exc.code} from {url}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Could not reach {url}: {exc.reason}") from exc

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--endpoint", default=DEFAULT_ENDPOINT, help="Public HTTPS webhook endpoint; its root POST route must support AgentBazaar tasks.")
    parser.add_argument("--name", default="Data Check", help="Agent display name.")
    parser.add_argument("--price-usdc", type=float, default=0.10, help="Price per request in USDC (default: 0.10).")
    parser.add_argument("--register", action="store_true", help="Actually submit the registration. Without this flag, only preflight checks run.")
    args = parser.parse_args()

    if not args.endpoint.startswith("https://"):
        print("ERROR: the endpoint must use HTTPS.", file=sys.stderr)
        return 2
    if not (0 <= args.price_usdc <= 1000):
        print("ERROR: price must be between 0 and 1000 USDC.", file=sys.stderr)
        return 2

    print("Checking the deployed webhook before registration...")
    try:
        health = request_json(args.endpoint.rstrip("/") + "/health")
    except Exception as exc:
        print(f"ERROR: webhook health check failed: {exc}", file=sys.stderr)
        return 2
    if health.get("marketplace_webhook") is not True:
        print("BLOCKED: this deployment does not advertise marketplace_webhook=true.")
        print("Deploy and test branch agentbazaar-integration-v1 first; no account was created.")
        return 2

    if not args.register:
        print("Preflight OK. No account has been created.")
        print(f"Endpoint: {args.endpoint}")
        print(f"Planned price: {args.price_usdc:.2f} USDC per request")
        print("To create the account after reviewing the endpoint, rerun with --register.")
        return 0

    print("This will create an AgentBazaar agent and a wallet. The platform may return a recovery phrase.")
    print("The script stores the response locally; never upload that file or share the phrase.")
    if input("Type REGISTER to continue: ").strip() != "REGISTER":
        print("Cancelled. No registration request sent.")
        return 1

    micro_usdc = round(args.price_usdc * 1_000_000)
    payload = {
        "name": args.name,
        "skills": "csv-validation,json-validation,data-quality",
        "description": "Validates CSV and JSON text for syntax and common structural issues. Does not store submitted content.",
        "pricePerRequest": micro_usdc,
        "deliveryMode": "push",
        "endpoint": args.endpoint.rstrip("/") + "/",
        "ownerGithub": "nemo610",
    }
    try:
        result = request_json(API_BASE + "/agents/register", data=payload, timeout=30)
    except Exception as exc:
        print(f"ERROR: registration failed: {exc}", file=sys.stderr)
        return 2

    agent = result.get("agent") if isinstance(result.get("agent"), dict) else {}
    if not agent or not result.get("apiToken"):
        print("ERROR: response did not contain the expected agent and apiToken fields.")
        print("No credentials were saved. Check the official docs and response format.")
        return 2

    config_dir = Path.home() / ".config" / "data-check-agentbazaar"
    config_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
    try:
        config_dir.chmod(0o700)
    except OSError:
        pass
    output = config_dir / "credentials.json"
    if output.exists():
        print(f"ERROR: {output} already exists. Refusing to overwrite credentials.", file=sys.stderr)
        print("Contact platform support to check whether registration succeeded before retrying.", file=sys.stderr)
        return 3
    temp = output.with_suffix(".json.tmp")
    temp.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.chmod(temp, 0o600)
    temp.replace(output)
    os.chmod(output, 0o600)

    print("Registration response saved securely on this computer.")
    print(f"Credentials file: {output}")
    print(f"Agent profile: {agent.get('profile', '(not supplied)')}")
    print(f"Agent authority: {agent.get('authority', '(not supplied)')}")
    print("Do not paste credentials.json, apiToken, or recoveryPhrase into ChatGPT, GitHub, or Render logs.")
    print("Back up the recovery phrase securely before using the wallet.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
