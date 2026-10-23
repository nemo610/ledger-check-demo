"""Read-only discovery of claimable AgenC marketplace tasks.

This utility invokes only the documented task-list command. It cannot claim,
submit, accept, or sign transactions. It intentionally preserves the provider
JSON rather than assuming an undocumented response schema.
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Sequence


COMMAND = [
    "--network", "mainnet",
    "--json", "tasks", "list-claimable",
    "--limit", "10", "--compact",
]


class DiscoveryError(RuntimeError):
    """The read-only marketplace discovery failed or returned invalid data."""


def discover_tasks(
    *, executable: str = "agenc-marketplace", timeout: float = 20.0,
    runner=subprocess.run,
) -> dict:
    """Fetch up to ten claimable tasks without invoking any write operation."""
    if timeout <= 0 or timeout > 120:
        raise ValueError("timeout must be between 0 and 120 seconds")
    binary = shutil.which(executable)
    if binary is None:
        raise DiscoveryError(
            "agenc-marketplace CLI not found; install the official marketplace kit first"
        )
    try:
        result = runner(
            [binary, *COMMAND],
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired as exc:
        raise DiscoveryError("AgenC task discovery timed out") from exc
    except OSError as exc:
        raise DiscoveryError(f"Could not execute AgenC CLI: {exc}") from exc
    if result.returncode != 0:
        message = (result.stderr or "").strip()[:500]
        raise DiscoveryError(f"AgenC CLI exited {result.returncode}: {message}")
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise DiscoveryError("AgenC CLI did not return valid JSON") from exc
    if not isinstance(payload, (dict, list)):
        raise DiscoveryError("AgenC CLI JSON must be an object or array")
    return {
        "provider": "agenc",
        "mode": "read_only",
        "queried_at_utc": datetime.now(timezone.utc).isoformat(),
        "write_operations_enabled": False,
        "claimable_tasks": payload,
        "note": (
            "Discovery only. No task was claimed and no wallet signature or "
            "payment was requested. Review task specifications and reward terms manually."
        ),
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Read-only AgenC claimable-task discovery; never claims or signs."
    )
    parser.add_argument("--out", default="output/agenc_claimable_tasks.json")
    parser.add_argument("--timeout", type=float, default=20.0)
    args = parser.parse_args(argv)
    try:
        snapshot = discover_tasks(timeout=args.timeout)
    except (DiscoveryError, ValueError) as exc:
        print(f"Discovery unavailable: {exc}", file=sys.stderr)
        return 2
    path = Path(args.out)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(snapshot, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    count = len(snapshot["claimable_tasks"]) if isinstance(snapshot["claimable_tasks"], list) else len(
        snapshot["claimable_tasks"].get("tasks", [])
    )
    print(f"Read-only discovery saved to {path}; reported items={count}")
    print("No task was claimed. No transaction was signed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
