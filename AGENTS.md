# 3d-prints

## Preview an assembly

Use this before describing how a model looks. Do not rely on a straight-on front shot: for `aio_frame` that view is just the panel.

Meshes in `aio_frame/preview/` are the assembled stand, in housing coordinates (Y up the panel, Z out the back, Z=0 at the panel front). They are not the print-bed STLs in `aio_frame/stl/`.

Regenerate them after a geometry change:

```bash
cd aio_frame
PYTHONPATH=. /tmp/cqenv/bin/python viz/export_preview.py
```

Serve from `aio_frame` so `viz/` can load `../preview/`:

```bash
cd aio_frame
python3 -m http.server 8765 --bind 127.0.0.1
```

Open `http://127.0.0.1:8765/viz/`. Drag orbits, scroll zooms. The page rotates the model 12° about X so the feet sit on the floor.

Screenshot these URLs:

- `?view=front&clean=1` three-quarter front
- `?view=back&clean=1` crossbars, rails, locks
- `?view=side&clean=1` leg and tilt
- `?view=joint&clean=1` one socket

`clean=1` hides the on-screen hint. Save the shots under `aio_frame/renders/`.

Colors: orange frames, blue crossbars, yellow rails, gray locks, green clips, black panel.
