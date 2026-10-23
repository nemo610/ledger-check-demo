"""Read-only adapter for AgenC's public settled-earnings explorer.

This adapter never signs transactions or moves funds. It fetches earnings
reported for an explicitly supplied Solana wallet and preserves provider
payloads for reconciliation; the provider remains the source of truth.
"""
from __future__ import annotations

import json
import re
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

API_BASE = "https://api.agenc.ag/api/explorer"
_BASE58_WALLET = re.compile(r"^[1-9A-HJ-NP-Za-km-z]{32,44}$")


class AgenCAPIError(RuntimeError):
    """The provider API could not supply a trustworthy response."""


def _validate_payload(payload: object) -> dict:
    """Validate the response shape even when the transport is mocked/replaced."""
    if not isinstance(payload, dict) or payload.get("live") is not True:
        raise AgenCAPIError("AgenC response is not marked live; earnings remain unverified")
    if not isinstance(payload.get("hires"), list):
        raise AgenCAPIError("AgenC response has no valid hires list")
    return payload


def _get_json(url: str, timeout: float = 10.0) -> dict:
    request = Request(url, headers={"Accept": "application/json", "User-Agent": "agent-economy-adapter/0.1"})
    try:
        with urlopen(request, timeout=timeout) as response:
            if response.status != 200:
                raise AgenCAPIError(f"AgenC API returned HTTP {response.status}")
            payload = json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError, TimeoutError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise AgenCAPIError(f"Unable to read AgenC earnings API: {exc}") from exc
    return _validate_payload(payload)


def fetch_settled_earnings(wallet: str, *, timeout: float = 10.0) -> dict:
    """Fetch operator and referrer earnings for a Solana wallet, read-only.

    A valid wallet is required; a bank-transfer alias is not a wallet address.
    Empty hires lists are valid and mean no earnings were returned by the API.
    """
    wallet = str(wallet).strip()
    if not _BASE58_WALLET.fullmatch(wallet):
        raise ValueError("wallet must be a valid-looking Solana base58 address (not a bank-transfer alias)")
    encoded = quote(wallet, safe="")
    referrer_url = f"{API_BASE}/referrers/{encoded}/hires"
    operator_url = f"{API_BASE}/operators/{encoded}/hires"
    referrer = _validate_payload(_get_json(referrer_url, timeout=timeout))
    operator = _validate_payload(_get_json(operator_url, timeout=timeout))
    return {
        "provider": "agenc",
        "wallet": wallet,
        "mode": "read_only",
        "settlement_verified": False,
        "referrer": {"endpoint": referrer_url, "hires": referrer["hires"]},
        "operator": {"endpoint": operator_url, "hires": operator["hires"]},
        "note": "Provider-reported earnings only; independently reconcile on-chain receipts before marking funds received.",
    }
