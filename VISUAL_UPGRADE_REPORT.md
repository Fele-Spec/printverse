# Visual Upgrade Report

Date: 2026-11-06 · Phase 3 visual pass

## 1. Before

The phase-2 scene was a kinematic proxy:

- 460×460×480 frame built from 2020 box primitives.
- Toolhead was a stack of boxes/cylinders; gantry rails were boxes.
- One camera composition, one flat key light, a point light and a low-opacity panel slab.
- No part identity, no module switching, no explode, no orthographic mode, no selection.
- Bed top was a 1,156-face real STEP mesh, but the rest was proxy.

Before screenshots: `BEFORE_AFTER_SCREENSHOTS/before_front.png`, `before_side.png`,
`before_interior.png`, `before_top.png`.

## 2. After

### Real geometry

- Eight module GLBs generated from 4,526 FreeCAD placements:
  `FRAME`, `ENCLOSURE`, `XY_GANTRY`, `Z_DRIVE`, `TOOLHEAD`, `BUILD_PLATFORM`, `ELECTRONICS`,
  `WIRING`.
- 1,686 shape-bearing parts, 1,939,867 full triangles; per-part node names, placement IDs,
  paths, materials and dimensions.
- Default render LOD: 497,199 triangles, 8 merged module meshes with face-range picking.
- High-detail mode: full 1,686-node meshes for Toolhead/Interior views.

### Lighting and material

- ACES Filmic tone mapping, exposure 1.42, sRGB output.
- Procedural studio environment with four Lightformers; key/fill/rim directions.
- Static contact shadow pass, 1024 shadow map.
- Twelve-entry `MATERIAL_LIBRARY.json`: anodized/brushed aluminum, stainless, black oxide,
  rubber, engineering plastic, acrylic, textured print surface, brass, silicone, painted and
  powder-coated surfaces.
- Module material groups are deliberately distinct; glass enclosure is a single transparent
  material with no per-panel transmission recompilation.
- Floor, grid and product plinth are toned down; no fluorescent accent wash.

### Camera and view presets

Six presets: Product, Engineering, Interior, Toolhead, Top, Exploded. Perspective and orthographic
cameras are both implemented; OrbitControls damping, target locking and near/far ranges.
The CAD mode uses a different target Z than the proxy so the real assembly is not cropped.

### Interaction

- Click any merged module face → face-range lookup → placement record.
- Inspector shows part name, module, material, dimensions, placement ID, full source path.
- Green selection box around the picked part.
- Hide module / Focus actions.
- Module visibility toggles for all eight modules.
- Enclosure modes: smoked glass / clear / hidden.
- Explode slider and animated module offsets; Explode preset auto-sets 65%.
- CAD / SIM toggle. Starting a print switches to the simulation tree so the real G-code
  animation remains intact.

After screenshots: `BEFORE_AFTER_SCREENSHOTS/after_front.png`, `after_interior.png`,
`after_toolhead.png`, `after_top.png`, `after_z.png`, `after_bed.png`, `after_clear.png`,
`after_exploded.png`, `after_part_inspector.png`, `after_cad_product.png`, `after_printing_cad.png`.

## 3. Honest comparison

| Area | Before | After |
|---|---|---|
| Frame | box extrusion placeholder | real FreeCAD frame/extrusion parts, corner plates, fasteners |
| Panels | three flat transparent slabs | real panel/door geometry from ENCLOSURE module |
| XY gantry | two box rails | real rails, carriages, idlers, belts, motors |
| Toolhead | box + cylinder stack | full Clockwork/Dragon/Fan toolhead mesh in high detail |
| Z drive | four cylinders + box | real Z assembly, rails, screws, motors |
| Bed | real STEP plate | real BUILD_PLATFORM module with plate/heater/supports |
| Materials | one generic metal look | module material groups + 12-material library |
| Lighting | key + point | studio key/fill/rim + environment + contact shadow |
| Camera | one composition | six presets, perspective/ortho |
| Part identity | none | clickable placement with dimensions/path |
| Transparency | fixed panel slab | glass/clear/hidden modes |
| Explode | none | slider + preset |
| Motion | proxy tree | real CAD toolhead and platform move with G-code; XY crossbeam static |

## 4. Still not complete

1. The real CAD toolhead and BUILD_PLATFORM now follow the G-code. The XY crossbeam is still
   part of a static merged module, so the CoreXY gantry motion is **PARTIAL**.
2. LOD is visible at close range on non-Toolhead modules; full detail is loaded only for
   Toolhead/Interior.
3. `InstancedMesh` is not implemented; fasteners are merged into the LOD.
4. The procedural environment is not a captured HDR; it is a lightformer studio, which is
   adequate but not photogrammetric.
5. The raw assembly has no UV/texture maps; normal maps and texture atlases are not yet authored.
6. One zero-volume compound (`F0490`) is retained and may show an inverted detail.

These are stated in the final phase status rather than hidden.
