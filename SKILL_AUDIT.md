# PrintVerse Skill Audit

## Registry mechanism (verified)

The active Harness profile carries `@deepseek-ai/dsh-skill-filesystem` (discovery) and
`@deepseek-ai/dsh-tool-skill` (catalog + `skill` loader). Its documented rules:

- A skill is a directory bundle `<root>/<name>/SKILL.md` or a flat `<root>/<name>.md`.
- Discovery is exactly one level deep.
- Roots and priority: `<project>/.dsh/skills` (100), `<project>/.agents/skills` (200),
  custom dirs (300), `~/.dsh/skills` (400), `~/.agents/skills` (500).
- The project root is the nearest ancestor containing `.git`.
- Required frontmatter: `name` (kebab-case) and `description`; optional `whenToUse`,
  `metadata`, `disable-model-invocation`, `user-invocable`.
- Frontmatter changes trigger a catalog refresh; body edits are re-read on every load.

Canonical location for this project: `.dsh/skills/`. `.agents/skills/README.txt` intentionally
contains no skill, to avoid duplicate names.

## Six skills

All six are present, valid, listed in the replacement session catalog, and were loaded through
the `skill` tool at least once.

| Skill | Trigger summary | Frontmatter | Catalog | Loaded | Body |
|---|---|---|---|---|---|
| `printverse-orchestrator` | Phase planning, status, parallelism, cost, safety | valid | yes | yes | 3,834 B |
| `printverse-cad-audit` | STEP/STL/DXF integrity, FreeCAD import, assembly | valid | yes | yes | 3,232 B |
| `printverse-mesh-preflight` | Watertight/normals/non-manifold/repair | valid | yes | yes | 2,789 B |
| `printverse-gcode-simulation` | Orca slicing, parsing, toolpaths, mass/time | valid | yes | yes | 3,371 B |
| `printverse-filament-accounting` | Dual ledger, first print free, admin unlimited | valid | yes | yes | 3,479 B |
| `printverse-moonraker-safety` | Read-only API research, no real printer | valid | yes | yes | 3,125 B |

Machine-readable frontmatter audit: `docs/reports/skill_frontmatter.json` — six records,
zero errors, each with `name`, `description`, `whenToUse`, `metadata`.

## External tool dependencies

| Skill | External commands / libraries | Availability |
|---|---|---|
| orchestrator | filesystem, Git, Python, Node, scripts | present |
| cad-audit | `FreeCADCmd.exe`, `scripts/freecad_validate.py`, `freecad_entry.py` | verified |
| mesh-preflight | `.venv` + trimesh 5.2.0, `scripts/mesh_audit.py` | verified |
| gcode-simulation | OrcaSlicer 2.4.2, `scripts/build_orca_profiles.py`, `parse_gcode.py` | verified |
| filament-accounting | database/backend design only; no payment SDK | no dangerous dependency |
| moonraker-safety | documentation only; no live client in this phase | no printer connection |

## Security review

- No third-party install script was executed to add these skills. They were authored locally.
- No skill downloads or executes remote code as part of loading.
- No credentials, API keys, payment data or printer addresses are stored in any skill.
- The Moonraker skill explicitly forbids mutating endpoints and public exposure in this phase.
- The accounting skill explicitly forbids real payment processing.
- File writes are limited to project paths and `assets/processed/` for repaired meshes.

## Discovery sources searched

- DeepSeek Harness skill subsystem docs embedded in the installed app (`dsh-skill-filesystem`,
  `dsh-tool-skill` READMEs).
- Public GitHub search for PrintVerse/CAD/3D-printing/FreeCAD/G-code agent skills.
- Mature third-party projects found were MCP servers or application plugins, not DSH-format
  `SKILL.md` bundles. No unvetted repository was installed as a skill. The six project-specific
  skills were therefore authored from the verified toolchain rather than copied.

## Limitations / follow-up

- No third-party Skill Registry package was adopted; the local filesystem provider is the
  registry in use.
- Skill bodies contain command paths relative to the project root; the loader reports the
  skill base directory, so an agent must resolve project paths from the repository root.
- The catalog description cap is 500 characters; all six descriptions are below 300 characters.
