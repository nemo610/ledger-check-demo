"""CLI for the agent-to-agent commission prototype."""
from __future__ import annotations
import argparse
from .ledger import process_events, read_json, write_json


def main() -> None:
    parser = argparse.ArgumentParser(description="Calculate proposed agent-to-agent commissions; never sends payments.")
    parser.add_argument("--events", default="data/agent_events.example.json")
    parser.add_argument("--policies", default="data/fee_policies.example.json")
    parser.add_argument("--out", default="output/commission_proposals.json")
    args = parser.parse_args()
    result = process_events(read_json(args.events), read_json(args.policies))
    write_json(args.out, result)
    print(f"Processed {len(result)} unique events -> {args.out}")
    print("NOTICE: proposals only; external attribution and settlement have not been verified.")


if __name__ == "__main__":
    main()
