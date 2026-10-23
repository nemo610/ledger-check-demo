"""CLI for the agent-to-agent commission prototype."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone

from .ledger import process_events, read_json, write_json


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Calculate proposed agent-to-agent commissions; never sends payments."
    )
    parser.add_argument("--events", default="data/agent_events.example.json")
    parser.add_argument("--policies", default="data/fee_policies.example.json")
    parser.add_argument("--out", default="output/commission_proposals.json")
    parser.add_argument(
        "--agenc-wallet",
        help="Optional public Solana wallet address for a read-only AgenC earnings query.",
    )
    parser.add_argument(
        "--agenc-out",
        default="output/agenc_earnings_snapshot.json",
        help="Output JSON path for the provider-reported AgenC snapshot.",
    )
    args = parser.parse_args()

    result = process_events(read_json(args.events), read_json(args.policies))
    write_json(args.out, result)
    print(f"Processed {len(result)} unique events -> {args.out}")
    print("NOTICE: proposals only; external attribution and settlement have not been verified.")

    if args.agenc_wallet:
        # Import only when requested; normal demo usage does not call external services.
        from .agenc_adapter import AgenCAPIError, fetch_settled_earnings

        try:
            snapshot = fetch_settled_earnings(args.agenc_wallet)
        except (AgenCAPIError, ValueError) as exc:
            parser.error(f"AgenC read-only query failed: {exc}")
        snapshot["queried_at_utc"] = datetime.now(timezone.utc).isoformat()
        write_json(args.agenc_out, snapshot)
        referrer_count = len(snapshot["referrer"]["hires"])
        operator_count = len(snapshot["operator"]["hires"])
        print(f"AgenC provider snapshot -> {args.agenc_out}")
        print(f"Provider-reported hires: referrer={referrer_count}, operator={operator_count}")
        print("NOTICE: this is not proof of on-chain receipt; settlement_verified=false.")


if __name__ == "__main__":
    main()
