#!/usr/bin/env python3
"""Apply the narrow Vite-on-Windows sandbox workaround.

Vite calls `exec('net use')` during its first Windows realpath lookup. This DSH
workspace sandbox denies that child process with EPERM, which aborts both build and
preview. The fallback Vite already has for EISDIR is `fs.realpathSync`; we select it
directly. This changes only the installed tool copy, never project source data.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "frontend" / "node_modules" / "vite" / "dist" / "node" / "chunks" / "node.js"

if not TARGET.exists():
    print(f"SKIP: {TARGET} not present")
    raise SystemExit(0)

text = TARGET.read_text(encoding="utf-8")
old = "\t\toptimizeSafeRealPathSync();\n"
new = "\t\tsafeRealpathSync = fs.realpathSync;\n"
if old in text:
    TARGET.write_text(text.replace(old, new, 1), encoding="utf-8")
    print(f"PATCHED: {TARGET}")
elif new in text:
    print(f"ALREADY PATCHED: {TARGET}")
else:
    print("FAIL: expected Vite realpath call not found")
    raise SystemExit(1)
