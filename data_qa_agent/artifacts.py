"""Create a verifiable JSON artifact for a local Data QA job.

This module does not upload files, read credentials, contact a marketplace,
or claim that a report has been accepted or paid.
"""
from __future__ import annotations

import hashlib
import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from data_qa_agent.core import inspect_file

DEFAULT_MAX_INPUT_BYTES = 10 * 1024 * 1024


class ArtifactError(ValueError):
    """An input or output cannot safely be packaged as a report artifact."""


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def create_report_artifact(
    input_path: str | Path,
    output_path: str | Path,
    *,
    max_input_bytes: int = DEFAULT_MAX_INPUT_BYTES,
) -> dict[str, Any]:
    """Inspect one CSV/JSON input and atomically write a hash-verifiable report.

    The input's contents are never copied into the report; only its basename,
    byte count and SHA-256 are included. Output includes an artifact hash
    returned separately, avoiding a self-referential hash field.
    """
    source = Path(input_path)
    destination = Path(output_path)
    if max_input_bytes <= 0:
        raise ArtifactError("max_input_bytes must be positive")
    try:
        if not source.is_file():
            raise ArtifactError("Input must be an existing regular file")
        source_size = source.stat().st_size
    except OSError as exc:
        raise ArtifactError("Input file cannot be accessed") from exc
    if source_size > max_input_bytes:
        raise ArtifactError(f"Input exceeds the {max_input_bytes}-byte limit")
    try:
        if source.resolve() == destination.resolve():
            raise ArtifactError("Output path must not overwrite the input")
    except OSError as exc:
        raise ArtifactError("Input/output paths could not be resolved") from exc
    if destination.suffix.lower() != ".json":
        raise ArtifactError("Output artifact must use the .json extension")

    report = inspect_file(source)
    payload = {
        "schema_version": "1.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source": {
            "filename": source.name,
            "size_bytes": source_size,
            "sha256": _sha256_file(source),
        },
        "report": report,
        "disclaimer": (
            "Preliminary structural checks only. Findings require human review; "
            "this report is not accounting, tax, legal, or business advice."
        ),
    }
    encoded = (json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary_name: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb", prefix=".data-qa-", suffix=".tmp",
            dir=destination.parent, delete=False,
        ) as handle:
            temporary_name = handle.name
            handle.write(encoded)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_name, destination)
        temporary_name = None
    except OSError as exc:
        raise ArtifactError("Report artifact could not be written atomically") from exc
    finally:
        if temporary_name is not None:
            try:
                os.unlink(temporary_name)
            except OSError:
                pass

    return {
        "artifact_path": str(destination),
        "artifact_size_bytes": destination.stat().st_size,
        "artifact_sha256": _sha256_file(destination),
        "source_sha256": payload["source"]["sha256"],
        "status": report.get("status", "unknown"),
    }
