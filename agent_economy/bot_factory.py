"""Scalable registry for commission-focused agent bots.

This creates logical bot configurations, not fake marketplace accounts or
independent revenue sources. Live activity stays disabled until a provider,
terms, attribution, and settlement evidence have been independently verified.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class BotArchetype:
    role: str
    purpose: str
    required_evidence: tuple[str, ...]


ARCHETYPES: tuple[BotArchetype, ...] = (
    BotArchetype(
        role="opportunity_scout",
        purpose="Find eligible third-party services and commission programs.",
        required_evidence=("official_terms", "program_approval"),
    ),
    BotArchetype(
        role="referral_router",
        purpose="Route a genuine buyer to an eligible provider with disclosed attribution.",
        required_evidence=("official_terms", "program_approval", "attribution_contract"),
    ),
    BotArchetype(
        role="conversion_verifier",
        purpose="Verify provider-confirmed conversions and reject self-reported claims.",
        required_evidence=("signed_or_authenticated_event_source", "deduplication"),
    ),
    BotArchetype(
        role="commission_auditor",
        purpose="Calculate expected commissions and detect duplicates, reversals, and mismatches.",
        required_evidence=("official_fee_schedule", "source_event", "idempotency"),
    ),
    BotArchetype(
        role="settlement_reconciler",
        purpose="Reconcile provider records against independent payment or on-chain evidence.",
        required_evidence=("provider_settlement_record", "independent_receipt_evidence"),
    ),
)


def build_registry(
    count: int = 1000,
    approved_providers: Iterable[str] = (),
    settlement_verified_providers: Iterable[str] = (),
) -> dict:
    """Build deterministic logical bot slots; never activates live execution."""
    if isinstance(count, bool) or not isinstance(count, int) or not 1 <= count <= 1000:
        raise ValueError("count must be an integer between 1 and 1000")

    approved = {p.strip().lower() for p in approved_providers if p and p.strip()}
    settled = {p.strip().lower() for p in settlement_verified_providers if p and p.strip()}
    bots = []
    for index in range(1, count + 1):
        archetype = ARCHETYPES[(index - 1) % len(ARCHETYPES)]
        # Provider assignment is intentionally absent until an actual integration
        # has been approved and configured; no imaginary income is projected.
        bots.append({
            "bot_id": f"commission-bot-{index:04d}",
            "role": archetype.role,
            "purpose": archetype.purpose,
            "revenue_model": "third_party_commission",
            "provider": None,
            "required_evidence": list(archetype.required_evidence),
            "status": "blocked_no_verified_provider",
            "live_execution_enabled": False,
            "approved_provider_count": len(approved),
            "settlement_verified_provider_count": len(approved & settled),
        })

    return {
        "schema_version": 1,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "requested_bot_slots": count,
        "unique_archetypes": len(ARCHETYPES),
        "revenue_claim": "none",
        "live_execution_enabled": False,
        "safety_note": (
            "Bot slots are configurations, not deployed workers or guaranteed income. "
            "Do not create fake accounts, spam, self-refer, or bypass provider rules."
        ),
        "bots": bots,
    }


def write_registry(path: str, count: int = 1000) -> dict:
    registry = build_registry(count=count)
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(registry, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return registry


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Generate commission-bot registry (safe, disabled by default).")
    parser.add_argument("--count", type=int, default=1000, help="Logical bot slots, 1–1000 (default: 1000).")
    parser.add_argument("--out", default="output/bot_registry.json", help="Output JSON path.")
    args = parser.parse_args()
    result = write_registry(args.out, args.count)
    print(f"Generated {result['requested_bot_slots']} logical bot slots -> {args.out}")
    print("Live execution: disabled; revenue: unverified/none.")
