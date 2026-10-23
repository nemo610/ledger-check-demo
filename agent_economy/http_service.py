"""AgenC HTTPS endpoint with health/manifest routes and CSV/JSON validation.
Registration, signing, task claiming, and settlement remain disabled until verified.
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlsplit

from agent_economy.provider_service import MAX_CONTENT_BYTES, validate_payload

AGENT_NAME = os.environ.get("AGENC_AGENT_NAME", "Nemo Agent")
AGENT_DESCRIPTION = os.environ.get(
    "AGENC_AGENT_DESCRIPTION",
    "CSV/JSON data validation service; on-chain actions require owner approval.",
)
PUBLIC_WALLET = os.environ.get("AGENC_PUBLIC_WALLET", "").strip()
CAPABILITIES = ["compute", "research", "code-review", "data-processing", "csv-json-validation"]
MAX_BODY_BYTES = 256 * 1024


def payload(path: str) -> tuple[int, dict]:
    if path in ("/health", "/healthz"):
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
            "service_api": {
                "validation_endpoint": "/v1/validate",
                "method": "POST",
                "content_type": "application/json",
                "max_content_bytes": MAX_CONTENT_BYTES,
                "stores_uploads": False,
                "performs_payments": False,
            },
            "next_steps": [
                "Verify the HTTPS endpoint publicly",
                "Read live protocol configuration and minimum stake",
                "Register the agent with an explicit owner-approved transaction",
                "Verify the commercial listing and settlement flow before claiming revenue",
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
    server_version = "NemoAgenCEndpoint/0.2"

    def _send_json(self, status: int, data: dict) -> None:
        body = json.dumps(data, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802
        status, data = payload(urlsplit(self.path).path)
        self._send_json(status, data)

    def do_POST(self) -> None:  # noqa: N802
        if urlsplit(self.path).path != "/v1/validate":
            self._send_json(404, {"error": "not_found"})
            return
        if "application/json" not in self.headers.get("Content-Type", "").lower():
            self._send_json(415, {"error": "content_type_must_be_application_json"})
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            self._send_json(400, {"error": "invalid_content_length"})
            return
        if length < 1 or length > MAX_BODY_BYTES:
            self._send_json(413 if length > MAX_BODY_BYTES else 400, {
                "error": "body_size_out_of_range",
                "max_body_bytes": MAX_BODY_BYTES,
            })
            return
        try:
            request_data = json.loads(self.rfile.read(length).decode("utf-8"))
            result = validate_payload(request_data)
        except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
            self._send_json(400, {"error": "invalid_request", "message": str(exc)})
            return
        except OverflowError as exc:
            self._send_json(413, {"error": "content_too_large", "message": str(exc)})
            return
        self._send_json(200, result)

    def log_message(self, fmt: str, *args) -> None:
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
