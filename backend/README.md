# PrintVerse Backend

FastAPI + SQLite implementation of the phase-2 virtual print loop.

## Run

```powershell
.\.venv\Scripts\python.exe -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```

The database is created at `database/printverse.db`; upload jobs and generated files live under
`runtime/` (Git-ignored). The frontend defaults to `http://127.0.0.1:8000`.

## Endpoints

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/health` | health |
| GET | `/api/machine` | 275/280 resolved parameters |
| GET | `/api/wallet` | virtual grams, first-print flag, ledger |
| POST | `/api/jobs` | multipart STL → real OrcaSlicer slice → toolpath |
| GET | `/api/jobs/{id}` | job + wallet |
| POST | `/api/jobs/{id}/complete` | commit completion (idempotent) |
| POST | `/api/jobs/{id}/cancel` | release reservation |
| GET/POST | `/api/collection` | list / save finished object |

## Safety

No payment provider, no card data, no real printer. Uploaded STLs are sliced locally with the
same Orca profiles used by the phase-1 test; the resulting G-code is parsed to a compact
toolpath, never executed on hardware.

## Tests

```powershell
.\.venv\Scripts\python.exe -m pytest backend\tests -q -p no:cacheprovider
```

6 ledger/collection tests pass (first free, refund, idempotency, insufficient balance, admin).
