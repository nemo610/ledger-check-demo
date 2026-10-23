# AgenC public endpoint foundation

This service is a minimal HTTPS endpoint suitable for checking that the agent's
published URL is reachable. It is not proof of on-chain registration and is not
a completed task worker.

## Routes

- `GET /` and `GET /manifest.json`: agent metadata and explicit capability flags.
- `GET /.well-known/agent.json`: same machine-readable manifest.
- `GET /health` and `GET /healthz`: process health.
- `GET /ready`: returns HTTP 503 until registration and signer policy are verified.

## Deploy on Render

Create a **Web Service** from this repository and branch
`agenc-endpoint-worker-foundation` with runtime Python, build command
`python -m compileall -q agent_economy`, start command
`python -m agent_economy.http_service`, and the Free plan to start. Render supplies
HTTPS and the `PORT` environment variable.

Optional non-secret environment variables:
- `AGENC_AGENT_NAME`
- `AGENC_AGENT_DESCRIPTION`
- `AGENC_PUBLIC_WALLET` (public address only; never a seed or private key)

## Explicitly not enabled

- No private-key storage or signer endpoint.
- No automatic registration, staking, claims, submissions, or transfers.
- No claim that a task was paid or settled.
- No secrets are required for the health endpoint.

Before live work: read the current AgenC protocol config; verify the live minimum
stake; review task requirements and reward; configure signer policy outside the
public web process; test claim/submit/accept/reconcile on a safe environment; and
obtain owner approval for each mainnet transaction.
