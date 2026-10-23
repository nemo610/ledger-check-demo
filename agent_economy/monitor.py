"""One-shot, read-only AgenC earnings monitor for scheduled runtimes.

This process never claims work, signs transactions, or moves funds. It reports
provider-reported hire counts only; those counts are not proof of settlement.
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone

from .agenc_adapter import AgenCAPIError, fetch_settled_earnings


def main() -> int:
    wallet = os.environ.get("AGENC_WALLET", "").strip()
    if not wallet:
        print("ERROR: set the public Solana address in AGENC_WALLET; never use a seed/private key.", file=sys.stderr)
        return 2

    try:
        snapshot = fetch_settled_earnings(wallet)
    except (AgenCAPIError, ValueError) as exc:
        print(json.dumps({
            "provider": "agenc",
            "checked_at_utc": datetime.now(timezone.utc).isoformat(),
            "status": "error",
            "error_type": type(exc).__name__,
            "message": str(exc),
        }, ensure_ascii=False), file=sys.stderr)
        return 1

    print(json.dumps({
        "provider": "agenc",
        "checked_at_utc": datetime.now(timezone.utc).isoformat(),
        "wallet_suffix": wallet[-6:],
        "status": "ok",
        "mode": "read_only",
        "referrer_hires_reported": len(snapshot["referrer"]["hires"]),
        "operator_hires_reported": len(snapshot["operator"]["hires"]),
        "settlement_verified": False,
        "note": "Provider-reported counts only; reconcile on-chain before treating funds as received.",
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
