"""
Counter stand for a long-sleeve baby smock.

The spine is two tubes. The lower one is slim, with a tenon for the feet and
a hollow center for storage. The upper one is wider and has the post. Push
the slim tube up into the wide one to pack it. Pull it down and a flare on
the slim tube seats in the mouth. Four slits let the mouth spring over the
flare on the way through.

Both print standing. The slim one has a snap-off brim and ribs, because the
tenon alone is too small a foot for a tall tube. The wide one stands on its
mouth, with a brim around that ring.

Millimetres. Each part fits a 256 mm plate.
/tmp/cqenv/bin/python smock_dryer.py
"""
import os

import cadquery as cq

# ----------------------------------------------------------------- SPINE
OUTER = 32.0
WALL = 3.2
INNER = OUTER - 2 * WALL          # 25.6 cavity

TENON = 11.0
TENON_FIT = 0.70
TENON_L = 6.5
FOOT_T = 8.0

LOWER = 214.0                     # slim tube, tenon included
FLOOR = 3.5
FLARE_H = 14.0
FLARE_TOP = 34.8                  # wide end of the flare, at the top of the slim tube
FLARE_Z0 = LOWER - FLARE_H

# The wide tube. Mouth at print z=0, post at the top.
WIDE = 48.0
BORE = 40.0
LIP = 33.6                        # narrow end of the mouth. Clears the 32 mm body.
MOUTH_H = 16.0
MOUTH_WIDE = LIP + (FLARE_TOP - OUTER) / FLARE_H * MOUTH_H
TUBE_TOP = 216.0                  # solid roof starts overlapping below this
ROOF_TOP = 32.0                   # flat the hanger sits on
ROOF_Z = TUBE_TOP + 16.0
POST_D = 14.0
POST_H = 12.0
SLIT_W = 1.8
SLIT_H = MOUTH_H + 8.0

# How far the flare tip sits above the lip when the stand is up.
SEAT = 8.0

BRIM = 62.0
BRIM_T = 0.8
WIDE_BRIM = 68.0

# ----------------------------------------------------------------- HANGER
ROD_L = 200.0
ROD_W = 22.0
ROD_T = 5.0
HOLE_FIT = 0.70

# ----------------------------------------------------------------- FEET
FOOT_L = 200.0
FOOT_W = 20.0
SLOT_FIT = 0.45


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


def _loft_xy(z0, s0, z1, s1):
    return (cq.Workplane("XY").workplane(offset=z0).rect(s0, s0)
            .workplane(offset=z1 - z0).rect(s1, s1).loft(combine=True))


def spine_lower(brim=False):
    """Slim tube. Print standing, tenon on the bed. The top flares out."""
    tenon = _loft_xy(0, TENON - 1.0, 0.8, TENON)
    tenon = tenon.union(
        cq.Workplane("XY").rect(TENON, TENON).extrude(TENON_L - 0.8)
        .translate((0, 0, 0.8)))
    body = _box(OUTER, OUTER, FLARE_Z0 - TENON_L + 0.8,
                0, 0, TENON_L + (FLARE_Z0 - TENON_L + 0.8) / 2)
    flare = _loft_xy(FLARE_Z0, OUTER, LOWER, FLARE_TOP)
    solid = tenon.union(body).union(flare)
    cavity_z0 = TENON_L + FLOOR
    cavity = _box(INNER, INNER, LOWER - cavity_z0 + 1,
                  0, 0, (cavity_z0 + LOWER + 1) / 2)
    solid = solid.cut(cavity)
    if brim:
        solid = solid.union(_lower_brim())
    return solid


def _rib(bite0, bite1, base0, base1):
    """Steep rib on the +X side. The polyline's Y becomes Z."""
    rib = (cq.Workplane("XY")
           .polyline([(bite0, 7.4), (bite1, 7.4), (bite1, 6.5),
                      (base1, 0.15), (base0, 0.15)])
           .close()
           .extrude(1.6, both=True))
    return rib.rotate((0, 0, 0), (1, 0, 0), 90)


def _lower_brim():
    """Pad and ribs under the shoulder. Snap them off before the tenon goes in the feet."""
    pad = _box(BRIM, BRIM, BRIM_T, 0, 0, BRIM_T / 2)
    pad = pad.cut(_box(TENON + 1.6, TENON + 1.6, BRIM_T + 1, 0, 0, BRIM_T / 2))
    web = _box(TENON + 1.4, TENON + 1.4, BRIM_T, 0, 0, BRIM_T / 2)
    web = web.cut(_box(TENON - 0.6, TENON - 0.6, BRIM_T + 1, 0, 0, BRIM_T / 2))
    ribs = None
    specs = (
        (13.2, 15.4, 16.2, 20.2, 0),
        (19.4, 21.6, 22.4, 27.2, 45),
    )
    for bite0, bite1, base0, base1, twist in specs:
        rib = _rib(bite0, bite1, base0, base1)
        for turn in range(4):
            one = rib.rotate((0, 0, 0), (0, 0, 1), twist + 90 * turn)
            ribs = one if ribs is None else ribs.union(one)
    return pad.union(web).union(ribs)


def spine_upper(brim=False):
    """Wide tube. Print standing on the mouth. The post is up."""
    tube = _box(WIDE, WIDE, ROOF_Z, 0, 0, ROOF_Z / 2)
    # Roof closes inward so the top needs no bridge, then the hanger sits on it.
    roof = _loft_xy(TUBE_TOP - 2.0, WIDE, ROOF_Z, ROOF_TOP)
    post = _cyl(0, 0, ROOF_Z - 0.6, ROOF_Z + POST_H, POST_D / 2)
    mouth = _loft_xy(-0.2, LIP, MOUTH_H, MOUTH_WIDE)
    bore = _box(BORE, BORE, TUBE_TOP - MOUTH_H + 0.4,
                0, 0, MOUTH_H - 0.2 + (TUBE_TOP - MOUTH_H + 0.4) / 2)
    solid = tube.union(roof).union(post).cut(mouth).cut(bore)
    for turn in range(4):
        slit = _box(WIDE, SLIT_W, SLIT_H, WIDE / 4, 0, SLIT_H / 2)
        solid = solid.cut(slit.rotate((0, 0, 0), (0, 0, 1), 90 * turn))
    if brim:
        solid = solid.union(_upper_brim())
    return solid


def _upper_brim():
    pad = _box(WIDE_BRIM, WIDE_BRIM, BRIM_T, 0, 0, BRIM_T / 2)
    pad = pad.cut(_box(WIDE + 0.2, WIDE + 0.2, BRIM_T + 1, 0, 0, BRIM_T / 2))
    web = _box(WIDE + 1.6, WIDE + 1.6, BRIM_T, 0, 0, BRIM_T / 2)
    web = web.cut(_box(WIDE - 0.8, WIDE - 0.8, BRIM_T + 1, 0, 0, BRIM_T / 2))
    return pad.union(web)


def hanger():
    """Flat on the bed. The hole is vertical, so the post drops through it."""
    core = _box(ROD_L - ROD_W, ROD_W, ROD_T, 0, 0, ROD_T / 2)
    for sign in (-1, 1):
        core = core.union(_cyl(sign * (ROD_L - ROD_W) / 2, 0, 0, ROD_T, ROD_W / 2))
    hole = _cyl(0, 0, -1, ROD_T + 2, (POST_D + HOLE_FIT) / 2)
    return core.cut(hole)


def foot():
    """One half of the X. Print two. The slot is on the top face."""
    slot = _box(FOOT_W + SLOT_FIT, FOOT_W + 4, FOOT_T / 2 + 0.2,
                0, 0, FOOT_T * 0.75 + 0.1)
    hole = _box(TENON + TENON_FIT, TENON + TENON_FIT, FOOT_T + 2, 0, 0, FOOT_T / 2)
    ends = None
    for sign in (-1, 1):
        cap = _cyl(sign * (FOOT_L / 2 - FOOT_W / 2), 0, 0, FOOT_T, FOOT_W / 2)
        ends = cap if ends is None else ends.union(cap)
    straight = _box(FOOT_L - FOOT_W + 1.2, FOOT_W, FOOT_T, 0, 0, FOOT_T / 2)
    return straight.union(ends).cut(slot).cut(hole)


def _stand_up(solid):
    """Part Z (print up) becomes assembly Y (stand up)."""
    return solid.rotate((0, 0, 0), (1, 0, 0), -90)


def assemble():
    lower = spine_lower()
    upper = spine_upper()
    bar = hanger()
    one = foot()

    lift = FOOT_T - TENON_L
    low = _stand_up(lower).translate((0, lift, 0))
    # Lip of the wide tube sits SEAT mm below the flare tip.
    lip_y = lift + LOWER - SEAT
    up = _stand_up(upper).translate((0, lip_y, 0))

    ridge_top = lip_y + ROOF_Z
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


def packed():
    """Slim tube slid up inside the wide one, post end first. Parts in the slim cavity."""
    lift = FOOT_T - TENON_L
    # Tenon sticks out of the mouth a little, so it can be pulled back out.
    low = _stand_up(spine_lower()).translate((0, lift - 16.0, 0))
    up = _stand_up(spine_upper()).translate((0, lift, 0))
    cavity_lo = lift - 16.0 + TENON_L + FLOOR
    cavity_hi = lift - 16.0 + LOWER
    mid = (cavity_lo + cavity_hi) / 2
    bar = _along_spine(hanger()).translate((-6.5, mid, 0))
    a = _along_spine(foot()).translate((2.5, mid, 0))
    b = _along_spine(foot()).translate((11.0, mid, 0))
    return {
        "spine_0": low,
        "spine_1": up,
        "hanger": bar,
        "foot_0": a,
        "foot_1": b,
    }


if __name__ == "__main__":
    here = os.path.dirname(os.path.abspath(__file__))
    out, prev = os.path.join(here, "stl"), os.path.join(here, "preview")
    os.makedirs(out, exist_ok=True)
    os.makedirs(prev, exist_ok=True)

    lower, upper = spine_lower(brim=True), spine_upper(brim=True)
    bar, one = hanger(), foot()
    stood, ridge_top = assemble()
    pack = packed()

    print("-- prints. the long number has to stay under 256")
    for name, solid in (("spine_lower", lower), ("spine_upper", upper),
                        ("hanger", bar), ("foot", one)):
        _report(name, solid)

    print("-- standing fit. want ~0")
    pairs = (("spine_0", "spine_1"), ("spine_1", "hanger"),
             ("spine_0", "foot_0"), ("spine_0", "foot_1"),
             ("foot_0", "foot_1"), ("hanger", "foot_0"))
    for a, b in pairs:
        hit = _hit(stood[a], stood[b])
        mark = "" if hit < 1 else "  <--"
        print(f"  {a:8s} x {b:8s} {hit:8.1f}{mark}")

    print("-- packed. slim tube inside the wide one. want ~0")
    for name in ("spine_1", "hanger", "foot_0", "foot_1"):
        hit = _hit(pack["spine_0"], pack[name])
        mark = "" if hit < 1 else "  <--"
        print(f"  spine_0 x {name:8s} {hit:8.1f}{mark}")
    for name in ("hanger", "foot_0", "foot_1"):
        hit = _hit(pack["spine_1"], pack[name])
        mark = "" if hit < 1 else "  <--"
        print(f"  spine_1 x {name:8s} {hit:8.1f}{mark}")
    print(f"  hanger x foot_0 {_hit(pack['hanger'], pack['foot_0']):8.1f}")
    print(f"  foot_0 x foot_1 {_hit(pack['foot_0'], pack['foot_1']):8.1f}")

    print(f"hanger seat {ridge_top:.0f} mm above the counter")
    print(f"post top    {ridge_top + POST_H:.0f} mm")
    cavity_len = LOWER - TENON_L - FLOOR
    print(f"cavity {INNER:.1f} x {INNER:.1f} x {cavity_len:.0f} mm  "
          f"rod {ROD_L:.0f}  foot {FOOT_L:.0f}")
    print(f"mouth lip {LIP:.1f}  flare {FLARE_TOP:.1f}  bore {BORE:.0f}")

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
        if name not in ("spine_0", "spine_1"):
            solid = solid.translate((0, -90, 0))
        preview["pack_" + name] = solid
    preview["print_spine_0"] = _stand_up(lower)
    preview["print_spine_1"] = _stand_up(upper).translate((100, 0, 0))
    for name, solid in preview.items():
        cq.exporters.export(solid, os.path.join(prev, name + ".stl"),
                            tolerance=0.12, angularTolerance=0.35)
    print("wrote stl/ and preview/")
