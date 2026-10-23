# AgentBazaar integration for Data Check

Status: integration branch only; registration has NOT been submitted.

## Why this marketplace

The official AgentBazaar project documents free registration, platform-paid Solana gas, USDC settlement, and a push endpoint mode. This is a better fit for a no-upfront-SOL trial than the AgenC registration path. Marketplace claims and future revenue are not guarantees; this repository does not claim that an agent is registered or that settlement has been verified.

Official references:
- https://agentbazaar.dev/
- https://github.com/Agent-Bazaar/Agent-Bazaar
- https://raw.githubusercontent.com/Agent-Bazaar/Agent-Bazaar/main/SKILLS.md

## What this branch changes

- Keeps the existing POST /v1/validate API.
- Adds POST / as an AgentBazaar push webhook.
- The webhook expects JSON with a non-empty `task` string and `payload` containing `format` (`csv` or `json`), `content` (text), and optional `filename`.
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
3. Run `python3 scripts/register_agentbazaar.py --endpoint https://YOUR-NEW-SERVICE.onrender.com` for a preflight only. This does not register anything.
4. Review the price. The helper defaults to 0.10 USDC per request; change it explicitly if desired.
5. When ready, run the helper again with `--register` and type `REGISTER` at the prompt.
6. The official registration endpoint may return an API token and a wallet recovery phrase. The helper writes the response to `~/.config/data-check-agentbazaar/credentials.json` with restrictive local permissions and never prints the secrets. Back up the recovery phrase securely. Never commit or upload this file.
7. Submit a test task using synthetic content and verify delivery and payment independently before advertising the agent as commercially operational.

## Important security and status notes

- Never paste a seed phrase or private key into ChatGPT, GitHub, issue comments, or support messages.
- Never commit `credentials.json` or copy it into the repository.
- The registration helper is opt-in and will not submit registration unless `--register` is passed and the user types `REGISTER`.
- If the helper reports that the endpoint is not ready, it exits before registration.
- No registration, paid job, or settlement has been performed by this code change.
- The branch has not been deployed or production-tested as part of this commit.
