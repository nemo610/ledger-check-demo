"""Stateless CSV/JSON quality-check logic; no chain writes or payment execution."""
from __future__ import annotations

import csv
import hashlib
import io
import json
from typing import Any

MAX_CONTENT_BYTES = 192 * 1024


def _csv(text: str) -> dict[str, Any]:
    try:
        rows = list(csv.reader(io.StringIO(text, newline=""), strict=True))
    except csv.Error as exc:
        return {"valid": False, "format": "csv", "findings": [{"code": "CSV_PARSE_ERROR", "message": str(exc)}]}
    findings = []
    if not rows or not rows[0] or not any(cell.strip() for cell in rows[0]):
        return {"valid": False, "format": "csv", "findings": [{"code": "MISSING_HEADER", "message": "CSV needs a non-empty header row."}]}
    header = rows[0]
    if any(not name.strip() for name in header):
        findings.append({"code": "EMPTY_COLUMN_NAME", "message": "One or more column names are empty."})
    normalized = [name.strip().casefold() for name in header]
    if len(set(normalized)) != len(normalized):
        findings.append({"code": "DUPLICATE_COLUMN", "message": "Column names are duplicated (case-insensitive)."})
    bad_rows = [i + 1 for i, row in enumerate(rows[1:], start=1) if len(row) != len(header)]
    if bad_rows:
        findings.append({"code": "ROW_WIDTH_MISMATCH", "message": "Some data rows have a different number of fields.", "row_numbers": bad_rows[:100], "count": len(bad_rows)})
    if len(rows) == 1:
        findings.append({"code": "NO_DATA_ROWS", "message": "CSV has a header but no data rows.", "severity": "warning"})
    return {"valid": not any(item.get("severity") != "warning" for item in findings), "format": "csv", "columns": len(header), "data_rows": max(0, len(rows) - 1), "findings": findings}


def validate_payload(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise ValueError("Request JSON must be an object.")
    filename = payload.get("filename", "upload")
    fmt = str(payload.get("format", "")).lower().strip()
    content = payload.get("content")
    if not isinstance(filename, str) or not filename or len(filename) > 160 or "/" in filename or chr(92) in filename:
        raise ValueError("filename must be a simple filename, not a path.")
    if fmt not in {"csv", "json"}:
        raise ValueError("format must be 'csv' or 'json'.")
    if not isinstance(content, str):
        raise ValueError("content must be a UTF-8 text string.")
    raw = content.encode("utf-8")
    if len(raw) > MAX_CONTENT_BYTES:
        raise OverflowError("content exceeds the 192 KiB limit.")
    if fmt == "json":
        try:
            parsed = json.loads(content)
            result = {"valid": True, "format": "json", "root_type": type(parsed).__name__, "findings": []}
        except json.JSONDecodeError as exc:
            result = {"valid": False, "format": "json", "findings": [{"code": "JSON_PARSE_ERROR", "message": exc.msg, "line": exc.lineno, "column": exc.colno}]}
    else:
        result = _csv(content)
    return {"service": "CSV/JSON Data Quality Check", "version": "0.1.0", "filename": filename, "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw), "stored": False, "settlement_verified": False, **result}
