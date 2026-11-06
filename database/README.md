# PrintVerse Database

SQLite is used for the phase-2 demo; migrations are intentionally minimal. Tables are created
by `backend/app/db.py` on startup.

| Table | Purpose |
|---|---|
| `users` | demo/user/admin role |
| `wallets` | virtual balance in integer milligrams + first-print flag |
| `ledger` | append-only reserve/commit/release/grant rows, unique `operation_id` |
| `jobs` | upload, sliced G-code/toolpath paths, mass, layer count, status |
| `collection` | finished objects, unique per (user, job) |

The demo seeds 100,000 mg virtual credit and one free first print. No real payment or physical
spool data is stored. The database file is Git-ignored; it is recreated on a fresh run.
