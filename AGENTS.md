# 3d-prints

## Design

Print every part. Use a printed joint instead of screws, nuts, heat-set inserts, or other bought hardware.

Fit a design on one X2D build plate when you can. The plate is 256 × 256 mm.

Prefer the simpler design. Add a part, a joint, or a feature only when the object needs it.

## Preview an assembly

Use the shared viewer before describing how a model looks. Pick a camera that shows the depth of the part. A straight-on view often hides it.

The viewer and server live in `tools/` and work for any project. A project shows up when `<project>/preview/` contains binary STL meshes of the assembly, in that model's housing coordinates. Those meshes are separate from the print-bed STLs in `<project>/stl/`.

```bash
python3 tools/preview_server.py
```

Open `http://127.0.0.1:8765/`. Drag orbits, scroll zooms. `?project=<name>` opens one project. `clean=1` hides the on-screen hint. The page sets `document.body.dataset.ready` to `"1"` after the meshes load. Save shots under `<project>/renders/`.

Optional `<project>/preview.json` configures that project. Read it for the cameras worth shooting.

- `title` and `hud`
- `tilt`: degrees about X, applied to the mesh before the camera
- `colors`: RGB triples keyed by part family. Trailing `_` plus digits are ignored, so `rail_2` uses `rail`. A group prefix is removed first.
- `camera`: default `yaw`, `pitch`, `dist`, and optional `center`
- `views`: named cameras for `?view=<name>`. `center` is in viewer space, after tilt.
- `groups`: pose name to a filename prefix, with `defaultGroup`, when one folder holds more than one pose. `?group=<name>` selects a pose. A `view` whose name is also a group shows that pose.

With no `preview.json`, the viewer loads every `.stl` in `preview/`, colors parts by name, and frames the camera to the mesh.

Each project regenerates its own `preview/` meshes. The server only reads them.
