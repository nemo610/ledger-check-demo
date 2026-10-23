# AgentBazaar integration for Data Check

Status: integration branch only; registration has NOT been submitted. Public service deployment exists, but marketplace protocol and registration authentication remain unverified.

## Why this marketplace

The official AgentBazaar repository describes free registration, platform-paid Solana gas, USDC payments, and a push endpoint mode. However, its SKILLS.md raw-registration example conflicts with current API-reference docs that require wallet-signature headers. The exact push-job request/response contract is also not established by the docs reviewed. Therefore, no registration request will be sent by this integration until those points are resolved. No marketplace eligibility or revenue is guaranteed.

Official references:
- https://agentbazaar.dev/
- https://github.com/Agent-Bazaar/Agent-Bazaar
- https://raw.githubusercontent.com/Agent-Bazaar/Agent-Bazaar/main/SKILLS.md

## What this branch changes

- Keeps the existing POST /v1/validate API.
- Adds POST / as an AgentBazaar push webhook.
- The current webhook adapter expects JSON with a non-empty `task` string and `payload` containing `format` (`csv` or `json`), `content` (text), and optional `filename`. This is our proposed adapter contract, not yet verified against AgentBazaar's live push dispatcher.
- Returns a JSON object with `result` and `task_status`.
- Does not store uploaded content, sign transactions, or claim payment settlement is verified.
- Adds tests for the new webhook route.

Example task body (use synthetic, non-sensitive content only):

```json
{
  "task": "Validate this CSV",
  "payload": {
    "filename": "sample.csv",
    "format": "csv",
    "content": "id,name\n1,Ada\n"
  }
}
```

Expected response shape:

```json
{
  "result": {
    "service": "CSV/JSON Data Quality Check",
    "format": "csv",
    "valid": true,
    "stored": false,
    "settlement_verified": false
  },
  "task_status": "completed",
  "service": "Data Check"
}
```

## Safe onboarding steps

1. Deploy this branch as a separate Render web service or test environment. Do not change the existing AgenC service until the new service passes its tests.
2. Verify `GET /health` returns `marketplace_webhook: true`.
3. Run `python3 scripts/register_agentbazaar.py` for a read-only preflight. It never creates an account or wallet.
4. Resolve the official registration-authentication discrepancy and confirm the live push-dispatch schema with AgentBazaar support/docs.
5. Only then implement the verified registration flow. Do not paste wallet recovery phrases or private keys into ChatGPT, GitHub, or Render.
6. After a verified registration, submit a test task using synthetic content and independently verify delivery and payment before advertising the agent as commercially operational.

## Important security and status notes

- Never paste a seed phrase or private key into ChatGPT, GitHub, issue comments, or support messages.
- Never commit `credentials.json` or copy it into the repository.
- The registration helper is deliberately read-only; it cannot submit registration or create a wallet.
- The exact marketplace push payload has not yet been validated end-to-end.
- No registration, paid job, or settlement has been performed by this code change.
- The branch has not been deployed or production-tested as part of this commit.
