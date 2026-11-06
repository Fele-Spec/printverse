#!/usr/bin/env python3
"""Render BOM snapshots (PDF, PNG table, HTML) from the official-configurator replay.

The generated page and PDF are paired with a real browser screenshot at
assets/previews/BOM_300MM_browser.png; the official configurator UI itself is not automated.
"""
from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.patches import Rectangle

ROOT = Path(__file__).resolve().parents[1]
BOM_JSON = ROOT / "assets/source/voron-v2.4r2-300/BOM/BOM_300MM.json"
CSV = ROOT / "BOM_300MM.csv"
PREVIEW = ROOT / "assets/previews"
PREVIEW.mkdir(parents=True, exist_ok=True)
NOW = datetime.now(timezone.utc).isoformat()

data = json.loads(BOM_JSON.read_text(encoding="utf-8"))
rows = []
with CSV.open(encoding="utf-8-sig", newline="") as f:
    for r in csv.DictReader(f):
        rows.append(r)
cfg = data["config"]
geo = data["derived_geometry_mm"]


def page(pdf, chunk, page_no, total_pages):
    fig = plt.figure(figsize=(8.27, 11.69), dpi=160)
    fig.patch.set_facecolor("#f7fafb")
    ax = fig.add_axes([0.05, 0.05, 0.9, 0.9])
    ax.axis("off")
    ax.text(0, 1.02, "PRINTVERSE / VORON V2.4r2 300", fontsize=9, color="#0b7a66",
            family="DejaVu Sans Mono", weight="bold")
    ax.text(0, 0.985, "300 mm Custom BOM", fontsize=24, color="#15212b", weight="bold")
    ax.text(0, 0.958, "Official configurator replay  ·  New Build  ·  Direct Feed  ·  Blind Joints  ·  Generic Cable Chains",
            fontsize=8.5, color="#607180")
    ax.text(0, 0.942, f"Build {geo['build_volume']['x']} × {geo['build_volume']['y']} × {geo['build_volume']['z']} mm   |   "
                       f"Frame {geo['frame_outer']['x']} × {geo['frame_outer']['y']} × {geo['frame_outer']['z']} mm   |   "
                       f"Page {page_no}/{total_pages}", fontsize=8, color="#607180", family="DejaVu Sans Mono")
    ax.add_patch(Rectangle((0, 0.925), 1, 0.002, transform=ax.transAxes, color="#0b7a66", lw=0))
    table_rows = [[r["Category"], r["Part Description"], r["Qty"]] for r in chunk]
    table = ax.table(cellText=table_rows, colLabels=["Category", "Part description", "Qty"],
                     colWidths=[0.19, 0.70, 0.08], loc="upper left", cellLoc="left",
                     bbox=[0, 0.02, 1, 0.88])
    table.auto_set_font_size(False)
    table.set_fontsize(7.4)
    for (row_i, col_i), cell in table.get_celld().items():
        cell.set_edgecolor("#dbe5ea")
        cell.set_linewidth(0.5)
        if row_i == 0:
            cell.set_facecolor("#15212b")
            cell.set_text_props(color="white", weight="bold")
        else:
            cell.set_facecolor("#ffffff" if row_i % 2 else "#eef5f7")
        if col_i == 2:
            cell.set_text_props(ha="center")
    fig.text(0.05, 0.02, "Derived from https://www.vorondesign.com/voron2.4 JavaScript; official quantities preserved. "
                         "Fastener quantities are minimums. Generated preview, not a browser screenshot.",
             fontsize=6.6, color="#607180")
    pdf.savefig(fig, facecolor=fig.get_facecolor())
    plt.close(fig)


per_page = 32
chunks = [rows[i:i + per_page] for i in range(0, len(rows), per_page)]
pdf_path = ROOT / "BOM_300MM.pdf"
with PdfPages(pdf_path) as pdf:
    for i, chunk in enumerate(chunks, 1):
        page(pdf, chunk, i, len(chunks))

# PNG preview of page 1, generated directly at high resolution.
fig = plt.figure(figsize=(8.27, 11.69), dpi=150)
fig.patch.set_facecolor("#f7fafb")
ax = fig.add_axes([0.05, 0.05, 0.9, 0.9]); ax.axis("off")
ax.text(0, 1.02, "PRINTVERSE / VORON V2.4r2 300", fontsize=9, color="#0b7a66", family="DejaVu Sans Mono", weight="bold")
ax.text(0, 0.985, "300 mm Custom BOM", fontsize=24, color="#15212b", weight="bold")
ax.text(0, 0.958, "Official configurator replay  ·  New Build  ·  Direct Feed  ·  Blind Joints  ·  Generic Cable Chains", fontsize=8.5, color="#607180")
ax.text(0, 0.942, f"Build {geo['build_volume']['x']} × {geo['build_volume']['y']} × {geo['build_volume']['z']} mm   |   Frame {geo['frame_outer']['x']} × {geo['frame_outer']['y']} × {geo['frame_outer']['z']} mm", fontsize=8, color="#607180", family="DejaVu Sans Mono")
table = ax.table(cellText=[[r["Category"], r["Part Description"], r["Qty"]] for r in chunks[0]],
                 colLabels=["Category", "Part description", "Qty"], colWidths=[0.19, 0.70, 0.08],
                 loc="upper left", cellLoc="left", bbox=[0, 0.02, 1, 0.88])
table.auto_set_font_size(False); table.set_fontsize(7.4)
for (ri, ci), cell in table.get_celld().items():
    cell.set_edgecolor("#dbe5ea"); cell.set_linewidth(0.5)
    if ri == 0: cell.set_facecolor("#15212b"); cell.set_text_props(color="white", weight="bold")
    else: cell.set_facecolor("#ffffff" if ri % 2 else "#eef5f7")
    if ci == 2: cell.set_text_props(ha="center")
fig.savefig(PREVIEW / "BOM_300MM_page1.png", dpi=170, facecolor=fig.get_facecolor())
plt.close(fig)

html_rows = "\n".join(
    f"<tr><td>{r['Category']}</td><td>{r['Part Description']}</td><td class='q'>{r['Qty']}</td></tr>" for r in rows
)
html = f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><title>PrintVerse BOM 300 mm</title>
<style>body{{font:14px/1.5 'Segoe UI',sans-serif;background:#f7fafb;color:#15212b;margin:0;padding:38px}}
main{{max-width:980px;margin:auto}}h1{{font-size:30px;margin:4px 0 2px}}.eyebrow{{font:11px ui-monospace,Consolas;letter-spacing:.16em;color:#0b7a66}}
p{{color:#607180}}.params{{background:#eaf3f4;padding:14px 18px;border-radius:10px;margin:18px 0}}
table{{border-collapse:collapse;width:100%;font-size:12px}}th{{background:#15212b;color:white;text-align:left}}
td,th{{padding:6px 8px;border-bottom:1px solid #dbe5ea}}tr:nth-child(even) td{{background:#eef5f7}}.q{{text-align:center;font-family:ui-monospace,Consolas}}
.note{{font-size:11px;color:#607180;margin-top:18px}}</style></head><body><main>
<div class="eyebrow">PRINTVERSE / VORON V2.4r2 300</div><h1>300 mm Custom BOM</h1>
<div class="params"><b>Official configurator replay:</b> V2.4 · 300 mm Spec · New Build · Direct Feed · Blind Joints · Generic Cable Chains<br>
Build volume {geo['build_volume']['x']} × {geo['build_volume']['y']} × {geo['build_volume']['z']} mm · Frame {geo['frame_outer']['x']} × {geo['frame_outer']['y']} × {geo['frame_outer']['z']} mm · {len(rows)} line items · total quantity {data['total_quantity']}</div>
<table><thead><tr><th>Category</th><th>Part description</th><th>Qty</th></tr></thead><tbody>{html_rows}</tbody></table>
<p class="note">Derived from the public JavaScript at <a href="https://www.vorondesign.com/voron2.4">vorondesign.com/voron2.4</a>;
official quantities preserved. Fastener quantities are minimums. A real browser screenshot is saved at
<code>assets/previews/BOM_300MM_browser.png</code>; the official configurator UI itself is not automated.</p></main></body></html>"""
(ROOT / "BOM_300MM.html").write_text(html, encoding="utf-8")
(PREVIEW / "BOM_300MM_page1.png").replace(PREVIEW / "BOM_300MM_page1.png")
print(f"wrote {pdf_path}, BOM_300MM.html, {PREVIEW / 'BOM_300MM_page1.png'} ({len(rows)} rows)")
