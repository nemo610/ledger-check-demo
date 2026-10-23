"""Deterministic CSV/JSON data-quality checks; never uploads input data."""
from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path
from typing import Any

MAX_INPUT_BYTES = 10 * 1024 * 1024


def _finding(code: str, severity: str, message: str, count: int = 1) -> dict[str, Any]:
    return {"code": code, "severity": severity, "message": message, "count": count}


def _input_too_large(source: Path, size: int) -> dict[str, Any]:
    return {
        "file": source.name,
        "format": source.suffix.lower().lstrip("."),
        "status": "error",
        "rows": 0,
        "columns": 0,
        "findings": [_finding(
            "INPUT_TOO_LARGE", "high",
            f"El archivo supera el límite de {MAX_INPUT_BYTES} bytes.",
        )],
    }


def inspect_csv(path: str | Path) -> dict[str, Any]:
    """Inspect a CSV locally and return a JSON-serializable QA report."""
    source = Path(path)
    findings: list[dict[str, Any]] = []
    try:
        if not source.is_file():
            raise OSError("not a regular file")
        if source.stat().st_size > MAX_INPUT_BYTES:
            return _input_too_large(source, source.stat().st_size)
        with source.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.reader(handle, strict=True)
            try:
                headers = next(reader)
            except StopIteration:
                return {"file": source.name, "format": "csv", "status": "needs_review",
                        "rows": 0, "columns": 0,
                        "findings": [_finding("EMPTY_FILE", "high", "El archivo está vacío.")]}
            normalized = [h.strip() for h in headers]
            counts = Counter(normalized)
            blank_headers = sum(not h for h in normalized)
            duplicate_header_count = sum(count - 1 for name, count in counts.items() if name and count > 1)
            if blank_headers:
                findings.append(_finding("BLANK_HEADERS", "high", "Hay columnas sin nombre.", blank_headers))
            if duplicate_header_count:
                # Do not disclose customer-defined header names in generated reports.
                findings.append(_finding("DUPLICATE_HEADERS", "high",
                    "Hay nombres de columnas repetidos; revisar el encabezado.",
                    duplicate_header_count))
            width = len(headers)
            rows = 0
            blank_rows = 0
            malformed_rows = 0
            exact_duplicates = 0
            seen: set[tuple[str, ...]] = set()
            for row in reader:
                if not row or all(not cell.strip() for cell in row):
                    blank_rows += 1
                    continue
                rows += 1
                if len(row) != width:
                    malformed_rows += 1
                key = tuple(cell.strip() for cell in row)
                if key in seen:
                    exact_duplicates += 1
                else:
                    seen.add(key)
    except (OSError, UnicodeError, csv.Error) as exc:
        return {"file": source.name, "format": "csv", "status": "error",
                "rows": 0, "columns": 0,
                "findings": [_finding("READ_ERROR", "high", f"No se pudo leer el CSV: {type(exc).__name__}.")]}
    if blank_rows:
        findings.append(_finding("BLANK_ROWS", "medium", "Hay filas completamente vacías.", blank_rows))
    if malformed_rows:
        findings.append(_finding("ROW_WIDTH_MISMATCH", "high",
            "Hay filas con distinta cantidad de campos que el encabezado.", malformed_rows))
    if exact_duplicates:
        findings.append(_finding("EXACT_DUPLICATE_ROWS", "medium",
            "Hay filas idénticas; verificar si son duplicados legítimos.", exact_duplicates))
    return {"file": source.name, "format": "csv", "status": "needs_review" if findings else "passed",
            "rows": rows, "columns": width, "findings": findings,
            "limitations": ["No valida obligaciones fiscales ni la veracidad del contenido.",
                            "Los duplicados son alertas y requieren criterio humano."]}


def inspect_json(path: str | Path) -> dict[str, Any]:
    """Check JSON syntax and report the root shape without exposing file contents."""
    source = Path(path)
    try:
        if not source.is_file():
            raise OSError("not a regular file")
        if source.stat().st_size > MAX_INPUT_BYTES:
            return _input_too_large(source, source.stat().st_size)
        with source.open("r", encoding="utf-8-sig") as handle:
            payload = json.load(handle)
    except (OSError, UnicodeError, json.JSONDecodeError, RecursionError) as exc:
        return {"file": source.name, "format": "json", "status": "error",
                "findings": [_finding("INVALID_JSON", "high",
                    f"No se pudo leer JSON válido: {type(exc).__name__}.")]}
    if isinstance(payload, dict):
        root_type, item_count = "object", len(payload)
    elif isinstance(payload, list):
        root_type, item_count = "array", len(payload)
    else:
        root_type, item_count = type(payload).__name__, 1
    findings = [] if isinstance(payload, (dict, list)) else [
        _finding("UNEXPECTED_ROOT_TYPE", "low",
                 "La raíz JSON no es un objeto ni un arreglo.")
    ]
    return {"file": source.name, "format": "json",
            "status": "needs_review" if findings else "passed",
            "root_type": root_type, "items_or_keys": item_count, "findings": findings,
            "limitations": ["Valida sintaxis y forma general; no valida reglas de negocio."]}


def inspect_file(path: str | Path) -> dict[str, Any]:
    """Route supported local files to a deterministic inspector with a hard size limit."""
    source = Path(path)
    suffix = source.suffix.lower()
    if suffix not in {".csv", ".json"}:
        raise ValueError("Formato no soportado; usá .csv o .json")
    try:
        if not source.is_file():
            raise OSError("not a regular file")
        if source.stat().st_size > MAX_INPUT_BYTES:
            return _input_too_large(source, source.stat().st_size)
    except OSError as exc:
        return {"file": source.name, "format": suffix[1:], "status": "error",
                "rows": 0, "columns": 0,
                "findings": [_finding("READ_ERROR", "high", "No se pudo acceder al archivo de entrada.")]}
    if suffix == ".csv":
        return inspect_csv(source)
    return inspect_json(source)
