"""PostgreSQL integration tests.

Skipped by default because SQLite is the zero-config local backend. Run with:
  $env:PRINTVERSE_DATABASE_URL="postgresql://printverse@127.0.0.1:55432/printverse"
  .\\.venv\\Scripts\\python.exe -m pytest backend/tests/test_postgres.py -q
"""
from __future__ import annotations

import os
import uuid

import pytest

from backend.app import db

pytestmark = pytest.mark.skipif(
    not os.environ.get("PRINTVERSE_DATABASE_URL", "").startswith("postgres"),
    reason="PostgreSQL integration test requires PRINTVERSE_DATABASE_URL",
)


def _user(role: str = "user", balance_mg: int = 100_000, used: int = 0) -> str:
    uid = f"pgtest-{uuid.uuid4().hex[:10]}"
    with db.connect() as conn:
        conn.execute("INSERT INTO users(id,name,role,created_at) VALUES(%s,%s,%s,%s)",
                     (uid, uid, role, db.now()))
        conn.execute("INSERT INTO wallets(user_id,balance_mg,first_print_used,updated_at) VALUES(%s,%s,%s,%s)",
                     (uid, balance_mg, used, db.now()))
    return uid


def _job(uid: str, mass_mg: int = 3978) -> str:
    job_id = db.create_job(uid, "pg-cube.stl", "runtime/pg-cube.stl")
    db.set_job_sliced(job_id, "runtime/pg.gcode", "runtime/pg.json", mass_mg, 1192, 100)
    return job_id


def test_postgres_roundtrip_and_first_free():
    db.init_db()
    uid = _user()
    j = _job(uid)
    row = db.reserve_for_job(j, uid, 3978)
    assert row["free_print"] == 1 and row["reserved_mg"] == 0
    assert db.wallet(uid)["first_print_available"] is False
    db.complete_job(j, uid)
    db.complete_job(j, uid)  # idempotent
    item = db.add_collection(uid, j, "pg-cube.stl", 3978, "runtime/pg.stl")
    assert item["job_id"] == j
    assert db.wallet(uid)["balance_mg"] == 100_000


def test_postgres_second_print_charges_and_cancel_refunds():
    db.init_db()
    uid = _user()
    j1 = _job(uid)
    db.reserve_for_job(j1, uid, 3978)
    db.complete_job(j1, uid)
    j2 = _job(uid)
    db.reserve_for_job(j2, uid, 3978)
    assert db.wallet(uid)["balance_mg"] == 96_022
    db.cancel_job(j2, uid)
    assert db.wallet(uid)["balance_mg"] == 100_000


def test_postgres_admin_is_unlimited():
    db.init_db()
    uid = _user("admin", 0, 0)
    j = _job(uid, 50_000)
    row = db.reserve_for_job(j, uid, 50_000)
    assert row["free_print"] == 0 and row["reserved_mg"] == 0
    assert db.wallet(uid)["balance_mg"] == 0
    assert db.wallet(uid)["first_print_available"] is True
