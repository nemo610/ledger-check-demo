"""CLI for the local Data QA worker."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .core import inspect_file


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Data QA worker: inspect a local CSV/JSON and emit an auditable report."
    )
    parser.add_argument("input", help="Ruta local a un archivo .csv o .json")
    parser.add_argument("--out", default="output/data_qa_report.json", help="Ruta del informe JSON")
    args = parser.parse_args(argv)
    try:
        report = inspect_file(args.input)
        destination = Path(args.out)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    except (OSError, ValueError) as exc:
        print(f"Data QA failed: {exc}", file=sys.stderr)
        return 2
    print(f"Informe generado: {destination} | estado={report['status']}")
    print("Procesamiento local; el archivo de entrada no se subió a ningún servicio.")
    return 1 if report["status"] == "error" else 0


if __name__ == "__main__":
    raise SystemExit(main())
