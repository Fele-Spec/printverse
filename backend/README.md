# Backend

The bootstrap installs FastAPI 0.162, Pydantic 2.14 and Uvicorn 0.54 but intentionally does
not implement product endpoints yet. Start with the contracts in
`../docs/architecture/SYSTEM_OVERVIEW.md` and the accounting schema in
`../.dsh/skills/printverse-filament-accounting/SKILL.md`.

Planned first vertical slice:

1. `GET /health` and `GET /api/machine` (read the resolved Voron profile).
2. Upload → mesh preflight job.
3. Slice job → parsed toolpath JSON.
4. Reserve/commit/release ledger operations with idempotency.
5. Read-only Moonraker fixture adapter; no control endpoints.

Do not add payment processing or real printer control without explicit authorization.
