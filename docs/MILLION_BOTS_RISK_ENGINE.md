# Million logical bots connected to RiskEngine

## What this delivers
- A stable namespace of up to 1,000,000 **logical bot identities**, generated lazily in O(1) memory.
- Each candidate order is passed to the existing `RiskEngine.evaluar_orden(...)` interface.
- Bounded evaluation batches (maximum 10,000 proposals per call) for later worker orchestration.
- Risk decisions are returned for audit; no order is submitted.

## What it does not deliver
This is not one million deployed processes, accounts, marketplace identities, or revenue streams. It does not create wallets, call providers, place trades, execute payments, or promise income. Live execution is hard-disabled in this prototype.

## Integration
Import `iter_bot_specs` to page through stable logical identities. Pass an initialized instance of the project's `RiskEngine` into `evaluate_candidate` or `evaluate_batch`. Candidate fields follow the current engine interface:
- Required: `precio_actual`, `capital_disponible`
- Optional: `regla_sizing`, `volatilidad_anual`, `condicion_macro`, `drawdown_actual`, `fecha`

Use isolated, bounded workers and separate engine instances when processing large volumes; do not share one mutable engine across concurrent workers because it maintains decision logs. Run the project's tests before deployment. No financial or production readiness is implied.
