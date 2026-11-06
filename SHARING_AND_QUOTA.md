# Sharing and Quota Guide

## 1. Where the interface is

- Source: `frontend/`
- Built UI: `frontend/dist/`
- `frontend/dist/index.html` — **do not double-click it**; ES modules, relative assets and the API need an HTTP origin.
- API: `backend/`

Run locally:

```powershell
# terminal 1
.\.venv\Scripts\python.exe -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000

# terminal 2
npm run preview --prefix frontend
# open http://127.0.0.1:4173/
```

Current services: frontend `http://127.0.0.1:4173/`, API `http://127.0.0.1:8000/`.

## 2. Sharing and quota — implemented as opt-in

The default is still the single-user demo, so the existing E2E tests remain valid. Set:

```powershell
$env:PRINTVERSE_SHARE_MODE="1"
$env:PRINTVERSE_CORS_ORIGINS="http://192.168.1.50:4173"
.\.venv\Scripts\python.exe -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000

# frontend on the LAN (use a firewall rule / private network)
npm run dev --prefix frontend -- --host 0.0.0.0
# build remote UI with:
$env:VITE_API_BASE="http://192.168.1.50:8000"
npm run build --prefix frontend
```

Behavior in shared mode:

| Client | Identity | Quota |
|---|---|---|
| `127.0.0.1` / `::1` (owner's machine) | `owner`, role `admin` | **unlimited**, admin ledger bypass |
| Other LAN address | `guest`, role `user` | **20 g** wallet, first-print-free **disabled** |
| Guest with `PV_GUEST_TOKEN` set | guest only when `X-PV-Member` matches | same guest quota |

Set `PRINTVERSE_SHARE_MODE=0` (default) to return to the original demo identity.

Tests: `backend/tests/test_share.py` verifies owner/guest selection, 20 g guest wallet, disabled
first-free, and optional member-token rejection. Full backend suite: **12 passed**.

## 3. Security boundaries

This is **not password authentication**. Owner identity is based on the TCP loopback source;
guest identity is quota-limited. Before sharing beyond a trusted LAN:

1. Put the API and UI behind **Tailscale Funnel / Cloudflare Tunnel / Caddy with HTTPS**.
2. Terminate authentication at the proxy; do not expose uvicorn directly.
3. Do **not** let a proxy rewrite all remote traffic to `127.0.0.1`; that would make every
   visitor an owner.
4. Set a strong `PV_GUEST_TOKEN` if invite-only access is required.
5. Keep the Kimi/TokenHub keys server-side; never send them to the browser.
6. Rate-limit the API and back up `database/printverse.db`.
7. Never expose the current unauthenticated default mode.

The ledger already distinguishes `owner`/`guest`; the owner is loopback-only in shared mode.
The current default remains demo for backward compatibility, so **do not describe the default
localhost URL as a public share link**.

## 4. Image-to-3D and sharing

The Image → 3D studio calls the same backend identity resolver. Provider keys live only in
`.env.local` on the server. Cloud generation still requires explicit per-request authorization
and a positive CNY budget; guests cannot silently trigger paid calls.
