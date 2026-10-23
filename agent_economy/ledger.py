"""Deterministic commission ledger for agent-to-agent service events.

This module only records and calculates proposed fees. It does not move money,
claim external settlement, or treat unverified events as paid.
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class ServiceEvent:
    event_id: str
    provider_id: str
    payer_agent_id: str
    provider_agent_id: str
    gross_amount: str
    currency: str
    status: str
    source_reference: str = ""

    @classmethod
    def from_dict(cls, raw: dict) -> "ServiceEvent":
        required = ("event_id", "provider_id", "payer_agent_id", "provider_agent_id",
                    "gross_amount", "currency", "status")
        missing = [key for key in required if not str(raw.get(key, "")).strip()]
        if missing:
            raise ValueError("Missing required fields: " + ", ".join(missing))
        try:
            amount = Decimal(str(raw["gross_amount"]))
        except InvalidOperation as exc:
            raise ValueError("gross_amount must be a decimal number") from exc
        if not amount.is_finite() or amount < 0:
            raise ValueError("gross_amount must be finite and >= 0")
        status = str(raw["status"]).upper()
        if status not in {"OBSERVED", "CONFIRMED", "SETTLED", "REVERSED"}:
            raise ValueError("status must be OBSERVED, CONFIRMED, SETTLED, or REVERSED")
        return cls(
            event_id=str(raw["event_id"]).strip(),
            provider_id=str(raw["provider_id"]).strip(),
            payer_agent_id=str(raw["payer_agent_id"]).strip(),
            provider_agent_id=str(raw["provider_agent_id"]).strip(),
            gross_amount=format(amount, "f"),
            currency=str(raw["currency"]).strip().upper(),
            status=status,
            source_reference=str(raw.get("source_reference", "")).strip(),
        )


@dataclass(frozen=True)
class FeePolicy:
    policy_id: str
    provider_id: str
    rate: str
    currency: str
    enabled: bool = False
    evidence_url: str = ""
    notes: str = ""

    def validated_rate(self) -> Decimal:
        try:
            rate = Decimal(self.rate)
        except InvalidOperation as exc:
            raise ValueError(f"Invalid rate for {self.policy_id}") from exc
        if not rate.is_finite() or rate < 0 or rate > 1:
            raise ValueError("Fee rate must be between 0 and 1")
        return rate


def calculate_commission(event: ServiceEvent, policy: FeePolicy) -> dict:
    """Calculate a proposal; only confirmed/settled source events are eligible."""
    rate = policy.validated_rate()
    gross = Decimal(event.gross_amount)
    eligible = (
        policy.enabled
        and event.provider_id == policy.provider_id
        and event.currency == policy.currency.upper()
        and event.status in {"CONFIRMED", "SETTLED"}
        and event.payer_agent_id != event.provider_agent_id
    )
    fee = (gross * rate).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP) if eligible else Decimal("0.00")
    return {
        "event_id": event.event_id,
        "provider_id": event.provider_id,
        "payer_agent_id": event.payer_agent_id,
        "provider_agent_id": event.provider_agent_id,
        "gross_amount": event.gross_amount,
        "currency": event.currency,
        "source_status": event.status,
        "policy_id": policy.policy_id,
        "rate": str(rate),
        "commission_amount": str(fee),
        "commission_status": "PROPOSED" if eligible and fee > 0 else "NOT_ELIGIBLE",
        "settlement_verified": False,
        "source_reference": event.source_reference,
    }


def process_events(events: Iterable[dict], policies: Iterable[dict]) -> list[dict]:
    """Process unique events idempotently; ambiguous policies fail closed."""
    policy_list = [FeePolicy(**p) for p in policies]
    by_provider: dict[str, list[FeePolicy]] = {}
    for policy in policy_list:
        policy.validated_rate()
        by_provider.setdefault(policy.provider_id, []).append(policy)
    results, seen = [], set()
    for raw in events:
        event = ServiceEvent.from_dict(raw)
        if event.event_id in seen:
            continue
        seen.add(event.event_id)
        matches = by_provider.get(event.provider_id, [])
        if len(matches) != 1:
            results.append({
                "event_id": event.event_id, "provider_id": event.provider_id,
                "commission_amount": "0.00", "currency": event.currency,
                "commission_status": "NO_POLICY" if not matches else "AMBIGUOUS_POLICY",
                "settlement_verified": False,
            })
            continue
        results.append(calculate_commission(event, matches[0]))
    return results


def read_json(path: str | Path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_json(path: str | Path, data) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
