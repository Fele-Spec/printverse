"""SQLite ledger and job persistence for the PrintVerse phase-2 demo.

Virtual-only: no payment provider, card data or real spool mutation.
"""
from __future__ import annotations

import os
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from contextlib import closing

ROOT = Path(__file__).resolve().parents[2]
DB_PATH = Path(os.environ.get("PRINTVERSE_DB", ROOT / "database" / "printverse.db"))
DEMO_USER = "demo"
DEMO_GRANT_MG = 100_000  # 100 g demo credit; first print is separately free


class InsufficientFilament(RuntimeError):
    pass


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db() -> None:
    with closing(connect()) as conn, conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS users(
              id TEXT PRIMARY KEY, name TEXT NOT NULL, role TEXT NOT NULL DEFAULT 'user',
              created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS wallets(
              user_id TEXT PRIMARY KEY REFERENCES users(id),
              balance_mg INTEGER NOT NULL DEFAULT 0,
              first_print_used INTEGER NOT NULL DEFAULT 0,
              updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS ledger(
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              user_id TEXT NOT NULL REFERENCES users(id),
              kind TEXT NOT NULL,
              mg INTEGER NOT NULL,
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
              gcode_path TEXT,
              toolpath_path TEXT,
              mass_mg INTEGER NOT NULL DEFAULT 0,
              status TEXT NOT NULL,
              free_print INTEGER NOT NULL DEFAULT 0,
              reserved_mg INTEGER NOT NULL DEFAULT 0,
              estimated_time_s REAL,
              layers INTEGER,
              warnings TEXT,
              created_at TEXT NOT NULL,
              completed_at TEXT
            );
            CREATE TABLE IF NOT EXISTS collection(
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              user_id TEXT NOT NULL REFERENCES users(id),
              job_id TEXT NOT NULL REFERENCES jobs(id),
              name TEXT NOT NULL,
              mass_mg INTEGER NOT NULL,
              model_path TEXT NOT NULL,
              created_at TEXT NOT NULL,
              UNIQUE(user_id, job_id)
            );
            """
        )
        conn.execute(
            "INSERT OR IGNORE INTO users(id,name,role,created_at) VALUES(?,?,?,?)",
            (DEMO_USER, "Demo Maker", "user", now()),
        )
        conn.execute(
            "INSERT OR IGNORE INTO wallets(user_id,balance_mg,first_print_used,updated_at) VALUES(?,?,0,?)",
            (DEMO_USER, DEMO_GRANT_MG, now()),
        )
        exists = conn.execute(
            "SELECT 1 FROM ledger WHERE operation_id=?", ("seed:demo:grant",)
        ).fetchone()
        if not exists:
            conn.execute(
                "INSERT INTO ledger(user_id,kind,mg,operation_id,actor,reason,created_at) VALUES(?,?,?,?,?,?,?)",
                (DEMO_USER, "grant", DEMO_GRANT_MG, "seed:demo:grant", "system", "bootstrap virtual credit", now()),
            )
        # Shared-mode identities: owner is admin/unlimited and is selected only
        # from loopback; guest has a finite wallet and no free-print entitlement.
        conn.execute("INSERT OR IGNORE INTO users(id,name,role,created_at) VALUES(?,?,?,?)",
                     ("owner", "Owner", "admin", now()))
        conn.execute("INSERT OR IGNORE INTO wallets(user_id,balance_mg,first_print_used,updated_at) VALUES(?,?,?,?)",
                     ("owner", DEMO_GRANT_MG, 0, now()))
        conn.execute("INSERT OR IGNORE INTO users(id,name,role,created_at) VALUES(?,?,?,?)",
                     ("guest", "Shared Guest", "user", now()))
        conn.execute("INSERT OR IGNORE INTO wallets(user_id,balance_mg,first_print_used,updated_at) VALUES(?,?,?,?)",
                     ("guest", 20_000, 1, now()))
        for uid, op, reason in (("owner", "seed:owner:grant", "owner unlimited virtual credit"),
                                ("guest", "seed:guest:grant", "guest quota virtual credit")):
            if not conn.execute("SELECT 1 FROM ledger WHERE operation_id=?", (op,)).fetchone():
                conn.execute(
                    "INSERT INTO ledger(user_id,kind,mg,operation_id,actor,reason,created_at) VALUES(?,?,?,?,?,?,?)",
                    (uid, "grant", 100_000 if uid == "owner" else 20_000, op, "system", reason, now()),
                )


def wallet(user_id: str = DEMO_USER) -> dict:
    with closing(connect()) as conn, conn:
        row = conn.execute(
            "SELECT u.id,u.name,u.role,w.balance_mg,w.first_print_used "
            "FROM users u JOIN wallets w ON w.user_id=u.id WHERE u.id=?",
            (user_id,),
        ).fetchone()
        if not row:
            raise KeyError(user_id)
        ledger = [
            dict(r)
            for r in conn.execute(
                "SELECT kind,mg,operation_id,job_id,reason,created_at FROM ledger "
                "WHERE user_id=? ORDER BY id DESC LIMIT 12",
                (user_id,),
            )
        ]
    return {
        "user": row["id"],
        "name": row["name"],
        "role": row["role"],
        "balance_mg": row["balance_mg"],
        "balance_g": round(row["balance_mg"] / 1000, 3),
        "first_print_available": bool(not row["first_print_used"]),
        "ledger": ledger,
    }


def create_job(user_id: str, name: str, stl_path: str, job_id: str | None = None) -> str:
    job_id = job_id or uuid.uuid4().hex
    with closing(connect()) as conn, conn:
        conn.execute(
            "INSERT INTO jobs(id,user_id,name,stl_path,status,created_at) VALUES(?,?,?,?,?,?)",
            (job_id, user_id, name, stl_path, "slicing", now()),
        )
    return job_id


def set_job_sliced(job_id: str, gcode_path: str, toolpath_path: str, mass_mg: int,
                   estimated_time_s: float, layers: int, warnings: str = "") -> dict:
    with closing(connect()) as conn, conn:
        conn.execute(
            "UPDATE jobs SET gcode_path=?,toolpath_path=?,mass_mg=?,status='ready',"
            "estimated_time_s=?,layers=?,warnings=? WHERE id=?",
            (gcode_path, toolpath_path, mass_mg, estimated_time_s, layers, warnings, job_id),
        )
        row = conn.execute("SELECT * FROM jobs WHERE id=?", (job_id,)).fetchone()
    return dict(row)


def get_job(job_id: str) -> dict:
    with closing(connect()) as conn, conn:
        row = conn.execute("SELECT * FROM jobs WHERE id=?", (job_id,)).fetchone()
    if not row:
        raise KeyError(job_id)
    return dict(row)


def reserve_for_job(job_id: str, user_id: str, mass_mg: int) -> dict:
    """Reserve balance or the single first-print entitlement in one transaction."""
    with closing(connect()) as conn, conn:
        conn.execute("BEGIN IMMEDIATE")
        existing = conn.execute(
            "SELECT 1 FROM ledger WHERE operation_id=?", (f"job:{job_id}:reserve",)
        ).fetchone()
        if existing:
            row = conn.execute("SELECT * FROM jobs WHERE id=?", (job_id,)).fetchone()
            return dict(row)
        user = conn.execute("SELECT role FROM users WHERE id=?", (user_id,)).fetchone()
        if not user:
            raise KeyError(user_id)
        w = conn.execute("SELECT * FROM wallets WHERE user_id=?", (user_id,)).fetchone()
        if user["role"] == "admin":
            free = 0
            reserved = 0
            conn.execute(
                "INSERT INTO ledger(user_id,kind,mg,operation_id,job_id,actor,reason,created_at) "
                "VALUES(?,?,?,?,?,?,?,?)",
                (user_id, "reserve", 0, f"job:{job_id}:reserve", job_id, user_id, "admin unlimited", now()),
            )
        elif not w["first_print_used"]:
            free = 1
            reserved = 0
            conn.execute(
                "UPDATE wallets SET first_print_used=1,updated_at=? WHERE user_id=?",
                (now(), user_id),
            )
            conn.execute(
                "INSERT INTO ledger(user_id,kind,mg,operation_id,job_id,actor,reason,created_at) "
                "VALUES(?,?,?,?,?,?,?,?)",
                (user_id, "reserve", 0, f"job:{job_id}:reserve", job_id, user_id, "first print free", now()),
            )
        else:
            free = 0
            reserved = int(mass_mg)
            if w["balance_mg"] < reserved:
                raise InsufficientFilament(
                    f"need {reserved/1000:.3f} g, available {w['balance_mg']/1000:.3f} g"
                )
            conn.execute(
                "UPDATE wallets SET balance_mg=balance_mg-?,updated_at=? WHERE user_id=?",
                (reserved, now(), user_id),
            )
            conn.execute(
                "INSERT INTO ledger(user_id,kind,mg,operation_id,job_id,actor,reason,created_at) "
                "VALUES(?,?,?,?,?,?,?,?)",
                (user_id, "reserve", -reserved, f"job:{job_id}:reserve", job_id, user_id, "print reservation", now()),
            )
        conn.execute(
            "UPDATE jobs SET free_print=?,reserved_mg=?,status='ready' WHERE id=?",
            (free, reserved, job_id),
        )
        row = conn.execute("SELECT * FROM jobs WHERE id=?", (job_id,)).fetchone()
    return dict(row)


def complete_job(job_id: str, user_id: str) -> dict:
    with closing(connect()) as conn, conn:
        conn.execute("BEGIN IMMEDIATE")
        job = conn.execute("SELECT * FROM jobs WHERE id=? AND user_id=?", (job_id, user_id)).fetchone()
        if not job:
            raise KeyError(job_id)
        if job["status"] == "completed":
            return dict(job)
        conn.execute(
            "INSERT OR IGNORE INTO ledger(user_id,kind,mg,operation_id,job_id,actor,reason,created_at) "
            "VALUES(?,?,?,?,?,?,?,?)",
            (user_id, "commit", 0, f"job:{job_id}:commit", job_id, user_id, "print completed", now()),
        )
        conn.execute(
            "UPDATE jobs SET status='completed',completed_at=? WHERE id=?",
            (now(), job_id),
        )
        row = conn.execute("SELECT * FROM jobs WHERE id=?", (job_id,)).fetchone()
    return dict(row)


def cancel_job(job_id: str, user_id: str) -> dict:
    with closing(connect()) as conn, conn:
        conn.execute("BEGIN IMMEDIATE")
        job = conn.execute("SELECT * FROM jobs WHERE id=? AND user_id=?", (job_id, user_id)).fetchone()
        if not job:
            raise KeyError(job_id)
        if job["status"] in {"completed", "cancelled"}:
            return dict(job)
        if job["free_print"]:
            conn.execute("UPDATE wallets SET first_print_used=0,updated_at=? WHERE user_id=?", (now(), user_id))
            mg = 0
        else:
            mg = int(job["reserved_mg"])
            if mg:
                conn.execute(
                    "UPDATE wallets SET balance_mg=balance_mg+?,updated_at=? WHERE user_id=?",
                    (mg, now(), user_id),
                )
        conn.execute(
            "INSERT OR IGNORE INTO ledger(user_id,kind,mg,operation_id,job_id,actor,reason,created_at) "
            "VALUES(?,?,?,?,?,?,?,?)",
            (user_id, "release", mg, f"job:{job_id}:release", job_id, user_id, "print cancelled", now()),
        )
        conn.execute("UPDATE jobs SET status='cancelled' WHERE id=?", (job_id,))
        row = conn.execute("SELECT * FROM jobs WHERE id=?", (job_id,)).fetchone()
    return dict(row)


def add_collection(user_id: str, job_id: str, name: str, mass_mg: int, model_path: str) -> dict:
    with closing(connect()) as conn, conn:
        conn.execute(
            "INSERT OR IGNORE INTO collection(user_id,job_id,name,mass_mg,model_path,created_at) "
            "VALUES(?,?,?,?,?,?)",
            (user_id, job_id, name, mass_mg, model_path, now()),
        )
        row = conn.execute(
            "SELECT * FROM collection WHERE user_id=? AND job_id=?", (user_id, job_id)
        ).fetchone()
    return dict(row)


def list_collection(user_id: str = DEMO_USER) -> list[dict]:
    with closing(connect()) as conn, conn:
        rows = conn.execute(
            "SELECT * FROM collection WHERE user_id=? ORDER BY id DESC", (user_id,)
        ).fetchall()
    return [dict(r) for r in rows]

