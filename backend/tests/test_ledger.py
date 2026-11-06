"""Deterministic virtual-ledger tests. No payment provider, no real printer."""
from __future__ import annotations

import uuid

import pytest

from backend.app import db


@pytest.fixture()
def fresh_db(monkeypatch):
    # The DSH sandbox cannot write pytest's default system temp directory; keep the
    # test database beside the project's real database and remove it afterwards.
    p = db.ROOT / "database" / f"test-{uuid.uuid4().hex}.db"
    p.parent.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(db, "DB_PATH", p)
    db.init_db()
    try:
        yield p
    finally:
        for suffix in ("", "-wal", "-shm"):
            try:
                (p.parent / (p.name + suffix)).unlink()
            except (FileNotFoundError, PermissionError):
                # Windows can hold a transient WAL handle briefly; pytest must not fail
                # because of cleanup. The files are removed by the test wrapper.
                pass


def make_job(name="cube.stl", mass_mg=3978):
    job_id = db.create_job(db.DEMO_USER, name, f"runtime/{name}")
    db.set_job_sliced(job_id, f"runtime/{name}.gcode", f"runtime/{name}.json", mass_mg, 1192, 100)
    return job_id


def test_first_print_is_free_once(fresh_db):
    j1 = make_job("one.stl")
    reserved = db.reserve_for_job(j1, db.DEMO_USER, 3978)
    assert reserved["free_print"] == 1
    assert reserved["reserved_mg"] == 0
    assert db.wallet()["balance_mg"] == 100_000
    assert db.wallet()["first_print_available"] is False

    db.complete_job(j1, db.DEMO_USER)
    assert db.wallet()["balance_mg"] == 100_000

    j2 = make_job("two.stl")
    reserved2 = db.reserve_for_job(j2, db.DEMO_USER, 3978)
    assert reserved2["free_print"] == 0
    assert reserved2["reserved_mg"] == 3978
    assert db.wallet()["balance_mg"] == 96_022


def test_cancel_refunds_and_keeps_first_print(fresh_db):
    j = make_job()
    db.reserve_for_job(j, db.DEMO_USER, 3978)
    assert db.wallet()["balance_mg"] == 100_000
    db.cancel_job(j, db.DEMO_USER)
    assert db.wallet()["balance_mg"] == 100_000
    assert db.wallet()["first_print_available"] is True
    assert db.get_job(j)["status"] == "cancelled"


def test_duplicate_reserve_does_not_double_charge(fresh_db):
    j1 = make_job("one.stl")
    db.reserve_for_job(j1, db.DEMO_USER, 3978)  # free
    db.complete_job(j1, db.DEMO_USER)
    j2 = make_job("two.stl")
    db.reserve_for_job(j2, db.DEMO_USER, 3978)
    db.reserve_for_job(j2, db.DEMO_USER, 3978)
    assert db.wallet()["balance_mg"] == 96_022


def test_complete_and_collection_idempotent(fresh_db):
    j = make_job()
    db.reserve_for_job(j, db.DEMO_USER, 3978)
    db.complete_job(j, db.DEMO_USER)
    db.complete_job(j, db.DEMO_USER)
    item1 = db.add_collection(db.DEMO_USER, j, "cube.stl", 3978, "runtime/cube.stl")
    item2 = db.add_collection(db.DEMO_USER, j, "cube.stl", 3978, "runtime/cube.stl")
    assert item1["id"] == item2["id"]
    assert len(db.list_collection()) == 1


def test_insufficient_balance_does_not_charge(fresh_db):
    # Use the first job to consume the free entitlement, then a tiny wallet.
    j1 = make_job("one.stl")
    db.reserve_for_job(j1, db.DEMO_USER, 3978)
    db.complete_job(j1, db.DEMO_USER)
    with db.connect() as conn:
        conn.execute("UPDATE wallets SET balance_mg=1000 WHERE user_id=?", (db.DEMO_USER,))
    j2 = make_job("huge.stl", 50_000)
    with pytest.raises(db.InsufficientFilament):
        db.reserve_for_job(j2, db.DEMO_USER, 50_000)
    assert db.wallet()["balance_mg"] == 1000


def test_admin_unlimited_does_not_touch_first_print(fresh_db):
    with db.connect() as conn:
        conn.execute("INSERT INTO users(id,name,role,created_at) VALUES(?,?,?,?)", ("admin", "Admin", "admin", db.now()))
        conn.execute("INSERT INTO wallets(user_id,balance_mg,first_print_used,updated_at) VALUES(?,0,0,?)", ("admin", db.now()))
    j = db.create_job("admin", "admin.stl", "runtime/admin.stl")
    db.set_job_sliced(j, "runtime/a.gcode", "runtime/a.json", 10_000, 10, 2)
    row = db.reserve_for_job(j, "admin", 10_000)
    assert row["free_print"] == 0 and row["reserved_mg"] == 0
    assert db.wallet("admin")["balance_mg"] == 0
    assert db.wallet("admin")["first_print_available"] is True
