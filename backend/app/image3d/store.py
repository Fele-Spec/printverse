"""SQLite persistence for Image-to-3D tasks."""
from __future__ import annotations

import json
import uuid
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .. import db

ROOT = Path(__file__).resolve().parents[3]


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def init_db() -> None:
    with closing(db.connect()) as conn, conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS image3d_jobs(
              id TEXT PRIMARY KEY,
              user_id TEXT NOT NULL,
              provider TEXT NOT NULL,
              model TEXT NOT NULL,
              status TEXT NOT NULL,
              task_id TEXT,
              input_path TEXT NOT NULL,
              output_format TEXT,
              output_url TEXT,
              local_path TEXT,
              generation_cost REAL,
              cost_currency TEXT,
              cost_basis TEXT,
              texture_status TEXT,
              geometry_status TEXT,
              task_status TEXT,
              authorized INTEGER NOT NULL DEFAULT 0,
              prompt TEXT,
              error TEXT,
              metadata TEXT,
              created_at TEXT NOT NULL,
              updated_at TEXT NOT NULL
            )
            """
        )


def create_job(*, user_id: str, provider: str, model: str, input_path: str,
               prompt: str, authorized: bool) -> dict:
    job_id = uuid.uuid4().hex
    ts = now()
    with closing(db.connect()) as conn, conn:
        conn.execute(
            "INSERT INTO image3d_jobs(id,user_id,provider,model,status,input_path,authorized,prompt,created_at,updated_at) "
            "VALUES(?,?,?,?,?,?,?,?,?,?)",
            (job_id, user_id, provider, model, "queued", input_path, int(authorized), prompt, ts, ts),
        )
    return get_job(job_id)


def update_job(job_id: str, **fields: Any) -> dict:
    allowed = {
        "status", "task_id", "output_format", "output_url", "local_path",
        "generation_cost", "cost_currency", "cost_basis", "texture_status",
        "geometry_status", "task_status", "error", "metadata",
    }
    sets, values = [], []
    for k, v in fields.items():
        if k not in allowed:
            continue
        if k == "metadata" and not isinstance(v, str):
            v = json.dumps(v, ensure_ascii=False)
        sets.append(f"{k}=?")
        values.append(v)
    sets.append("updated_at=?")
    values.append(now())
    values.append(job_id)
    with closing(db.connect()) as conn, conn:
        conn.execute(f"UPDATE image3d_jobs SET {', '.join(sets)} WHERE id=?", values)
    return get_job(job_id)


def get_job(job_id: str) -> dict:
    with closing(db.connect()) as conn, conn:
        row = conn.execute("SELECT * FROM image3d_jobs WHERE id=?", (job_id,)).fetchone()
    if not row:
        raise KeyError(job_id)
    out = dict(row)
    try:
        out["metadata"] = json.loads(out["metadata"]) if out.get("metadata") else {}
    except Exception:
        out["metadata"] = {}
    return out


def list_jobs(user_id: str, limit: int = 30) -> list[dict]:
    with closing(db.connect()) as conn, conn:
        rows = conn.execute(
            "SELECT * FROM image3d_jobs WHERE user_id=? ORDER BY created_at DESC LIMIT ?",
            (user_id, limit),
        ).fetchall()
    return [dict(r) for r in rows]
