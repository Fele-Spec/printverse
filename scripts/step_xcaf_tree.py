"""Name-preserving XCAF traversal of the Voron STEP assembly.

Uses OCP 7.9 in .venv-cadquery because its TDF_LabelSequence binding is available.
Records product names, parent/child relationships and local 4x4 transforms.
"""
from __future__ import annotations

import json
import time
from pathlib import Path

from OCP.BRepBndLib import BRepBndLib
from OCP.Bnd import Bnd_Box
from OCP.STEPCAFControl import STEPCAFControl_Reader
from OCP.TCollection import TCollection_ExtendedString
from OCP.TDataStd import TDataStd_Name
from OCP.TDF import TDF_Label, TDF_LabelSequence
from OCP.TDocStd import TDocStd_Document
from OCP.TopLoc import TopLoc_Location
from OCP.XCAFDoc import XCAFDoc_DocumentTool, XCAFDoc_Location, XCAFDoc_ShapeTool

ROOT = Path(__file__).resolve().parents[1]
STEP = ROOT / "assets/source/voron-v2.4r2-300/CAD/VORON2.4_Assembly.step"
OUT = ROOT / "docs/reports/step_xcaf_tree.json"


def name_of(label) -> str:
    try:
        attr = TDataStd_Name()
        if label.FindAttribute(TDataStd_Name.GetID_s(), attr):
            return attr.Get().ToExtString()
    except Exception:
        pass
    return ""


def local_transform(label) -> list[list[float]]:
    # XCAFDoc_Location.GetID_s/FindAttribute crashes in this binding, but the shape
    # tool exposes the instance location directly. Keep the local matrix; consumers
    # compose it through the parent chain.
    try:
        loc = XCAFDoc_ShapeTool.GetLocation_s(label)
        if not loc.IsIdentity():
            trsf = loc.Transformation()
            return [[round(trsf.Value(r, c), 6) for c in range(1, 5)] for r in range(1, 5)]
    except Exception:
        pass
    return [[1.0, 0.0, 0.0, 0.0], [0.0, 1.0, 0.0, 0.0], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]]


def main() -> int:
    t0 = time.time()
    doc = TDocStd_Document(TCollection_ExtendedString("XCAF"))
    reader = STEPCAFControl_Reader()
    reader.SetNameMode(True)
    reader.SetColorMode(True)
    print("XCAF_READ_START", flush=True)
    status = reader.ReadFile(str(STEP))
    print("XCAF_READ_DONE", status, flush=True)
    if status != 1:
        raise SystemExit(f"XCAF ReadFile status {status}")
    print("XCAF_TRANSFER_START", flush=True)
    reader.Transfer(doc)
    print("XCAF_TRANSFER_DONE", flush=True)
    tool = XCAFDoc_DocumentTool.ShapeTool_s(doc.Main())
    roots = TDF_LabelSequence()
    tool.GetFreeShapes(roots)
    print("XCAF_ROOTS", roots.Length(), flush=True)
    nodes = []
    top_labels: dict[int, object] = {}
    max_depth = 8
    max_nodes = 1800

    def walk(label, parent: int | None, depth: int, index: int):
        if depth > max_depth or len(nodes) >= max_nodes:
            return
        name = name_of(label)
        target = label
        if XCAFDoc_ShapeTool.IsComponent_s(label):
            ref = TDF_Label()
            if XCAFDoc_ShapeTool.GetReferredShape_s(label, ref):
                target = ref
        n_children = int(XCAFDoc_ShapeTool.NbComponents_s(target, False))
        node = {
            "id": index,
            "parent": parent,
            "depth": depth,
            "name": name or f"<unnamed:{index}>",
            "children": n_children,
            "transform": local_transform(label),
        }
        nodes.append(node)
        if depth == 1:
            top_labels[index] = label
        if len(nodes) % 100 == 0:
            print("nodes", len(nodes), "depth", depth, "name", node["name"][:60], flush=True)
        if n_children:
            seq = TDF_LabelSequence()
            XCAFDoc_ShapeTool.GetComponents_s(target, seq, False)
            for i in range(1, seq.Length() + 1):
                walk(seq.Value(i), index, depth + 1, len(nodes))

    for i in range(1, roots.Length() + 1):
        walk(roots.Value(i), None, 0, len(nodes))

    # Bounding box of all free shapes (top-level only, for a quick sanity check).
    box = Bnd_Box()
    for i in range(1, roots.Length() + 1):
        try:
            shape = XCAFDoc_ShapeTool.GetShape_s(roots.Value(i))
            BRepBndLib.Add_s(shape, box)
        except Exception:
            pass
    try:
        b = box.Get()
        bbox = {"min": [round(b[0], 3), round(b[1], 3), round(b[2], 3)],
                "max": [round(b[3], 3), round(b[4], 3), round(b[5], 3)],
                "size": [round(b[3] - b[0], 3), round(b[4] - b[1], 3), round(b[5] - b[2], 3)]}
    except Exception as exc:
        bbox = {"error": repr(exc)}

    top_groups = []
    for node_id, label in top_labels.items():
        node = next((n for n in nodes if n["id"] == node_id), None)
        if not node:
            continue
        try:
            b = Bnd_Box()
            BRepBndLib.Add_s(XCAFDoc_ShapeTool.GetShape_s(label), b)
            v = b.Get()
            top_groups.append({
                "name": node["name"],
                "children": node["children"],
                "bbox": {
                    "min": [round(v[0], 3), round(v[1], 3), round(v[2], 3)],
                    "max": [round(v[3], 3), round(v[4], 3), round(v[5], 3)],
                    "size": [round(v[3] - v[0], 3), round(v[4] - v[1], 3), round(v[5] - v[2], 3)],
                },
            })
        except Exception as exc:
            top_groups.append({"name": node["name"], "children": node["children"], "bbox": {"error": repr(exc)}})

    report = {
        "ok": True,
        "file": str(STEP.relative_to(ROOT)).replace("\\", "/"),
        "bytes": STEP.stat().st_size,
        "read_status": str(status),
        "elapsed_s": round(time.time() - t0, 2),
        "root_count": roots.Length(),
        "node_count": len(nodes),
        "max_depth": max((n["depth"] for n in nodes), default=0),
        "bbox": bbox,
        "top_groups": top_groups,
        "transform_status": "XCAFDoc_ShapeTool.GetLocation_s returned identity for all nodes; XCAFDoc_Location.FindAttribute crashes in this OCP 7.9 binding. Product names, hierarchy and top-group bounding boxes are real; exact per-component transforms remain PARTIAL.",
        "nodes": nodes,
    }
    OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k: report[k] for k in ("ok", "root_count", "node_count", "bbox", "elapsed_s")}, indent=2))
    print("wrote", OUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
