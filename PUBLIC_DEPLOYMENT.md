# Public Deployment

## Current public URL

**https://troubleshooting-idea-jacket-sleeve.trycloudflare.com**

This is a **Cloudflare Quick Tunnel** to the Docker Compose stack:

```text
Cloudflare HTTPS
  → cloudflared quick tunnel
  → http://127.0.0.1:8080 (Docker web / nginx)
  → printverse-api:8000
  → printverse-postgres:5432
  → printverse-worker
```

## Source repository

**https://github.com/Fele-Spec/printverse**

The existing repository `https://github.com/Fele-Spec/borlin` is a different
SignBridge project and was not modified.

## Verified

- Public `/` → 200
- Public `/api/health` → 200
- Public `/api/wallet` → 200
- Public Image3D Mock job → completed
- Public GLB asset → 200
- Browser page errors: 0

## Important limitation

This is a Quick Tunnel, not a permanent production deployment:

- No uptime guarantee.
- The URL changes whenever cloudflared restarts.
- The Windows machine, WSL2 Ubuntu, Docker daemon, Compose containers and the
  cloudflared process must stay running.
- The demo has no authentication; the public site uses the `demo` virtual wallet.

## Restart

```powershell
# 1. WSL2 + Docker Compose
wsl -d Ubuntu -u root -- bash -lc "nohup sleep infinity >/dev/null 2>&1 & service docker start; cd /mnt/c/Users/someb/Desktop/printverse; docker compose up -d"

# 2. Public tunnel
.\.cache\cloudflared.exe tunnel --url http://127.0.0.1:8080 --no-autoupdate
```

For a permanent URL, use a Cloudflare named tunnel or deploy the Compose stack to
a cloud host with a domain; that requires the relevant account credentials.
