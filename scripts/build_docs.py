#!/usr/bin/env python3
"""Build the official-docs mirror: selected Markdown sources + rendered HTML + index."""
from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

from markdown_it import MarkdownIt

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs" / "official-docs"

VORON = DOCS / "Voron-Documentation-main"
KLIPPER = ROOT / "assets/source/voron-v2.4r2-300/Firmware/klipper-0.13.0/docs"
MOONRAKER = ROOT / "assets/source/voron-v2.4r2-300/Firmware/moonraker-0.11.0/docs"

MAPPING = [
    ("Voron", "Mechanical assembly overview", VORON / "build/mechanical/index.md", "build/mechanical/index.md", "https://docs.vorondesign.com/build/mechanical/"),
    ("Voron", "V2 gantry squaring", VORON / "build/mechanical/v2_gantry_squaring.md", "build/mechanical/v2_gantry_squaring.md", "https://docs.vorondesign.com/build/mechanical/v2_gantry_squaring.html"),
    ("Voron", "Software configuration", VORON / "build/software/configuration.md", "build/software/configuration.md", "https://docs.vorondesign.com/build/software/configuration.html"),
    ("Voron", "First print", VORON / "build/slicer/first_print.md", "build/slicer/first_print.md", "https://docs.vorondesign.com/build/slicer/first_print.html"),
    ("Voron", "Tuning overview", VORON / "tuning/index.md", "tuning/index.md", "https://docs.vorondesign.com/tuning/"),
    ("Voron", "Filament tuning", VORON / "tuning/filament_tuning.md", "tuning/filament_tuning.md", "https://docs.vorondesign.com/tuning/filament_tuning.html"),
    ("Voron", "Sensorless homing", VORON / "tuning/sensorless.md", "tuning/sensorless.md", "https://docs.vorondesign.com/tuning/sensorless.html"),
    ("Voron", "Sourcing", VORON / "sourcing.md", "sourcing.md", "https://docs.vorondesign.com/sourcing.html"),
    ("Voron", "Materials", VORON / "materials.md", "materials.md", "https://docs.vorondesign.com/materials.html"),
    ("Voron", "Maintenance", VORON / "maintenance.md", "maintenance.md", "https://docs.vorondesign.com/maintenance.html"),
    ("Klipper", "Configuration reference", KLIPPER / "Config_Reference.md", "Config_Reference.md", "https://www.klipper3d.org/Config_Reference.html"),
    ("Klipper", "G-code commands", KLIPPER / "G-Codes.md", "G-Codes.md", "https://www.klipper3d.org/G-Codes.html"),
    ("Klipper", "Example configurations", KLIPPER / "Example_Configs.md", "Example_Configs.md", "https://www.klipper3d.org/Example_Configs.html"),
    ("Klipper", "Kinematics", KLIPPER / "Kinematics.md", "Kinematics.md", "https://www.klipper3d.org/Kinematics.html"),
    ("Klipper", "Bed mesh", KLIPPER / "Bed_Mesh.md", "Bed_Mesh.md", "https://www.klipper3d.org/Bed_Mesh.html"),
    ("Klipper", "Configuration checks", KLIPPER / "Config_checks.md", "Config_checks.md", "https://www.klipper3d.org/Config_checks.html"),
    ("Klipper", "Command templates", KLIPPER / "Command_Templates.md", "Command_Templates.md", "https://www.klipper3d.org/Command_Templates.html"),
    ("Klipper", "API server", KLIPPER / "API_Server.md", "API_Server.md", "https://www.klipper3d.org/API_Server.html"),
    ("Moonraker", "API introduction", MOONRAKER / "external_api/introduction.md", "external_api/introduction.md", "https://moonraker.readthedocs.io/en/latest/external_api/introduction/"),
    ("Moonraker", "Printer API", MOONRAKER / "external_api/printer.md", "external_api/printer.md", "https://moonraker.readthedocs.io/en/latest/external_api/printer/"),
    ("Moonraker", "Server API", MOONRAKER / "external_api/server.md", "external_api/server.md", "https://moonraker.readthedocs.io/en/latest/external_api/server/"),
    ("Moonraker", "File manager API", MOONRAKER / "external_api/file_manager.md", "external_api/file_manager.md", "https://moonraker.readthedocs.io/en/latest/external_api/file_manager/"),
    ("Moonraker", "Job queue API", MOONRAKER / "external_api/job_queue.md", "external_api/job_queue.md", "https://moonraker.readthedocs.io/en/latest/external_api/job_queue/"),
    ("Moonraker", "Authorization", MOONRAKER / "external_api/authorization.md", "external_api/authorization.md", "https://moonraker.readthedocs.io/en/latest/external_api/authorization/"),
    ("Moonraker", "JSON-RPC notifications", MOONRAKER / "external_api/jsonrpc_notifications.md", "external_api/jsonrpc_notifications.md", "https://moonraker.readthedocs.io/en/latest/external_api/jsonrpc_notifications/"),
]

HTML = """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title} · PrintVerse official docs</title>
<style>
:root{{--ink:#15212b;--muted:#607180;--line:#dce5eb;--accent:#0b7a66;--bg:#fbfdfe}}
body{{margin:0;background:var(--bg);color:var(--ink);font:16px/1.65 -apple-system,'Segoe UI',sans-serif}}
main{{max-width:960px;margin:0 auto;padding:44px 26px 80px}}
.meta{{font:12px ui-monospace,Consolas,monospace;color:var(--muted);border-bottom:1px solid var(--line);padding-bottom:16px;margin-bottom:28px}}
a{{color:var(--accent)}} h1,h2,h3{{line-height:1.25;letter-spacing:-.02em}} h1{{font-size:34px}}
pre{{background:#101a22;color:#dcecf5;padding:16px;border-radius:10px;overflow:auto}} code{{font-family:ui-monospace,Consolas,monospace;font-size:13px}}
table{{border-collapse:collapse;width:100%;font-size:14px}} th,td{{border:1px solid var(--line);padding:7px 9px;text-align:left}} th{{background:#eef4f7}}
blockquote{{border-left:3px solid var(--accent);margin-left:0;padding-left:16px;color:var(--muted)}}
</style></head><body><main>
<div class="meta">{vendor} · source: <a href="{source}">{source}</a> · retrieved {date} · license recorded in LICENSE_AUDIT.csv</div>
{body}
</main></body></html>"""


def main() -> int:
    md = MarkdownIt("commonmark", {"html": True, "linkify": True}).enable("table").enable("strikethrough")
    entries = []
    now = datetime.now(timezone.utc).isoformat()
    for vendor, title, src, rel, url in MAPPING:
        if not src.exists():
            print(f"MISSING {src}")
            continue
        dest_dir = DOCS / vendor / Path(rel).parent
        dest_dir.mkdir(parents=True, exist_ok=True)
        md_path = DOCS / vendor / rel
        shutil.copy2(src, md_path)
        text = src.read_text(encoding="utf-8", errors="replace")
        body = md.render(text)
        html_path = md_path.with_suffix(".html")
        html_path.write_text(HTML.format(title=title, vendor=vendor, source=url, date=now[:10], body=body), encoding="utf-8")
        entries.append({"vendor": vendor, "title": title, "markdown": str(md_path.relative_to(ROOT)).replace("\\", "/"),
                        "html": str(html_path.relative_to(ROOT)).replace("\\", "/"), "source_url": url,
                        "bytes": md_path.stat().st_size, "retrieved_at": now})
        print(f"OK {vendor}: {title} -> {md_path.relative_to(ROOT)}")
    (DOCS / "sources.json").write_text(json.dumps({"retrieved_at": now, "documents": entries}, indent=2), encoding="utf-8")
    lines = ["# Official Documentation Mirror", "", f"Retrieved: {now[:10]}", "",
             "Selected public sources, mirrored as Markdown with a generated HTML view. The original",
             "assembly manuals remain under `assets/source/voron-v2.4r2-300/Manual/`.", "",
             "| Vendor | Document | Markdown | HTML | Source |", "|---|---|---|---|---|"]
    for e in entries:
        lines.append(f"| {e['vendor']} | {e['title']} | [{Path(e['markdown']).name}]({e['markdown']}) | [{Path(e['html']).name}]({e['html']}) | [official]({e['source_url']}) |")
    lines += ["", "## Manuals and firmware", "",
              "- `assets/source/voron-v2.4r2-300/Manual/Assembly_Manual_2.4r2.pdf`",
              "- `assets/source/voron-v2.4r2-300/Manual/Assembly_Manual_2.4r2_highcontrast.pdf`",
              "- `assets/source/voron-v2.4r2-300/Firmware/klipper-0.13.0/`",
              "- `assets/source/voron-v2.4r2-300/Firmware/moonraker-0.11.0/`",
              "- `assets/source/voron-v2.4r2-300/Firmware/voron-official/`", ""]
    (DOCS / "INDEX.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {DOCS / 'INDEX.md'} ({len(entries)} documents)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
