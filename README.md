# Agent-to-Agent Monetization Prototype

This repository currently contains an isolated experimental implementation of a commission ledger for automated service/agent marketplaces. The new implementation is in branch `agent-to-agent-monetization-v1`; the `main` branch has not been changed by this work.

## What it does
- Validates structured task/commission events.
- Deduplicates event IDs to prevent replay-based double counting.
- Calculates proposed referral commissions with decimal arithmetic.
- Calculates a separate, simulation-only proposal for first-party service usage and reversal events.
- Requires an explicitly enabled fee policy and a confirmed source event.
- Emits audit-friendly JSON; never executes payments or claims settlement is verified.

## Run locally

```bash
python -m unittest discover -s tests -v
python -m agent_economy.cli --help
```

The sample referral policy is disabled, and example events are synthetic. First-party billing is implemented as a separate proposal-only module; it has no commercial price default and does not charge customers. See [docs/AGENT_TO_AGENT_MONETIZATION.md](docs/AGENT_TO_AGENT_MONETIZATION.md), [docs/FACTURACION_SERVICIOS_PROPIOS_SIMULADA.md](docs/FACTURACION_SERVICIOS_PROPIOS_SIMULADA.md), and [docs/DOBLE_INGRESO_REFERIDOS_Y_SERVICIOS_PROPIOS_AR.md](docs/DOBLE_INGRESO_REFERIDOS_Y_SERVICIOS_PROPIOS_AR.md) for scope, evidence, caveats, and next steps.

## Important
No live provider has been connected, no affiliate/program account has been approved, no settlement webhook is verified, and no revenue has been generated. Do not enable a policy until the provider's current terms, event contract, source of usage evidence, and payment reconciliation have been validated. `settlement_verified=false` is not a temporary UI flag; it must only change after independent verification.
