"""Write the assembled stand into preview/ for the viewer. Not print orientation."""
import os
import cadquery as cq
from aio_frame import (
    side_frame, crossbar, lock_bar, rail, board_clip,
    FRAME_X, CROSSBAR_Y, LOCK_Y, PIN_Z, BOSS_X0, BOSS_X1, PW, PH, PT, box,
)

here = os.path.dirname(os.path.abspath(__file__))
prev = os.path.join(here, "preview")
os.makedirs(prev, exist_ok=True)

sf, cb, lk, rl, cl = side_frame(), crossbar(), lock_bar(), rail(), board_clip()
parts = {}
for i, x in enumerate((-FRAME_X, FRAME_X)):
    parts[f"side_frame_{i}"] = sf.translate((x, 0, 0))
for i, y in enumerate(CROSSBAR_Y):
    parts[f"crossbar_{i}"] = cb.translate((0, y, 0))
for i, x in enumerate((-70, 0, 70)):
    parts[f"rail_{i}"] = rl.translate((x, 0, 0))

# Lock shaft starts at model x=8. Head is on the outer face, shaft points inward.
for i, xc in enumerate((-FRAME_X, FRAME_X)):
    for j, y in enumerate(CROSSBAR_Y):
        if xc > 0:
            outer = xc + BOSS_X1
            placed = lk.mirror("YZ").translate((outer + 8.0, y + LOCK_Y, PIN_Z))
        else:
            outer = xc + BOSS_X0
            placed = lk.translate((outer - 8.0, y + LOCK_Y, PIN_Z))
        parts[f"lock_{i}_{j}"] = placed

# Cap back face. Clip groove opens toward -Z, so the clip sits just behind the rail.
cap_back = 32.6 + 5.0 + 5.8  # BEAM_Z1 + back plate + cap, kept in sync below
from aio_frame import BEAM_Z1
cap_back = BEAM_Z1 + 5.0 + 5.8
for i, x in enumerate((-70, 0, 70)):
    for k, y in enumerate((10.0, 55.0)):
        parts[f"clip_{i}_{k}"] = cl.translate((x, y - 2.0, cap_back))

parts["panel"] = box(-PW / 2, PW / 2, -PH / 2, PH / 2, 0, PT)

for n, p in parts.items():
    cq.exporters.export(p, os.path.join(prev, n + ".stl"), tolerance=0.12, angularTolerance=0.35)
    print(n)
print("cap_back", cap_back)
