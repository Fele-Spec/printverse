"""PostgreSQL backend for the virtual ledger.

The public API is selected by `PRINTVERSE_DATABASE_URL=postgresql://...`.
SQLite remains the zero-config local default. This module mirrors db.py's
transactional semantics without touching the existing SQLite tests.
"""
from __future__ import annotations

import os
import re
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Any, Iterable

import psycopg
from psycopg.rows import dict_row

DEMO_USER = "demo"
DEMO_GRANT_MG = 100_000
JSON = None


class InsufficientFilament(RuntimeError):
    pass


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _translate(sql: str) -> str:
    sql = sql.strip()
    if sql.upper().startswith("PRAGMA"):
        return "SELECT 1 WHERE FALSE"
    sql = sql.replace("?", "%s")
    sql = sql.replace("BEGIN IMMEDIATE", "BEGIN")
    if re.match(r"INSERT\s+OR\s+IGNORE\s+INTO", sql, re.I):
        sql = re.sub(r"INSERT\s+OR\s+IGNORE\s+INTO", "INSERT INTO", sql, flags=re.I)
        if "ON CONFLICT" not in sql.upper():
            sql = sql.rstrip().rstrip(";") + " ON CONFLICT DO NOTHING"
    return sql


class PgConnection:
    def __init__(self, dsn: str):
        self.conn = psycopg.connect(dsn, row_factory=dict_row, autocommit=True)
        self._tx = False

    def execute(self, sql: str, params: Iterable[Any] | None = None):
        return self.conn.execute(_translate(sql), params)

    def executescript(self, script: str) -> None:
        # psycopg cannot execute multiple statements with parameters; this schema
        # has no placeholders, so split on semicolons.
        for statement in script.split(";"):
            if statement.strip():
                self.execute(statement)

    def commit(self) -> None:
        if self._tx:
            self.conn.execute("COMMIT")
            self._tx = False

    def rollback(self) -> None:
        if self._tx:
            self.conn.execute("ROLLBACK")
            self._tx = False

    def close(self) -> None:
        self.conn.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        if exc_type:
            self.rollback()
        else:
            self.commit()
        self.close()


def connect() -> PgConnection:
    dsn = os.environ.get("PRINTVERSE_DATABASE_URL", "")
    if not dsn.startswith("postgres"):
        raise RuntimeError("PRINTVERSE_DATABASE_URL is not PostgreSQL")
    return PgConnection(dsn)


def init_db() -> None:
    schema = """
    CREATE TABLE IF NOT EXISTS users(
      id TEXT PRIMARY KEY, name TEXT NOT NULL, role TEXT NOT NULL DEFAULT 'user',
      created_at TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS wallets(
      user_id TEXT PRIMARY KEY REFERENCES users(id),
      balance_mg BIGINT NOT NULL DEFAULT 0,
      first_print_used INTEGER NOT NULL DEFAULT 0,
      updated_at TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS ledger(
      id BIGSERIAL PRIMARY KEY,
      user_id TEXT NOT NULL REFERENCES users(id),
      kind TEXT NOT NULL,
      mg BIGINT NOT NULL,
      operation_id TEXT NOT NULL UNIQUE,
      job_id TEXT,
      actor TEXT NOT NULL,
      reason TEXT NOT NULL,
      created_at TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS jobs(
      id TEXT PRIMARY KEY,
      user_id TEXT NOT NULL REFERENCES users(id),
      name TEXT NOT NULL,
      stl_path TEXT NOT NULL,
      color_path TEXT,
      gcode_path TEXT,
      toolpath_path TEXT,
      mass_mg BIGINT NOT NULL DEFAULT 0,
      status TEXT NOT NULL,
      free_print INTEGER NOT NULL DEFAULT 0,
      reserved_mg BIGINT NOT NULL DEFAULT 0,
      estimated_time_s DOUBLE PRECISION,
      layers INTEGER,
      warnings TEXT,
      created_at TEXT NOT NULL,
      completed_at TEXT
    );
    CREATE TABLE IF NOT EXISTS collection(
      id BIGSERIAL PRIMARY KEY,
      user_id TEXT NOT NULL REFERENCES users(id),
      job_id TEXT NOT NULL REFERENCES jobs(id),
      name TEXT NOT NULL,
      mass_mg BIGINT NOT NULL,
      model_path TEXT NOT NULL,
      created_at TEXT NOT NULL,
      UNIQUE(user_id, job_id)
    );
    """
    with connect() as conn:
        conn.executescript(schema)
        for uid, name, role in ((DEMO_USER, "Demo Maker", "user"), ("owner", "Owner", "admin"), ("guest", "Shared Guest", "user")):
            conn.execute("INSERT INTO users(id,name,role,created_at) VALUES(%s,%s,%s,%s) ON CONFLICT DO NOTHING",
                         (uid, name, role, now()))
        for uid, balance, used in ((DEMO_USER, DEMO_GRANT_MG, 0), ("owner", DEMO_GRANT_MG, 0), ("guest", 20_000, 1)):
            conn.execute("INSERT INTO wallets(user_id,balance_mg,first_print_used,updated_at) VALUES(%s,%s,%s,%s) ON CONFLICT DO NOTHING",
                         (uid, balance, used, now()))
        for uid, amount, op, reason in (
            (DEMO_USER, DEMO_GRANT_MG, "seed:demo:grant", "bootstrap virtual credit"),
            ("owner", DEMO_GRANT_MG, "seed:owner:grant", "owner unlimited virtual credit"),
            ("guest", 20_000, "seed:guest:grant", "guest quota virtual credit"),
        ):
            conn.execute("INSERT INTO ledger(user_id,kind,mg,operation_id,actor,reason,created_at) "
                         "VALUES(%s,%s,%s,%s,%s,%s,%s) ON CONFLICT DO NOTHING",
                         (uid, "grant", amount, op, "system", reason, now()))


def wallet(user_id: str = DEMO_USER) -> dict:
    with connect() as conn:
        row = conn.execute(
            "SELECT u.id,u.name,u.role,w.balance_mg,w.first_print_used "
            "FROM users u JOIN wallets w ON w.user_id=u.id WHERE u.id=%s", (user_id,)
        ).fetchone()
        if not row:
            raise KeyError(user_id)
        ledger = conn.execute(
            "SELECT kind,mg,operation_id,job_id,reason,created_at FROM ledger "
            "WHERE user_id=%s ORDER BY id DESC LIMIT 12", (user_id,)
        ).fetchall()
    return {
        "user": row["id"], "name": row["name"], "role": row["role"],
        "balance_mg": row["balance_mg"], "balance_g": round(row["balance_mg"] / 1000, 3),
        "first_print_available": bool(not row["first_print_used"]),
        "ledger": [dict(x) for x in ledger],
    }


def create_job(user_id: str, name: str, stl_path: str, job_id: str | None = None) -> str:
    job_id = job_id or uuid.uuid4().hex
    with connect() as conn:
        conn.execute("INSERT INTO jobs(id,user_id,name,stl_path,status,created_at) VALUES(%s,%s,%s,%s,%s,%s)",
                     (job_id, user_id, name, stl_path, "slicing", now()))
    return job_id


def set_job_color(job_id: str, color_path: str) -> None:
    with connect() as conn:
        conn.execute("UPDATE jobs SET color_path=%s WHERE id=%s", (color_path, job_id))


def set_job_sliced(job_id: str, gcode_path: str, toolpath_path: str, mass_mg: int,
                   estimated_time_s: float, layers: int, warnings: str = "") -> dict:
    with connect() as conn:
        conn.execute("UPDATE jobs SET gcode_path=%s,toolpath_path=%s,mass_mg=%s,status='ready',"
                     "estimated_time_s=%s,layers=%s,warnings=%s WHERE id=%s",
                     (gcode_path, toolpath_path, mass_mg, estimated_time_s, layers, warnings, job_id))
        row = conn.execute("SELECT * FROM jobs WHERE id=%s", (job_id,)).fetchone()
    return dict(row)


def get_job(job_id: str) -> dict:
    with connect() as conn:
        row = conn.execute("SELECT * FROM jobs WHERE id=%s", (job_id,)).fetchone()
    if not row:
        raise KeyError(job_id)
    return dict(row)


def reserve_for_job(job_id: str, user_id: str, mass_mg: int) -> dict:
    with connect() as conn:
        conn.execute("BEGIN")
        conn._tx = True
        existing = conn.execute("SELECT 1 FROM ledger WHERE operation_id=%s", (f"job:{job_id}:reserve",)).fetchone()
        if existing:
            row = conn.execute("SELECT * FROM jobs WHERE id=%s", (job_id,)).fetchone()
            return dict(row)
        user = conn.execute("SELECT role FROM users WHERE id=%s", (user_id,)).fetchone()
        if not user:
            raise KeyError(user_id)
        w = conn.execute("SELECT * FROM wallets WHERE user_id=%s FOR UPDATE", (user_id,)).fetchone()
        if user["role"] == "admin":
            free, reserved = 0, 0
            conn.execute("INSERT INTO ledger(user_id,kind,mg,operation_id,job_id,actor,reason,created_at) "
                         "VALUES(%s,%s,%s,%s,%s,%s,%s,%s)",
                         (user_id, "reserve", 0, f"job:{job_id}:reserve", job_id, user_id, "admin unlimited", now()))
        elif not w["first_print_used"]:
            free, reserved = 1, 0
            conn.execute("UPDATE wallets SET first_print_used=1,updated_at=%s WHERE user_id=%s", (now(), user_id))
            conn.execute("INSERT INTO ledger(user_id,kind,mg,operation_id,job_id,actor,reason,created_at) "
                         "VALUES(%s,%s,%s,%s,%s,%s,%s,%s)",
                         (user_id, "reserve", 0, f"job:{job_id}:reserve", job_id, user_id, "first print free", now()))
        else:
            free, reserved = 0, int(mass_mg)
            if w["balance_mg"] < reserved:
                raise InsufficientFilament(f"need {reserved/1000:.3f} g, available {w['balance_mg']/1000:.3f} g")
            conn.execute("UPDATE wallets SET balance_mg=balance_mg-%s,updated_at=%s WHERE user_id=%s",
                         (reserved, now(), user_id))
            conn.execute("INSERT INTO ledger(user_id,kind,mg,operation_id,job_id,actor,reason,created_at) "
                         "VALUES(%s,%s,%s,%s,%s,%s,%s,%s)",
                         (user_id, "reserve", -reserved, f"job:{job_id}:reserve", job_id, user_id, "print reservation", now()))
        conn.execute("UPDATE jobs SET free_print=%s,reserved_mg=%s,status='ready' WHERE id=%s",
                     (free, reserved, job_id))
        row = conn.execute("SELECT * FROM jobs WHERE id=%s", (job_id,)).fetchone()
        return dict(row)


def complete_job(job_id: str, user_id: str) -> dict:
    with connect() as conn:
        conn.execute("BEGIN")
        conn._tx = True
        job = conn.execute("SELECT * FROM jobs WHERE id=%s AND user_id=%s", (job_id, user_id)).fetchone()
        if not job:
            raise KeyError(job_id)
        if job["status"] == "completed":
            return dict(job)
        conn.execute("INSERT INTO ledger(user_id,kind,mg,operation_id,job_id,actor,reason,created_at) "
                     "VALUES(%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT DO NOTHING",
                     (user_id, "commit", 0, f"job:{job_id}:commit", job_id, user_id, "print completed", now()))
        conn.execute("UPDATE jobs SET status='completed',completed_at=%s WHERE id=%s", (now(), job_id))
        row = conn.execute("SELECT * FROM jobs WHERE id=%s", (job_id,)).fetchone()
    return dict(row)


def cancel_job(job_id: str, user_id: str) -> dict:
    with connect() as conn:
        conn.execute("BEGIN")
        conn._tx = True
        job = conn.execute("SELECT * FROM jobs WHERE id=%s AND user_id=%s", (job_id, user_id)).fetchone()
        if not job:
            raise KeyError(job_id)
        if job["status"] in {"completed", "cancelled"}:
            return dict(job)
        if job["free_print"]:
            conn.execute("UPDATE wallets SET first_print_used=0,updated_at=%s WHERE user_id=%s", (now(), user_id))
            mg = 0
        else:
            mg = int(job["reserved_mg"])
            if mg:
                conn.execute("UPDATE wallets SET balance_mg=balance_mg+%s,updated_at=%s WHERE user_id=%s",
                             (mg, now(), user_id))
        conn.execute("INSERT INTO ledger(user_id,kind,mg,operation_id,job_id,actor,reason,created_at) "
                     "VALUES(%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT DO NOTHING",
                     (user_id, "release", mg, f"job:{job_id}:release", job_id, user_id, "print cancelled", now()))
        conn.execute("UPDATE jobs SET status='cancelled' WHERE id=%s", (job_id,))
        row = conn.execute("SELECT * FROM jobs WHERE id=%s", (job_id,)).fetchone()
    return dict(row)


def add_collection(user_id: str, job_id: str, name: str, mass_mg: int, model_path: str) -> dict:
    with connect() as conn:
        conn.execute("INSERT INTO collection(user_id,job_id,name,mass_mg,model_path,created_at) "
                     "VALUES(%s,%s,%s,%s,%s,%s) ON CONFLICT (user_id,job_id) DO NOTHING",
                     (user_id, job_id, name, mass_mg, model_path, now()))
        row = conn.execute("SELECT * FROM collection WHERE user_id=%s AND job_id=%s", (user_id, job_id)).fetchone()
    return dict(row)


def list_collection(user_id: str = DEMO_USER) -> list[dict]:
    with connect() as conn:
        rows = conn.execute("SELECT * FROM collection WHERE user_id=%s ORDER BY id DESC", (user_id,)).fetchall()
    return [dict(r) for r in rows]
