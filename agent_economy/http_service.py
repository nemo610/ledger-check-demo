"""Minimal public health and capability endpoint for AgenC registration.

This service deliberately does not sign Solana transactions or claim tasks.
Registration and money-moving actions remain disabled until the owner configures
a signer locally and approves each exact transaction.
"""
from __future__ import annotations

import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from datetime import datetime, timezone
from urllib.parse import urlsplit


AGENT_NAME = os.environ.get("AGENC_AGENT_NAME", "Nemo Agent")
AGENT_DESCRIPTION = os.environ.get(
    "AGENC_AGENT_DESCRIPTION",
    "General-purpose AI agent in staged integration; on-chain actions require owner approval.",
)
PUBLIC_WALLET = os.environ.get("AGENC_PUBLIC_WALLET", "").strip()
CAPABILITIES = ["compute", "research", "code-review", "data-processing"]


def payload(path: str) -> tuple[int, dict]:
    if path == "/health" or path == "/healthz":
        return 200, {
            "ok": True,
            "service": "agenc-agent-endpoint",
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        }
    if path in ("/", "/manifest.json", "/.well-known/agent.json"):
        return 200, {
            "schema_version": "1.0",
            "name": AGENT_NAME,
            "description": AGENT_DESCRIPTION,
            "capabilities": CAPABILITIES,
            "protocol": "agenc",
            "endpoint_status": "online",
            "execution_mode": "staged",
            "worker_enabled": False,
            "registration_status": "not_verified",
            "signing_enabled": False,
            "settlement_verified": False,
            "public_wallet": PUBLIC_WALLET or None,
            "security": {
                "private_keys_exposed": False,
                "autonomous_mainnet_signing": False,
                "task_claiming_enabled": False,
                "result_submission_enabled": False,
            },
            "next_steps": [
                "Verify the HTTPS endpoint publicly",
                "Read live protocol configuration and minimum stake",
                "Register the agent with explicit owner-approved transaction",
                "Enable a bounded worker only after signer policy and tests pass",
            ],
        }
    if path == "/ready":
        return 503, {
            "ready": False,
            "reason": "Worker registration and signer policy are not verified yet.",
            "registration_status": "not_verified",
            "worker_enabled": False,
        }
    return 404, {"error": "not_found"}


class Handler(BaseHTTPRequestHandler):
    server_version = "NemoAgenCEndpoint/0.1"

    def do_GET(self) -> None:  # noqa: N802
        path = urlsplit(self.path).path
        status, data = payload(path)
        body = json.dumps(data, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt: str, *args) -> None:
        # Avoid logging query strings or any accidental user-provided values.
        print("%s - %s" % (self.address_string(), fmt % args))


def main() -> None:
    host = "0.0.0.0"
    port = int(os.environ.get("PORT", "10000"))
    server = ThreadingHTTPServer((host, port), Handler)
    print(json.dumps({"event": "server_started", "host": host, "port": port}))
    try:
        server.serve_forever()
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
