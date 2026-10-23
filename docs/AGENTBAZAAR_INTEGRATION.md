# AgentBazaar integration for Data Check

Status: worker implementation is on the integration branch. A new free Render service `data-check-agentbazaar-gateway` installs the official SDK and is under deployment verification. Registration has NOT been submitted, and marketplace account/settlement are not verified.

## Why this marketplace

The official AgentBazaar repository describes free registration, platform-paid Solana gas, USDC payments, and Gateway Protocol v1 over WebSocket. The registration guide and API reference require wallet-signature headers, while SKILLS.md also includes a raw-registration example without them. We will not guess which path the live service accepts or generate a wallet recovery phrase that cannot be safely delivered to the owner. No marketplace eligibility or revenue is guaranteed.

Official references:
- https://agentbazaar.dev/
- https://github.com/Agent-Bazaar/Agent-Bazaar
- https://raw.githubusercontent.com/Agent-Bazaar/Agent-Bazaar/main/SKILLS.md

## What this branch changes

- Keeps the existing POST /v1/validate API.
- Keeps POST / as a generic HTTP test adapter, but it is not claimed to match AgentBazaar's live dispatch contract.
- Adds `agent_economy/agentbazaar_worker.py`, which uses the official `agentsbazaar-worker` Gateway Protocol SDK to accept structured jobs and return validation results.
- The worker accepts only `filename`, `format` (`csv` or `json`), and `content`; it rejects extra fields, URLs, and unstructured payloads. It never executes task instructions or stores file contents.
- When `AGENTBAZAAR_TOKEN` is configured, the web service starts the Gateway worker in a background thread. Without the token, the worker stays disabled and the HTTP API still runs.
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

1. Verify the GitHub Actions result for both worker unit tests and the HTTPS smoke test.
2. Use `https://data-check-agentbazaar-gateway.onrender.com` for the SDK-enabled test service. It installs `requirements.txt`; the older `data-check-agentbazaar.onrender.com` service is only the initial HTTP adapter test.
3. Complete registration using the official supported wallet-signature flow, and deliver/store any generated recovery phrase securely in the owner's own password manager. Do not send it through ChatGPT, GitHub, or logs.
4. Set `AGENTBAZAAR_TOKEN` as a Render secret only after registration is completed and the token can be handled safely.
5. After the worker logs a successful Gateway `READY`, submit a test task using synthetic content and independently verify delivery and payment before advertising the agent as commercially operational.

## Important security and status notes

- Never paste a seed phrase or private key into ChatGPT, GitHub, issue comments, or support messages.
- Never commit `credentials.json` or copy it into the repository.
- The registration helper is deliberately read-only; it cannot submit registration or create a wallet.
- The WebSocket worker code is implemented and unit-tested, but is not connected because no marketplace token is configured.
- No registration, paid job, or settlement has been performed.
- The initial live HTTP adapter smoke test passed. The SDK-enabled service still needs its own smoke test and worker activation; neither result proves payment settlement.
