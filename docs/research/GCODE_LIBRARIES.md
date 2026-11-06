# G-code Visualization Library Evaluation

## Shortlist

| Library | Version | License | Runtime | Maintenance | Fit |
|---|---|---|---|---|---|
| `gcode-preview` | 2.18.0 | MIT | Three.js | Active; README updated for 3.x alpha | Strong visual preview, but **supports three >=0.166 <0.186** |
| `gcode-parser` (cncjs) | 2.2.0 | MIT | Node.js | Mature, low activity | Parser only, no renderer |
| `gcode-toolpath` (cncjs) | 3.0.0 | MIT | Node.js | Mature, low activity | Generates toolpaths, no browser viewer |
| Custom Python parser | local | project | Python 3.12 | Owned | Adopted for analysis; outputs JSON |
| Custom Three.js renderer | planned | project | Browser | Owned | Recommended for the digital twin |

## Key finding

The project uses Three.js **0.187.0**. `gcode-preview` 2.18's README states support for
`three >=0.166.0 <0.186.0`, while npm's peer declaration is narrower. Installing it against
0.187 would be a knowingly broken peer. Options:

1. Pin Three.js **0.185.x** for the viewer app only.
2. Isolate `gcode-preview` in a separate package/page with its own Three copy.
3. Keep the custom renderer and use the Python parser output.

No package was installed merely to claim a viewer. The parser and toolpath data are real; the
eventual renderer decision is deferred until the browser test environment is fixed.

## Recommended architecture

```text
OrcaSlicer
  -> cube.gcode
  -> scripts/parse_gcode.py
  -> compact JSON (layers, segments, type, extrusion, feed)
  -> typed arrays / BufferGeometry
  -> Three.js LineSegments + layer slider + nozzle marker
```

Why not send G-code text to an LLM: a 300 KB test file is already 11,938 lines; production
files are tens of MB. Parsing and geometry generation must stay local and deterministic.

## Minimum viewer acceptance

- Layer count and per-layer extrusion match `gcode_parse.json`.
- 100 layers of the cube render interactively.
- 1 M segments at ≥30 fps target (60 fps preferred) on the test laptop.
- Layer isolation, play/pause, speed control, and a nozzle position readout.
- Color by feature type (`Perimeter`, `External perimeter`, `Infill`, `Solid infill`, `Travel`).
- No worker/pipe dependency that the DSH sandbox blocks; prefer a normal web worker or main
  thread with chunked uploads.

## References

- https://github.com/remcoder/gcode-preview
- https://www.npmjs.com/package/gcode-preview
- https://github.com/cncjs/gcode-parser
- https://github.com/cncjs/gcode-toolpath
- https://threejs.org/
