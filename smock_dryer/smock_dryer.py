"""
Counter stand for a long-sleeve baby smock. Four pieces.

The spine is two tubes that snap together. A post at the top is narrower than
the tube, and that shoulder is the ridge: the hanger slides onto the post and
stops there. The bottom of the spine is a square tenon that seats in the
middle of the X feet.

The lower tube is hollow. With the top half off, the hanger and both feet
slide into that cavity for storage. The lower tube is the longest piece, and
the post and the tenon are the thin ends.

Millimetres. Each part fits a 256 mm plate.
/tmp/cqenv/bin/python smock_dryer.py
"""
import math
import os

import cadquery as cq

# ----------------------------------------------------------------- SPINE
OUTER = 32.0
WALL = 3.2
INNER = OUTER - 2 * WALL          # 25.6 cavity

TENON = 11.0
TENON_FIT = 0.70                  # socket is this much wider than the tenon
TENON_L = 6.5
FOOT_T = 8.0                      # the tenon stops short of the underside

LOWER = 246.0                     # lower tube, tenon included. Longest print.
FLOOR = 4.0

PLUG_L = 16.0
PLUG_FIT = 0.45                   # plug is this much smaller than the cavity
UPPER_TUBE = 140.0
RIDGE = OUTER + 4.0               # collar the hanger sits on
RIDGE_H = 4.0
POST_D = 14.0
POST_H = 12.0

# ----------------------------------------------------------------- HANGER
ROD_L = 200.0
ROD_W = 22.0
ROD_T = 5.0
HOLE_FIT = 0.70                   # hole is this much wider than the post

# ----------------------------------------------------------------- FEET
FOOT_L = 200.0
FOOT_W = 20.0
SLOT_FIT = 0.45

# Snap. Two hooks on the plug, two windows in the lower tube.
HOOK_W = 8.0
HOOK_T = 1.5
HOOK_CATCH = 1.05                 # how far the nose passes the inner wall
BEAM_L = 11.0


def _box(sx, sy, sz, x, y, z):
    return cq.Workplane("XY").box(sx, sy, sz).translate((x, y, z))


def _cyl(x, y, z0, z1, r):
    return cq.Workplane("XY").circle(r).extrude(z1 - z0).translate((x, y, z0))


def _hit(a, b):
    sols = a.intersect(b).solids().vals()
    return sum(v.Volume() for v in sols) if sols else 0.0


def _report(name, solid):
    bb = solid.val().BoundingBox()
    n = len(solid.solids().vals()) or 1
    print(f"{name:14s} {bb.xlen:6.1f} x {bb.ylen:6.1f} x {bb.zlen:5.1f}  "
          f"vol={solid.val().Volume() / 1000:6.1f} cm3  shells={n}")
    return bb


def spine_lower():
    """Print standing, tenon on the bed. Z is up."""
    tenon = (cq.Workplane("XY").rect(TENON - 2.4, TENON - 2.4)
             .workplane(offset=1.8).rect(TENON, TENON).loft(combine=True))
    tenon = tenon.union(
        cq.Workplane("XY").rect(TENON, TENON).extrude(TENON_L - 1.8).translate((0, 0, 1.8)))
    body = _box(OUTER, OUTER, LOWER - TENON_L, 0, 0, TENON_L + (LOWER - TENON_L) / 2)
    cavity_z0 = TENON_L + FLOOR
    cavity = _box(INNER, INNER, LOWER - cavity_z0 + 1, 0, 0, (cavity_z0 + LOWER + 1) / 2)
    solid = tenon.union(body).cut(cavity)
    # Windows the hooks land in. Cut the wall only.
    win_top = LOWER - 7.0
    win_bot = win_top - 5.0
    for sign in (-1, 1):
        solid = solid.cut(_box(WALL + 1.2, HOOK_W + 1.4, win_top - win_bot,
                               sign * (INNER / 2 + WALL / 2), 0, (win_top + win_bot) / 2))
    return solid


def spine_upper():
    """Print standing, plug on the bed. The plug snaps into the lower tube."""
    plug_s = INNER - PLUG_FIT
    # The plug runs a little past the joint so it has volume inside the tube.
    plug = _box(plug_s, plug_s, PLUG_L + 1.2, 0, 0, (PLUG_L + 1.2) / 2)
    tube_z0 = PLUG_L
    tube_z1 = PLUG_L + UPPER_TUBE
    tube = _box(OUTER, OUTER, UPPER_TUBE, 0, 0, (tube_z0 + tube_z1) / 2)
    # Ring above the joint only. Wider than the bore, so it ties the plug to the wall.
    ring = _box(OUTER - 0.4, OUTER - 0.4, 1.2, 0, 0, tube_z0 + 0.7)
    ridge = _box(RIDGE, RIDGE, RIDGE_H, 0, 0, tube_z1 + RIDGE_H / 2)
    post = _cyl(0, 0, tube_z1 + RIDGE_H, tube_z1 + RIDGE_H + POST_H, POST_D / 2)
    bore_h = UPPER_TUBE - 1.6
    bore = _box(INNER, INNER, bore_h, 0, 0, tube_z0 + 1.6 + bore_h / 2)
    solid = plug.union(ring).union(tube).union(ridge).union(post).cut(bore)

    # A tongue on each side, rooted at the top, with a ramped nose at the tip.
    half = plug_s / 2
    nose_z0, nose_z1 = 3.6, 7.2
    for sign in (-1, 1):
        tongue = _box(HOOK_T, HOOK_W, BEAM_L,
                      sign * (half - HOOK_T / 2), 0, 2.4 + BEAM_L / 2)
        nose = _box(HOOK_CATCH + 0.4, HOOK_W, nose_z1 - nose_z0,
                    sign * (half + HOOK_CATCH / 2 - 0.1), 0, (nose_z0 + nose_z1) / 2)
        # Ramp on the leading edge so the nose cams inward on the way in.
        ramp = (cq.Workplane("XY").box(HOOK_CATCH + 1.2, HOOK_W + 1, 3.0)
                .rotate((0, 0, 0), (0, 1, 0), -sign * 48)
                .translate((sign * (half + 0.2), 0, nose_z0 - 0.2)))
        relief = _box(1.7, HOOK_W + 1.2, BEAM_L - 2.4,
                      sign * (half - HOOK_T - 0.85), 0, 2.2 + (BEAM_L - 2.4) / 2)
        solid = solid.cut(relief).union(tongue).union(nose).cut(ramp)
    return solid


def hanger():
    """Flat on the bed. The hole is vertical, so the post drops through it."""
    core = _box(ROD_L - ROD_W, ROD_W, ROD_T, 0, 0, ROD_T / 2)
    for sign in (-1, 1):
        core = core.union(_cyl(sign * (ROD_L - ROD_W) / 2, 0, 0, ROD_T, ROD_W / 2))
    hole = _cyl(0, 0, -1, ROD_T + 2, (POST_D + HOLE_FIT) / 2)
    return core.cut(hole)


def foot():
    """One half of the X. Print two. The slot is on the top face."""
    bar = _box(FOOT_L, FOOT_W, FOOT_T, 0, 0, FOOT_T / 2)
    slot = _box(FOOT_W + SLOT_FIT, FOOT_W + 4, FOOT_T / 2 + 0.2,
                0, 0, FOOT_T * 0.75 + 0.1)
    hole = _box(TENON + TENON_FIT, TENON + TENON_FIT, FOOT_T + 2, 0, 0, FOOT_T / 2)
    # Round the ends so the stored feet slide into the cavity.
    ends = None
    for sign in (-1, 1):
        cap = _cyl(sign * (FOOT_L / 2 - FOOT_W / 2), 0, 0, FOOT_T, FOOT_W / 2)
        ends = cap if ends is None else ends.union(cap)
    # The end caps sit on the square ends; trim them back to a round tip.
    straight = _box(FOOT_L - FOOT_W + 1.2, FOOT_W, FOOT_T, 0, 0, FOOT_T / 2)
    bar = straight.union(ends)
    return bar.cut(slot).cut(hole)


def _stand_up(solid):
    """Part Z (print up) becomes assembly Y (stand up)."""
    return solid.rotate((0, 0, 0), (1, 0, 0), -90)


def assemble():
    lower = spine_lower()
    upper = spine_upper()
    bar = hanger()
    one = foot()

    # Shoulder of the lower tube sits on top of the feet.
    lift = FOOT_T - TENON_L
    low = _stand_up(lower).translate((0, lift, 0))
    # Plug tip meets the lower opening, one plug-length down.
    up = _stand_up(upper).translate((0, lift + LOWER - PLUG_L, 0))

    ridge_top = lift + LOWER - PLUG_L + PLUG_L + UPPER_TUBE + RIDGE_H
    hung = _stand_up(bar).translate((0, ridge_top, 0))

    foot_a = _stand_up(one)
    foot_b = (foot_a
              .rotate((0, FOOT_T / 2, 0), (1, FOOT_T / 2, 0), 180)
              .rotate((0, 0, 0), (0, 1, 0), 90))

    return {
        "spine_0": low,
        "spine_1": up,
        "hanger": hung,
        "foot_0": foot_a,
        "foot_1": foot_b,
    }, ridge_top


def _along_spine(solid):
    """Turn a flat part so its long axis (print X) runs up the spine."""
    return _stand_up(solid).rotate((0, 0, 0), (0, 0, 1), 90)


def packed(lower_print):
    """Hanger and both feet inside the lower cavity, top half off."""
    lift = FOOT_T - TENON_L
    low = _stand_up(lower_print).translate((0, lift, 0))
    cavity_lo = lift + TENON_L + FLOOR
    cavity_hi = lift + LOWER - PLUG_L
    mid = (cavity_lo + cavity_hi) / 2
    # Cross-section of the cavity is X by Z. Thicknesses stack along X.
    bar = _along_spine(hanger()).translate((-6.5, mid, 0))
    a = _along_spine(foot()).translate((2.5, mid, 0))
    b = _along_spine(foot()).translate((11.0, mid, 0))
    return {"spine_0": low, "hanger": bar, "foot_0": a, "foot_1": b}


if __name__ == "__main__":
    here = os.path.dirname(os.path.abspath(__file__))
    out, prev = os.path.join(here, "stl"), os.path.join(here, "preview")
    os.makedirs(out, exist_ok=True)
    os.makedirs(prev, exist_ok=True)

    lower, upper, bar, one = spine_lower(), spine_upper(), hanger(), foot()
    stood, ridge_top = assemble()
    pack = packed(lower)

    print("-- prints. the long number has to stay under 256")
    for name, solid in (("spine_lower", lower), ("spine_upper", upper),
                        ("hanger", bar), ("foot", one)):
        _report(name, solid)

    print("-- standing fit. want ~0, the hooks sit in the windows")
    pairs = (("spine_0", "spine_1"), ("spine_1", "hanger"),
             ("spine_0", "foot_0"), ("spine_0", "foot_1"),
             ("foot_0", "foot_1"), ("hanger", "foot_0"))
    for a, b in pairs:
        hit = _hit(stood[a], stood[b])
        mark = "" if hit < 1 else "  <--"
        print(f"  {a:8s} x {b:8s} {hit:8.1f}{mark}")

    print("-- packed into the lower tube. want ~0")
    for name in ("hanger", "foot_0", "foot_1"):
        hit = _hit(pack["spine_0"], pack[name])
        mark = "" if hit < 1 else "  <--"
        print(f"  spine x {name:8s} {hit:8.1f}{mark}")
    print(f"  hanger x foot_0 {_hit(pack['hanger'], pack['foot_0']):8.1f}")
    print(f"  foot_0 x foot_1 {_hit(pack['foot_0'], pack['foot_1']):8.1f}")

    feet_top = FOOT_T
    print(f"hanger seat {ridge_top - 0:.0f} mm above the counter")
    print(f"post top    {ridge_top + POST_H:.0f} mm")
    cavity_len = LOWER - TENON_L - FLOOR - PLUG_L
    print(f"cavity {INNER:.1f} x {INNER:.1f} x {cavity_len:.0f} mm  "
          f"rod {ROD_L:.0f}  foot {FOOT_L:.0f}")

    for folder in (out, prev):
        for name in os.listdir(folder):
            if name.endswith((".stl", ".step")):
                os.remove(os.path.join(folder, name))

    for name, solid in (("spine_lower", lower), ("spine_upper", upper),
                        ("hanger", bar), ("foot", one)):
        cq.exporters.export(solid, os.path.join(out, name + ".stl"),
                            tolerance=0.05, angularTolerance=0.15)
        cq.exporters.export(solid, os.path.join(out, name + ".step"))

    preview = {}
    for name, solid in stood.items():
        preview["up_" + name] = solid
    for name, solid in pack.items():
        # Slide the stored parts up so the open end shows they fit in the tube.
        if name != "spine_0":
            solid = solid.translate((0, 120, 0))
        preview["pack_" + name] = solid
    for name, solid in preview.items():
        cq.exporters.export(solid, os.path.join(prev, name + ".stl"),
                            tolerance=0.12, angularTolerance=0.35)
    print("wrote stl/ and preview/")
