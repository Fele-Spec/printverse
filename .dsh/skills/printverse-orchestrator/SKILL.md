---
name: printverse-orchestrator
description: Coordinate PrintVerse bootstrap and development work across CAD, mesh, slicing, G-code simulation, frontend, filament accounting, and Moonraker research. Use when starting or auditing a PrintVerse phase, deciding what can run in parallel, or producing a truthful COMPLETE/PARTIAL/BLOCKED status.
whenToUse: The request concerns PrintVerse project setup, phase planning, verification, deliverable assembly, cost control, or deciding whether work is safe to proceed without a real printer.
metadata:
  version: "0.1.0"
  owner: PrintVerse
  license: MIT
  requires: [filesystem, terminal, git, node, python]
---

# PrintVerse Orchestrator

## Purpose

Keep PrintVerse work reproducible, evidence-based, and inside the project safety boundary.
You are coordinating a digital-twin product, not operating a printer.

## Read first

1. `PRINTVERSE_BOOTSTRAP_REPORT.md`
2. `manifests/resources.json` and `manifests/checksums.sha256`
3. `docs/reports/` for the latest CAD, mesh, G-code and frontend evidence
4. `SKILL_AUDIT.md` for which skills the Harness actually recognized

Never infer success from a file existing. Require a command result, a parsed artifact, or a
checksum recorded in the reports.

## Phase workflow

| Phase | Work | Gate |
|---|---|---|
| P0 | Environment and project scaffold | Git initialized; Python/Node/FreeCAD/Orca paths recorded |
| P1 | Official Voron/Klipper/Moonraker acquisition | Fixed tag/commit; checksums; license rows |
| P2 | CAD and BOM | STEP + STL import evidence; 300 mm BOM traceable to configurator |
| P3 | Slicing and G-code | One real slice; parser reproduces bounds and mass |
| P4 | Frontend digital twin | GLB loads; camera/zoom/name/background controls verified |
| P5 | Skills | Six skills discovered by the Harness and loadable |
| P6 | Accounting and Moonraker design | No real device, payment, or credential side effects |

Do not start P6 hardware work until the user explicitly authorizes a real printer and a
separate safety review.

## Parallelism

Safe to run together:

- downloads of independent official sources
- FreeCAD import and trimesh audit on different files
- Orca slicing and frontend dependency installation
- documentation conversion and license indexing

Do not run together:

- two writers to the same manifest/checksum file
- two Orca instances writing the same output directory
- any real Moonraker request alongside an experiment that assumes no printer

## Cost discipline

- Default to the flash model and low/standard reasoning.
- Raise reasoning only for geometry tolerances, print-time/material models, authentication,
  destructive migrations, or a failure that resisted two normal attempts.
- Reuse report JSON instead of re-reading large CAD/G-code as text.
- Cap ordinary retries at 3; record the exact failure before retrying.
- At the RMB 80 stage threshold, stop optional work and write a cost/status report.
  Never cross RMB 100 without a new explicit budget authorization.

## Failure policy

For each failed step: retry once, try the official alternate route, inspect logs, then mark
the item `BLOCKED` with the command, error, and missing prerequisite. Continue independent
work. Never rewrite a `BLOCKED` item as `COMPLETE`.

## Safety boundary

- No connection to a real printer, no heating, no firmware flashing, no print job.
- No public Moonraker exposure, no real payment, no stored payment credential.
- No bypass of licenses, logins, access controls, or system security.
- Original downloads stay untouched under `assets/source/`; repairs go to
  `assets/processed/`.

## Output contract

Every phase report states: scope, commands run, evidence paths, PASS/FAIL per criterion,
`COMPLETE` / `PARTIAL` / `BLOCKED` / `NOT_STARTED`, unresolved risks, and the next smallest
verifiable step.
