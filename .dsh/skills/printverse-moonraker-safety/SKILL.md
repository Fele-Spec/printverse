---
name: printverse-moonraker-safety
description: Research and integrate Moonraker/Klipper APIs under a strict read-only, no-real-printer boundary. Use when inspecting HTTP/WebSocket endpoints, designing printer status models, or reviewing authentication and job-control safety before any hardware connection.
whenToUse: A task mentions Moonraker, Klipper, printer status, job pause/resume/cancel, API keys, device connection, or exposing a printer service.
metadata:
  version: "0.1.0"
  owner: PrintVerse
  license: MIT
  requires: [moonraker docs, klipper docs, backend, http-client]
---

# PrintVerse Moonraker Safety

## Current phase boundary

- No connection to a real printer.
- No heating, motion, firmware, or print-job command.
- No public exposure of Moonraker.
- No credential collection in this bootstrap.
- Research uses documentation and fixtures only.

## Read-only API surface for the digital twin

| Purpose | Endpoint | Method |
|---|---|---|
| Server identity/version | `/printer/info` | GET |
| Object/status snapshot | `/printer/objects/query?...` | GET |
| G-code file list | `/server/files/list` | GET |
| File metadata | `/server/files/metadata?filename=...` | GET |
| Job queue (read) | `/server/job_queue/status` | GET |
| Server config (redacted) | `/server/config` | GET |
| Websocket status | `/websocket` | WS subscribe |

Do not call mutating endpoints (`/printer/print/start`, `/pause`, `/resume`, `/cancel`,
`/printer/gcode/script`, `/machine/...`, firmware update, power device) in this phase.

## Security rules

1. Bind Moonraker to loopback or a trusted LAN only; never `0.0.0.0` on a public interface.
2. Treat the API key as a secret; never log it, commit it, or place it in a URL query.
3. Use TLS or an SSH tunnel for remote access; do not disable certificate verification.
4. Allowlist endpoints and HTTP methods in the backend client.
5. Apply a hard timeout and a maximum response size.
6. A paused/cancelled job is still a real machine action; require explicit user authorization
   and a physical safety check.
7. Never auto-retry a motion/heater command after a timeout; the command may have executed.

## Integration design

- Normalize status into `PrinterSnapshot`: state, temperatures, position, speed factor,
  job filename, progress, print duration, estimated remaining time, and errors.
- Keep a fixture-based mock server for frontend development.
- Separate `read_only` and `control` clients; the control client is disabled by default.
- Record every control request in an append-only audit log with actor, intent, and result.

## Failure handling

| Symptom | Action |
|---|---|
| 401/403 | check key scope; do not retry with another credential |
| websocket disconnect | back off; do not replay control commands |
| unknown printer state | surface `UNKNOWN`, block simulation-to-real promotion |
| request timeout | treat as indeterminate; never silently retry a mutation |

## Acceptance

A read-only snapshot can be produced from a fixture; the client cannot issue a mutating
request; secrets are absent from logs and Git; the public-exposure check fails closed.
