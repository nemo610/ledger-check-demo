#!/usr/bin/env python3
"""Validate CSV row widths and JSON syntax without uploading file contents."""
from __future__ import annotations

import csv
import json
import os
import sys
from pathlib import Path

ROOT = Path(os.environ.get("INPUT_PATH", ".")).expanduser()
FAIL_ON_EMPTY_CSV = os.environ.get("FAIL_ON_EMPTY_CSV", "false").lower() == "true"
IGNORED_DIRS = {".git", ".venv", "venv", "node_modules", "__pycache__"}


def files_to_check(root: Path):
    if root.is_file():
        if root.suffix.lower() in {".csv", ".json"}:
            yield root
        else:
            raise ValueError(f"Unsupported file type: {root.name} (expected .csv or .json)")
        return
    if not root.is_dir():
        raise ValueError(f"Path does not exist: {root}")
    for current, dirs, filenames in os.walk(root):
        dirs[:] = [d for d in dirs if d not in IGNORED_DIRS]
        for filename in sorted(filenames):
            path = Path(current) / filename
            if path.suffix.lower() in {".csv", ".json"}:
                yield path


def validate_csv(path: Path):
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.reader(handle, strict=True)
        try:
            header = next(reader, None)
            if header is None:
                raise ValueError("file is empty")
            if not header or all(not col.strip() for col in header):
                raise ValueError("header row is empty")
            normalized = [col.strip() for col in header]
            if len(set(normalized)) != len(normalized):
                raise ValueError("duplicate column names in header")
            if any(not col for col in normalized):
                raise ValueError("header contains an empty column name")
            rows = 0
            for line_number, row in enumerate(reader, start=2):
                if len(row) != len(header):
                    raise ValueError(
                        f"row {line_number} has {len(row)} fields; expected {len(header)}"
                    )
                rows += 1
            if FAIL_ON_EMPTY_CSV and rows == 0:
                raise ValueError("CSV contains a header but no data rows")
            return f"valid CSV ({len(header)} columns, {rows} data rows)"
        except csv.Error as exc:
            raise ValueError(f"CSV parse error near line {reader.line_num}: {exc}") from exc


def validate_json(path: Path):
    with path.open("r", encoding="utf-8-sig") as handle:
        json.load(handle)
    return "valid JSON syntax"


def main():
    try:
        candidates = list(files_to_check(ROOT))
    except (OSError, ValueError) as exc:
        print(f"::error::{exc}")
        return 2

    if not candidates:
        print(f"::error::No .csv or .json files found under {ROOT}")
        return 2

    failures = 0
    for path in candidates:
        try:
            result = validate_csv(path) if path.suffix.lower() == ".csv" else validate_json(path)
            print(f"PASS: {path}: {result}")
        except (OSError, UnicodeError, csv.Error, json.JSONDecodeError, ValueError) as exc:
            failures += 1
            safe_message = str(exc).replace("\n", " ")
            print(f"::error file={path}::{safe_message}")
            print(f"FAIL: {path}: {safe_message}")

    print(f"Summary: checked {len(candidates)} file(s), {failures} failure(s).")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
