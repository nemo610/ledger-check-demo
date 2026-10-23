"""AgentBazaar Gateway worker for Data Check.

The worker accepts only structured CSV/JSON payloads. It never executes task
instructions, downloads URLs, reads local paths, or stores submitted content.
"""
from __future__ import annotations

import asyncio
import logging
import os
from typing import Any

from .provider_service import validate_payload

logger = logging.getLogger("data_check.agentbazaar")


def process_job_payload(payload: Any) -> dict[str, Any]:
    """Validate one structured marketplace job payload."""
    if not isinstance(payload, dict):
        raise ValueError("Job payload must be an object.")
    # Explicit allowlist: only these fields reach the validator.
    allowed = {"filename", "format", "content"}
    unexpected = set(payload) - allowed
    if unexpected:
        raise ValueError("Unsupported payload fields: " + ", ".join(sorted(unexpected)))
    return validate_payload(payload)


async def run_worker(token: str | None = None) -> None:
    """Connect to AgentBazaar Gateway Protocol v1 and handle paid jobs."""
    token = token or os.environ.get("AGENTBAZAAR_TOKEN", "")
    if not token.strip():
        raise RuntimeError("AGENTBAZAAR_TOKEN is not configured; worker will not start.")

    # Import the official SDK only when the worker is enabled.
    from agentsbazaar_worker import AgentWorker

    worker = AgentWorker(
        token=token,
        capacity=2,
        capabilities=["data-validation", "csv-validation", "json-validation"],
        client_info={"name": "Data Check", "version": "0.2.0"},
        verbose=True,
    )

    @worker.on_job
    async def handle_job(job) -> None:
        try:
            result = process_job_payload(job.payload)
        except (ValueError, TypeError, OverflowError) as exc:
            await job.respond(
                {"service": "Data Check", "task_status": "rejected",
                 "error": "invalid_payload", "message": str(exc)},
                status=400,
            )
            return
        await job.respond(
            {"service": "Data Check", "task_status": "completed", "result": result},
            status=200,
        )

    logger.info("Starting AgentBazaar Gateway worker (token not logged).")
    await worker.run()


def run_worker_forever() -> None:
    """Entrypoint suitable for a worker process."""
    asyncio.run(run_worker())


if __name__ == "__main__":
    logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
    run_worker_forever()
