# Agent-to-agent monetization: implementation plan and evidence ledger

## What is implemented in this branch

A dependency-free Python prototype that ingests structured service events, validates their fields, deduplicates event IDs, applies explicitly enabled fee policies, calculates fees using Decimal arithmetic, and emits proposals. It never initiates a transfer. Every output sets `settlement_verified=false`; sample data is synthetic.

Run:

```bash
python -m unittest discover -s tests -v
python -m agent_economy.cli --events data/agent_events.example.json --policies data/fee_policies.example.json
```

The sample policy is deliberately disabled. Its 5% rate is only a test fixture, not a claimed marketplace rate.

## Opportunity shortlist — evidence versus assumptions

1. **Agenc** — its public marketplace-operator documentation describes service hires, an operator-fee leg at settlement, and a separate referrer-fee leg. This is the closest match to a true intermediary that earns a fee when one agent marketplace surface refers a buyer. Evidence: <https://agenc.ag/docs/launch-a-marketplace>. Next: verify current protocol repository, deployed program, fee caps, settlement event schema, security assumptions, and whether a no-cost test environment exists before writing an adapter. No live transactions are enabled here.
2. **AgentsAccess** — its public site describes an agent marketplace, REST API management, product sales, and native AA Credits. Evidence: <https://www.agentsaccess.ai/>. This is a candidate for agent-to-agent trade, but credits are not equivalent to withdrawable cash and beta/API terms must be checked. Do not model it as cash revenue.
3. **Dealwork** — its public API site describes AI-agent contracts, escrow, and a stated 3% fee on AI-to-AI contracts. Evidence: <https://api.dealwork.ai/>. This is a candidate only; API access, agent onboarding, payment/withdrawal mechanics, jurisdiction, and terms must be independently validated before an adapter can claim real revenue.
4. **Apify Affiliate Program** — official terms state 20% for the first three paid months, then 30% up to per-referral caps, subject to approval, attribution, thresholds, and restrictions. Evidence: <https://docs.apify.com/legal/affiliate-program-terms-and-conditions>. This is a secondary, conventional referral channel, not proof of bot-to-bot commissions. It should not be the core product unless approval and compliant attribution are obtained.

## Revenue rules

- No provider gets an enabled fee policy without documented terms, an approved account/integration, and a verified event source.
- A referral click or an agent's self-reported event is not a payable conversion.
- Only source-confirmed events can produce a commission proposal; settlement requires independent provider evidence.
- Event IDs are idempotency keys. Replays cannot create duplicate proposals.
- Self-referrals, unknown providers, unknown currencies, ambiguous policies, reversed events, and unconfirmed events fail closed.
- No API keys, paid services, wallets, or transactions are created or funded by this repository.

## Next engineering increments

1. Confirm the best provider (initially Agenc, with Dealwork as alternative) and obtain its canonical API/event contract.
2. Implement one read-only adapter for verified task/settlement events, with signature verification and replay protection.
3. Add provider-specific fee policy, currency handling, refunds/reversals, and reconciliation against source settlements.
4. Add a router that selects an external agent by capability, price, latency, and policy, without accepting tasks or moving funds until terms and auth are verified.
5. Run integration tests against a free test environment; only then propose live enablement.

## Explicit non-goals

No accounting firms, human-operated service business, spam, scraping, fake accounts, self-referrals, bypassing provider controls, automatic promotion, or claims of income. This is an implementation foundation, not a live earning bot yet.
