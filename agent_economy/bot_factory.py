"""Scalable registry for commission-focused agent bots.

This creates logical bot configurations, not fake marketplace accounts or
independent revenue sources. Live activity stays disabled until a provider,
terms, attribution, and settlement evidence have been independently verified.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
from pathlib import Path


@dataclass(frozen=True)
class BotArchetype:
    role: str
    purpose: str
    required_evidence: tuple[str, ...]


ARCHETYPES: tuple[BotArchetype, ...] = (
    BotArchetype("opportunity_scout", "Find eligible third-party services and commission programs.", ("official_terms", "program_approval")),
    BotArchetype("referral_router", "Route a genuine buyer to an eligible provider with disclosed attribution.", ("official_terms", "program_approval", "attribution_contract")),
    BotArchetype("conversion_verifier", "Verify provider-confirmed conversions and reject self-reported claims.", ("authenticated_event_source", "deduplication")),
    BotArchetype("commission_auditor", "Calculate expected commissions and detect duplicates, reversals, and mismatches.", ("official_fee_schedule", "source_event", "idempotency")),
    BotArchetype("settlement_reconciler", "Reconcile provider records against independent payment or on-chain evidence.", ("provider_settlement_record", "independent_receipt_evidence")),
)


def build_registry(count: int = 12000) -> dict:
    """Build logical bot slots; live execution is never enabled by this registry."""
    if isinstance(count, bool) or not isinstance(count, int) or not 1 <= count <= 12000:
        raise ValueError("count must be an integer between 1 and 12000")

    bots = []
    for index in range(1, count + 1):
        archetype = ARCHETYPES[(index - 1) % len(ARCHETYPES)]
        bots.append({
            "bot_id": f"commission-bot-{index:05d}",
            "role": archetype.role,
            "purpose": archetype.purpose,
            "revenue_model": "third_party_commission",
            "provider": None,
            "required_evidence": list(archetype.required_evidence),
            "status": "blocked_no_verified_provider",
            "live_execution_enabled": False,
        })

    return {
        "schema_version": 1,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "requested_bot_slots": count,
        "unique_archetypes": len(ARCHETYPES),
        "revenue_claim": "none",
        "live_execution_enabled": False,
        "safety_note": (
            "These are logical configurations, not deployed workers or guaranteed income. "
            "Do not create fake accounts, spam, self-refer, or bypass provider rules."
        ),
        "bots": bots,
    }


def write_registry(path: str, count: int = 12000) -> dict:
    registry = build_registry(count=count)
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(registry, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return registry


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Generate up to 12,000 logical commission-bot slots.")
    parser.add_argument("--count", type=int, default=12000, help="Logical bot slots, 1–12000 (default: 12000).")
    parser.add_argument("--out", default="output/bot_registry.json", help="Output JSON path.")
    args = parser.parse_args()
    result = write_registry(args.out, args.count)
    print(f"Generated {result['requested_bot_slots']} logical bot slots -> {args.out}")
    print("Live execution: disabled; revenue: unverified/none.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
