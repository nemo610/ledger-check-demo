"""First-party service billing proposals, separate from referral commissions.

This module is simulation-only: it never charges a customer or verifies settlement.
All policies are disabled by default and every output has settlement_verified=False.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Iterable


VALID_STATUSES = {"OBSERVED", "CONFIRMED", "SETTLED", "REVERSED"}


def _decimal(value: object, field: str) -> Decimal:
    try:
        result = Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"{field} must be a decimal number") from exc
    if not result.is_finite():
        raise ValueError(f"{field} must be finite")
    return result


@dataclass(frozen=True)
class ServiceBillingPolicy:
    policy_id: str
    service_id: str
    policy_version: str
    currency: str
    unit_price: str
    enabled: bool = False

    def validated_price(self) -> Decimal:
        price = _decimal(self.unit_price, "unit_price")
        if price <= 0:
            raise ValueError("unit_price must be > 0")
        if not self.policy_id.strip() or not self.service_id.strip() or not self.policy_version.strip():
            raise ValueError("policy_id, service_id, and policy_version are required")
        if not self.currency.strip():
            raise ValueError("currency is required")
        return price


@dataclass(frozen=True)
class ServiceUsageEvent:
    event_id: str
    service_id: str
    customer_agent_id: str
    provider_agent_id: str
    idempotency_key: str
    usage_units: str
    currency: str
    policy_version: str
    status: str
    source_reference: str = ""
    reverses_event_id: str = ""

    @classmethod
    def from_dict(cls, raw: dict) -> "ServiceUsageEvent":
        required = (
            "event_id", "service_id", "customer_agent_id", "provider_agent_id",
            "idempotency_key", "usage_units", "currency", "policy_version", "status",
        )
        missing = [key for key in required if not str(raw.get(key, "")).strip()]
        if missing:
            raise ValueError("Missing required fields: " + ", ".join(missing))
        units = _decimal(raw["usage_units"], "usage_units")
        if units <= 0:
            raise ValueError("usage_units must be > 0")
        status = str(raw["status"]).strip().upper()
        if status not in VALID_STATUSES:
            raise ValueError("status must be OBSERVED, CONFIRMED, SETTLED, or REVERSED")
        return cls(
            event_id=str(raw["event_id"]).strip(),
            service_id=str(raw["service_id"]).strip(),
            customer_agent_id=str(raw["customer_agent_id"]).strip(),
            provider_agent_id=str(raw["provider_agent_id"]).strip(),
            idempotency_key=str(raw["idempotency_key"]).strip(),
            usage_units=format(units, "f"),
            currency=str(raw["currency"]).strip().upper(),
            policy_version=str(raw["policy_version"]).strip(),
            status=status,
            source_reference=str(raw.get("source_reference", "")).strip(),
            reverses_event_id=str(raw.get("reverses_event_id", "")).strip(),
        )


def process_service_charges(events: Iterable[dict], policies: Iterable[dict]) -> list[dict]:
    """Return idempotent charge/reversal proposals; never execute a payment."""
    policy_list = [ServiceBillingPolicy(**item) for item in policies]
    by_key: dict[tuple[str, str], list[ServiceBillingPolicy]] = {}
    for policy in policy_list:
        policy.validated_price()
        key = (policy.service_id, policy.policy_version)
        by_key.setdefault(key, []).append(policy)

    results: list[dict] = []
    seen_ids: set[str] = set()
    seen_keys: set[str] = set()
    proposed_by_id: dict[str, dict] = {}
    reversed_ids: set[str] = set()

    for raw in events:
        event = ServiceUsageEvent.from_dict(raw)
        base = {
            "event_type": "first_party_service_charge",
            "event_id": event.event_id,
            "service_id": event.service_id,
            "customer_agent_id": event.customer_agent_id,
            "provider_agent_id": event.provider_agent_id,
            "idempotency_key": event.idempotency_key,
            "usage_units": event.usage_units,
            "currency": event.currency,
            "policy_version": event.policy_version,
            "source_status": event.status,
            "source_reference": event.source_reference,
            "reverses_event_id": event.reverses_event_id or None,
            "amount": "0.00",
            "status": "NOT_ELIGIBLE",
            "settlement_verified": False,
        }
        if event.event_id in seen_ids:
            base["status"] = "DUPLICATE_EVENT_ID"
            results.append(base)
            continue
        seen_ids.add(event.event_id)
        if event.idempotency_key in seen_keys:
            base["status"] = "DUPLICATE_IDEMPOTENCY_KEY"
            results.append(base)
            continue
        seen_keys.add(event.idempotency_key)

        if event.customer_agent_id == event.provider_agent_id:
            base["status"] = "SELF_CHARGE_REJECTED"
            results.append(base)
            continue

        matches = by_key.get((event.service_id, event.policy_version), [])
        if len(matches) == 0:
            base["status"] = "NO_POLICY"
            results.append(base)
            continue
        if len(matches) != 1:
            base["status"] = "AMBIGUOUS_POLICY"
            results.append(base)
            continue
        policy = matches[0]
        if event.currency != policy.currency.upper():
            base["status"] = "CURRENCY_MISMATCH"
            results.append(base)
            continue
        if not policy.enabled:
            base["status"] = "POLICY_DISABLED"
            results.append(base)
            continue

        if event.status == "REVERSED":
            original = proposed_by_id.get(event.reverses_event_id)
            if not event.reverses_event_id or original is None:
                base["status"] = "INVALID_REVERSAL_REFERENCE"
                results.append(base)
                continue
            if event.reverses_event_id in reversed_ids:
                base["status"] = "DUPLICATE_REVERSAL"
                results.append(base)
                continue
            if (original["service_id"] != event.service_id
                    or original["customer_agent_id"] != event.customer_agent_id
                    or original["provider_agent_id"] != event.provider_agent_id
                    or original["status"] != "PROPOSED"):
                base["status"] = "REVERSAL_MISMATCH"
                results.append(base)
                continue
            base["event_type"] = "first_party_service_reversal"
            base["amount"] = str(-Decimal(original["amount"]))
            base["status"] = "REVERSAL_PROPOSED"
            reversed_ids.add(event.reverses_event_id)
            results.append(base)
            continue

        if event.status not in {"CONFIRMED", "SETTLED"}:
            base["status"] = "USAGE_NOT_CONFIRMED"
            results.append(base)
            continue

        amount = (policy.validated_price() * Decimal(event.usage_units)).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        if amount <= 0:
            base["status"] = "INVALID_AMOUNT"
            results.append(base)
            continue
        base["amount"] = str(amount)
        base["status"] = "PROPOSED"
        results.append(base)
        proposed_by_id[event.event_id] = base

    return results
