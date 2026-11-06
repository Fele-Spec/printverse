"""Headless Blender validation: STL import, GLB export and 3D Print Toolbox checks."""
import bpy
import json
import os

ROOT = r"C:\Users\someb\Desktop\printverse"
STL = os.path.join(ROOT, "assets", "source", "voron-v2.4r2-300", "STLs", "Test_Prints", "Filament_Card.stl")
GLB = os.path.join(ROOT, "assets", "processed", "filament_card.glb")
OUT = os.path.join(ROOT, "docs", "reports", "blender_validation.json")

bpy.ops.wm.read_factory_settings(use_empty=True)
module = "bl_ext.user_default.print3d_toolbox"
addon_enabled = False
addon_error = None
try:
    bpy.ops.preferences.addon_enable(module=module)
    addon_enabled = module in bpy.context.preferences.addons
except Exception as exc:
    addon_error = repr(exc)

bpy.ops.wm.stl_import(filepath=STL)
obj = [o for o in bpy.context.scene.objects if o.type == "MESH"][0]
bpy.context.view_layer.objects.active = obj
obj.select_set(True)
mesh = obj.data
check_result = None
check_error = None
try:
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    check_result = str(bpy.ops.mesh.print3d_check_all())
    bpy.ops.object.mode_set(mode="OBJECT")
except Exception as exc:
    check_error = repr(exc)
    try:
        bpy.ops.object.mode_set(mode="OBJECT")
    except Exception:
        pass

bpy.ops.export_scene.gltf(filepath=GLB, export_format="GLB", use_selection=True)
report = {
    "blender": bpy.app.version_string,
    "addon": module,
    "addon_enabled": addon_enabled,
    "addon_error": addon_error,
    "print3d_check_all_available": hasattr(bpy.ops.mesh, "print3d_check_all"),
    "print3d_check_result": check_result,
    "print3d_check_error": check_error,
    "mesh": obj.name,
    "vertices": len(mesh.vertices),
    "polygons": len(mesh.polygons),
    "dimensions_mm": [round(float(x), 3) for x in obj.dimensions],
    "glb": GLB,
    "glb_bytes": os.path.getsize(GLB),
}
with open(OUT, "w", encoding="utf-8") as f:
    json.dump(report, f, indent=2)
print(json.dumps(report, indent=2))
