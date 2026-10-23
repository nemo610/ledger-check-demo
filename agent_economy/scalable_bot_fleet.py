"""Lazy, fail-closed fleet of logical bots wired to RiskEngine.

A million logical bot identities do not mean a million deployed workers.
This module creates no accounts, threads, API traffic, trades, or payments.
Each proposed order must pass through the supplied RiskEngine instance.
"""
from __future__ import annotations

from dataclasses import dataclass
from itertools import islice
from typing import Any, Iterable, Iterator, Mapping

DEFAULT_FLEET_SIZE = 1_000_000
MAX_FLEET_SIZE = 1_000_000
MAX_BATCH_SIZE = 10_000

SIZING_RULES = (
    "BASE_50",
    "SIZING_VOLATILIDAD",
    "MACRO_USO",
    "PERFIL_CONSERVADOR",
    "PERFIL_EQUILIBRADO",
    "PERFIL_CRECIMIENTO",
)


@dataclass(frozen=True)
class BotSpec:
    bot_id: str
    ordinal: int
    sizing_rule: str
    live_execution_enabled: bool = False


def iter_bot_specs(
    count: int = DEFAULT_FLEET_SIZE, *, start: int = 0
) -> Iterator[BotSpec]:
    """Yield stable logical bot specs lazily; memory usage is O(1)."""
    if isinstance(count, bool) or not isinstance(count, int) or not 1 <= count <= MAX_FLEET_SIZE:
        raise ValueError(f"count must be an integer from 1 to {MAX_FLEET_SIZE}")
    if isinstance(start, bool) or not isinstance(start, int) or start < 0 or start + count > MAX_FLEET_SIZE:
        raise ValueError("start must be non-negative and start + count must not exceed fleet limit")
    for ordinal in range(start, start + count):
        yield BotSpec(
            bot_id=f"nemo-risk-bot-{ordinal + 1:07d}",
            ordinal=ordinal,
            sizing_rule=SIZING_RULES[ordinal % len(SIZING_RULES)],
        )


def evaluate_candidate(
    engine: Any, bot: BotSpec, candidate: Mapping[str, Any]
) -> dict[str, Any]:
    """Ask the project's RiskEngine to approve/reject one candidate order.

    Required candidate keys: precio_actual, capital_disponible.
    Optional keys mirror RiskEngine.evaluar_orden. This only returns a risk
    decision; it never submits an order or enables live execution.
    """
    if bot.live_execution_enabled:
        raise ValueError("live execution is prohibited by this prototype")
    if not isinstance(candidate, Mapping):
        raise ValueError("candidate must be a mapping")
    required = ("precio_actual", "capital_disponible")
    missing = [key for key in required if key not in candidate]
    if missing:
        raise ValueError(f"missing candidate fields: {', '.join(missing)}")

    decision = engine.evaluar_orden(
        precio_actual=candidate["precio_actual"],
        capital_disponible=candidate["capital_disponible"],
        regla_sizing=candidate.get("regla_sizing", bot.sizing_rule),
        volatilidad_anual=candidate.get("volatilidad_anual"),
        condicion_macro=candidate.get("condicion_macro", False),
        drawdown_actual=candidate.get("drawdown_actual", 0.0),
        fecha=candidate.get("fecha"),
    )
    if not isinstance(decision, dict) or "aprobada" not in decision:
        raise TypeError("RiskEngine returned an invalid decision schema")
    return {
        "bot_id": bot.bot_id,
        "risk_decision": decision,
        "order_submitted": False,
        "live_execution_enabled": False,
    }


def evaluate_batch(
    engine: Any,
    candidates: Iterable[Mapping[str, Any]],
    *,
    start: int = 0,
    max_items: int = MAX_BATCH_SIZE,
) -> list[dict[str, Any]]:
    """Evaluate at most 10,000 candidates; caller controls worker scheduling."""
    if isinstance(max_items, bool) or not isinstance(max_items, int) or not 1 <= max_items <= MAX_BATCH_SIZE:
        raise ValueError(f"max_items must be an integer from 1 to {MAX_BATCH_SIZE}")
    bots = iter_bot_specs(count=max_items, start=start)
    results = []
    for bot, candidate in zip(bots, islice(candidates, max_items)):
        results.append(evaluate_candidate(engine, bot, candidate))
    return results
