# Sharing and Quota Guide

## 1. Where the interface is

Source and built interface:

- `frontend/` — React/Vite source
- `frontend/dist/` — built static bundle
- `frontend/dist/index.html` — **do not double-click this file**; ES modules, relative assets and the API expect an HTTP origin
- `backend/` — FastAPI service and SQLite ledger

Run locally:

```powershell
# terminal 1
.\.venv\Scripts\python.exe -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000

# terminal 2
npm run preview --prefix frontend
# open http://127.0.0.1:4173/
```

Current services: frontend `http://127.0.0.1:4173/`, API `http://127.0.0.1:8000/`.

## 2. Can it be shared as-is?

**No, not safely.** The current build is a local demo:

- Vite binds `127.0.0.1`, not LAN.
- CORS allows only `127.0.0.1:4173` / `localhost:4173`.
- The frontend hardcodes `http://127.0.0.1:8000`.
- The API has **no login or share token**; `user_id` is a request parameter and defaults to `demo`.
- Every visitor would share the demo wallet, and anyone could spoof another user.
- There is no owner identity, no per-guest quota, no TLS.

Do **not** port-forward the current API to the public internet.

## 3. What is already available for a future share mode

The SQLite layer already has:

- `users.role` with an `admin` role that the filament reservation treats as **unlimited**.
- Per-user `wallets` and append-only `ledger`.
- Per-user jobs and collection.

What is missing:

1. Authentication / session identity (owner vs guest).
2. Per-user API tokens or signed cookies.
3. A guest quota policy separate from the owner wallet.
4. Binding the frontend/API to a LAN or tunnel and CORS allow-list.
5. HTTPS and rate limiting.

## 4. Recommended safe deployment

1. Put frontend + API behind **Tailscale Funnel** or **Cloudflare Tunnel**; do not open router ports.
2. Add a login (owner passkey/password; guest one-time invite links).
3. Seed an `owner` user with `role=admin` and a private token.
4. Seed guest users with `role=user`, a small wallet and no first-print entitlement.
5. Build the frontend with:

```powershell
$env:VITE_API_BASE="https://your-private-api.example"
npm run build --prefix frontend
```

6. Let the backend read `VITE_API_BASE`/CORS origins from environment instead of the hardcoded localhost.
7. Enforce `current_user` server-side; never trust a `user_id` supplied by the browser.

## 5. Current limitation statement

The requested **“owner unlimited on my computer, other people quota-limited”** behavior is **NOT IMPLEMENTED as a share feature** in this build. The ledger supports admin-unlimited semantics, but there is no authentication layer yet. Sharing the current URL would give others the same unauthenticated demo.

The Image-to-3D studio also follows the same boundary: provider keys are server-side only; guest users must never receive them.
