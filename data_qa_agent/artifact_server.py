"""Authenticated local artifact service for Data QA reports.

Run behind a TLS-terminating HTTPS reverse proxy in production. The built-in
HTTP server deliberately binds to loopback by default and does not provide TLS.
Only generated report JSON is accepted; raw customer input files are not.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import os
import re
import secrets
import threading
import tempfile
import time
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread
from urllib.parse import parse_qs, urlsplit

MAX_ARTIFACT_BYTES = 1 * 1024 * 1024
_ARTIFACT_ID = re.compile(r"^[A-Za-z0-9_-]{32,64}$")


class ArtifactStoreError(ValueError):
    """Invalid, expired, or unavailable artifact."""


class ArtifactStore:
    """Small file-backed store with server-generated IDs and TTL cleanup."""

    def __init__(
        self,
        root: str | Path,
        *,
        ttl_seconds: int = 86_400,
        max_bytes: int = MAX_ARTIFACT_BYTES,
    ) -> None:
        if ttl_seconds <= 0:
            raise ValueError("ttl_seconds must be positive")
        if max_bytes <= 0 or max_bytes > MAX_ARTIFACT_BYTES:
            raise ValueError(f"max_bytes must be between 1 and {MAX_ARTIFACT_BYTES}")
        self.root = Path(root).resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        self.ttl_seconds = ttl_seconds
        self.max_bytes = max_bytes
        self._lock = threading.RLock()

    def _paths(self, artifact_id: str) -> tuple[Path, Path]:
        if not _ARTIFACT_ID.fullmatch(artifact_id):
            raise ArtifactStoreError("Invalid artifact ID")
        return self.root / f"{artifact_id}.json", self.root / f"{artifact_id}.expires"

    def _atomic_write(self, path: Path, data: bytes) -> None:
        """Write one file atomically within the store filesystem."""
        fd, temp_name = tempfile.mkstemp(
            prefix=f".{path.name}.", suffix=".tmp", dir=self.root
        )
        temp_path = Path(temp_name)
        try:
            with os.fdopen(fd, "wb") as stream:
                stream.write(data)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temp_path, path)
        finally:
            temp_path.unlink(missing_ok=True)

    def put(self, raw: bytes) -> dict:
        if not raw or len(raw) > self.max_bytes:
            raise ArtifactStoreError("Artifact is empty or exceeds the size limit")
        try:
            payload = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ArtifactStoreError("Artifact must be valid UTF-8 JSON") from exc
        if not isinstance(payload, dict):
            raise ArtifactStoreError("Artifact JSON root must be an object")
        source = payload.get("source")
        report = payload.get("report")
        if (
            payload.get("schema_version") != "1.0"
            or not isinstance(source, dict)
            or not isinstance(source.get("sha256"), str)
            or not re.fullmatch(r"[a-fA-F0-9]{64}", source["sha256"])
            or not isinstance(report, dict)
        ):
            raise ArtifactStoreError("JSON does not match the Data QA report schema")

        # Canonicalize the JSON before hashing and storing it.
        encoded = (json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")
        if len(encoded) > self.max_bytes:
            raise ArtifactStoreError("Canonical artifact exceeds the size limit")
        artifact_id = secrets.token_urlsafe(24)
        artifact_path, expiry_path = self._paths(artifact_id)
        expires_at = int(time.time()) + self.ttl_seconds
        with self._lock:
            try:
                self._atomic_write(artifact_path, encoded)
                self._atomic_write(expiry_path, str(expires_at).encode("ascii"))
            except OSError:
                # A newly generated ID cannot refer to an earlier valid record.
                # Remove either half if the second atomic replace fails.
                artifact_path.unlink(missing_ok=True)
                expiry_path.unlink(missing_ok=True)
                raise
        return {
            "artifact_id": artifact_id,
            "path": f"/v1/artifacts/{artifact_id}",
            "sha256": hashlib.sha256(encoded).hexdigest(),
            "size_bytes": len(encoded),
            "expires_at": datetime.fromtimestamp(expires_at, timezone.utc).isoformat(),
        }

    def get(self, artifact_id: str) -> tuple[bytes, str]:
        artifact_path, expiry_path = self._paths(artifact_id)
        with self._lock:
            try:
                expires_at = int(expiry_path.read_text(encoding="ascii"))
                if expires_at <= int(time.time()):
                    artifact_path.unlink(missing_ok=True)
                    expiry_path.unlink(missing_ok=True)
                    raise ArtifactStoreError("Artifact has expired")
                raw = artifact_path.read_bytes()
            except ArtifactStoreError:
                raise
            except (OSError, ValueError) as exc:
                raise ArtifactStoreError("Artifact not found") from exc
        return raw, hashlib.sha256(raw).hexdigest()

    def delete(self, artifact_id: str) -> None:
        artifact_path, expiry_path = self._paths(artifact_id)
        with self._lock:
            existed = artifact_path.exists()
            artifact_path.unlink(missing_ok=True)
            expiry_path.unlink(missing_ok=True)
            if not existed:
                raise ArtifactStoreError("Artifact not found")

    def cleanup_expired(self) -> int:
        removed = 0
        now = int(time.time())
        with self._lock:
            for expiry_path in self.root.glob("*.expires"):
                try:
                    expires_at = int(expiry_path.read_text(encoding="ascii"))
                    artifact_id = expiry_path.stem
                    artifact_path, _ = self._paths(artifact_id)
                    if expires_at <= now:
                        artifact_path.unlink(missing_ok=True)
                        expiry_path.unlink(missing_ok=True)
                        removed += 1
                except (OSError, ValueError, ArtifactStoreError):
                    # Do not delete files with malformed metadata automatically.
                    continue
        return removed


def make_handler(store: ArtifactStore, token: str):
    """Create an HTTP handler requiring a bearer token on every endpoint."""
    if len(token) < 32:
        raise ValueError("ARTIFACT_API_TOKEN must contain at least 32 characters")

    signing_secret = token.encode("utf-8")

    class Handler(BaseHTTPRequestHandler):
        server_version = "LedgerCheckArtifact/0.1"

        def log_message(self, fmt: str, *args) -> None:
            # Avoid logging request headers, tokens, or artifact contents.
            super().log_message("%s", "request handled")

        def _has_bearer_token(self) -> bool:
            supplied = self.headers.get("Authorization", "")
            expected = f"Bearer {token}"
            return hmac.compare_digest(supplied.encode("utf-8"), expected.encode("utf-8"))

        def _authorized(self) -> bool:
            if not self._has_bearer_token():
                self.send_error(401, "Unauthorized")
                return False
            return True

        def _valid_signed_download(self, artifact_id: str) -> bool:
            try:
                query = parse_qs(urlsplit(self.path).query, strict_parsing=True)
                if set(query) != {"expires", "sig"} or any(
                    len(values) != 1 for values in query.values()
                ):
                    return False
                expires = int(query["expires"][0])
                supplied_signature = query["sig"][0]
            except (KeyError, IndexError, ValueError):
                return False
            if expires <= int(time.time()) or not re.fullmatch(r"[a-f0-9]{64}", supplied_signature):
                return False
            expected_signature = hmac.new(
                signing_secret,
                f"{artifact_id}:{expires}".encode("ascii"),
                hashlib.sha256,
            ).hexdigest()
            return hmac.compare_digest(supplied_signature, expected_signature)

        def _json(self, status: int, payload: dict) -> None:
            raw = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(raw)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(raw)

        def do_POST(self) -> None:
            if urlsplit(self.path).path != "/v1/artifacts":
                self.send_error(404)
                return
            if not self._authorized():
                return
            try:
                length = int(self.headers.get("Content-Length", ""))
            except ValueError:
                self.send_error(411, "Content-Length required")
                return
            if length <= 0 or length > store.max_bytes:
                self.send_error(413, "Artifact size invalid or too large")
                return
            try:
                result = store.put(self.rfile.read(length))
                expires = int(datetime.fromisoformat(result["expires_at"]).timestamp())
                signature = hmac.new(
                    signing_secret,
                    f"{result['artifact_id']}:{expires}".encode("ascii"),
                    hashlib.sha256,
                ).hexdigest()
                result["download_path"] = f"{result['path']}?expires={expires}&sig={signature}"
            except ArtifactStoreError as exc:
                self._json(400, {"error": str(exc)})
                return
            except OSError:
                self.send_error(500, "Artifact storage failed")
                return
            self._json(201, result)

        def _artifact_id(self) -> str | None:
            match = re.fullmatch(r"/v1/artifacts/([A-Za-z0-9_-]{32,64})", urlsplit(self.path).path)
            return match.group(1) if match else None

        def do_GET(self) -> None:
            artifact_id = self._artifact_id()
            if artifact_id is None:
                self.send_error(404)
                return
            if not self._has_bearer_token() and not self._valid_signed_download(artifact_id):
                self.send_error(401, "Unauthorized or invalid download signature")
                return
            try:
                raw, digest = store.get(artifact_id)
            except ArtifactStoreError:
                self.send_error(404, "Artifact not found or expired")
                return
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(raw)))
            self.send_header("Cache-Control", "private, no-store")
            self.send_header("ETag", f'"{digest}"')
            self.end_headers()
            self.wfile.write(raw)

        def do_DELETE(self) -> None:
            if not self._authorized():
                return
            artifact_id = self._artifact_id()
            if artifact_id is None:
                self.send_error(404)
                return
            try:
                store.delete(artifact_id)
            except ArtifactStoreError:
                self.send_error(404, "Artifact not found")
                return
            self.send_response(204)
            self.send_header("Cache-Control", "no-store")
            self.end_headers()

    return Handler


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Authenticated local Data QA artifact API.")
    parser.add_argument("--host", default=os.environ.get("ARTIFACT_BIND_HOST", "127.0.0.1"))
    parser.add_argument("--port", type=int, default=int(os.environ.get("ARTIFACT_PORT", "8080")))
    parser.add_argument("--storage", default=os.environ.get("ARTIFACT_STORAGE_DIR", "./private_artifacts"))
    parser.add_argument("--ttl-seconds", type=int, default=int(os.environ.get("ARTIFACT_TTL_SECONDS", "86400")))
    args = parser.parse_args()
    token = os.environ.get("ARTIFACT_API_TOKEN", "")
    if len(token) < 32:
        parser.error("Set ARTIFACT_API_TOKEN to a random secret of at least 32 characters.")
    store = ArtifactStore(args.storage, ttl_seconds=args.ttl_seconds)
    server = ThreadingHTTPServer((args.host, args.port), make_handler(store, token))

    def cleanup_loop() -> None:
        while True:
            time.sleep(300)
            try:
                store.cleanup_expired()
            except OSError:
                # Keep the API alive; storage/cleanup failures need operational monitoring.
                continue

    Thread(target=cleanup_loop, name="artifact-expiry-cleanup", daemon=True).start()
    print(f"Artifact API listening on {args.host}:{args.port}; TLS must be provided by a trusted HTTPS reverse proxy in production.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
