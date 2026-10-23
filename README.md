# Agent-to-Agent Monetization Prototype

This repository currently contains an isolated experimental implementation of a commission ledger for automated service/agent marketplaces. The new implementation is in branch `agent-to-agent-monetization-v1`; the `main` branch has not been changed by this work.

## What it does
- Validates structured task/commission events.
- Deduplicates event IDs to prevent replay-based double counting.
- Calculates proposed commissions with decimal arithmetic.
- Requires an explicitly enabled fee policy and a confirmed source event.
- Emits audit-friendly JSON; never executes payments or claims settlement is verified.

## Run locally

```bash
python -m unittest discover -s tests -v
python -m agent_economy.cli
```

The sample policy is disabled, and all example events are synthetic. See [docs/AGENT_TO_AGENT_MONETIZATION.md](docs/AGENT_TO_AGENT_MONETIZATION.md) for the current opportunity shortlist, evidence, caveats, and next steps.

## Important
No live provider has been connected, no affiliate/program account has been approved, no settlement webhook is verified, and no revenue has been generated. Do not enable a policy until the provider's current terms and event contract have been validated.
