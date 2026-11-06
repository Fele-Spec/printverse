"""Standalone worker for queued Image-to-3D jobs.

The API can execute jobs inline for local development. In the compose deployment
this process is the durable consumer; it uses the same SQLite volume and never
calls a paid provider without the authorization stored on the job.
"""
from __future__ import annotations

import os
import time
from contextlib import closing

from . import db
from .image3d import store
from .image3d.registry import run
from .image3d.types import GenerationRequest, ProviderError


def main() -> None:
    db.init_db()
    store.init_db()
    poll = float(os.environ.get("WORKER_POLL_S", "2"))
    once = os.environ.get("WORKER_ONCE", "0").lower() in {"1", "true", "yes"}
    print("printverse worker ready", flush=True)
    while True:
        try:
            with closing(db.connect()) as conn:
                row = conn.execute(
                    "SELECT * FROM image3d_jobs WHERE status='queued' ORDER BY created_at LIMIT 1"
                ).fetchone()
            if not row:
                if once:
                    print("worker once: no queued job", flush=True)
                    return
                time.sleep(poll)
                continue
            job = dict(row)
            store.update_job(job["id"], status="running", task_status="running")
            req = GenerationRequest(
                job_id=job["id"], image_path=job["input_path"], prompt=job.get("prompt") or "",
                authorized=bool(job["authorized"]), budget_cny=0.0,
            )
            try:
                result = run(job["provider"], req, allow_free_fallback=job["provider"] == "auto")
                store.update_job(job["id"], status="completed", **result.to_dict())
            except ProviderError as exc:
                store.update_job(job["id"], status=exc.status, error=str(exc),
                                 task_status=exc.status, generation_cost=exc.cost)
            except Exception as exc:  # noqa: BLE001
                store.update_job(job["id"], status="failed", error=str(exc)[-4000:], task_status="failed")
            if once:
                print("worker once: processed", job["id"], flush=True)
                return
        except Exception as exc:  # noqa: BLE001
            print("worker error", type(exc).__name__, exc, flush=True)
            if once:
                return
            time.sleep(poll)


if __name__ == "__main__":
    main()
