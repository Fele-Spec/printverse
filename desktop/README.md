# PrintVerse Desktop Pet (Tauri)

This is the Windows transparent-window shell for the browser pet view at:

`http://127.0.0.1:4173/?pet=1`

The web app owns the 3D pet, collection and wallet; Tauri only provides the
transparent, borderless, always-on-top window. The URL can be changed in
`src-tauri/tauri.conf.json` to a deployed HTTPS PrintVerse origin.

## Build

Prerequisites:

- Rust stable + Cargo
- Microsoft C++ Build Tools / Windows SDK
- Node.js

```powershell
cd desktop
npm install
npm run dev
# or
npm run build
```

## Current verification

`cargo` is **not installed** in this workspace, so the Windows binary could not be
built or signed in this phase. The Rust/Tauri scaffold and configuration are
present; the browser pet view is testable without Tauri at `/?pet=1`.
