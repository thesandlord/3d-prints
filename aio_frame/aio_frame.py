"""
Open-frame stand for a 15.6" panel + LCD driver + SBC. Everything is printed.

Two side frames, two crossbars, four lock bars, three rails, six board clips.
Each crossbar drops into a socket on both frames. A thumb-sized lock bar slides
through the socket and stops the bar lifting out. Rails snap onto the crossbars.
Board clips slide on the rails and grip a PCB edge.

Coordinates (assembly): X = width, Y = up the panel, Z = depth (Z=0 = panel front).
Millimetres.  /tmp/cqenv/bin/python aio_frame.py
"""
import math, os
import cadquery as cq
from shapely.geometry import Polygon, box as sbox
from shapely.ops import unary_union

# ----------------------------------------------------------------- PARAMETERS
PW, PH, PT = 359.5, 223.8, 6.0
FIT = 0.4
FOAM = 1.0
LIP = 6.0
LIP_T = 2.4
HOOK_WALL = 3.0
SPINE = 8.0
FRAME_T = 12.0
FRAME_X = 110.0
TILT = 12.0
FOOT = 170.0
BRACE_Y = -40.0
CROSSBAR_Y = (-20.0, 80.0)

# crossbar section and the lock that pins it
BEAM_HY, BEAM_DZ = 9.0, 16.0       # 18 mm tall, 16 mm deep so the lock notch keeps a wall
BAR_Y, BAR_Z = 4.2, 10.0           # lock shaft: thin enough to spring, wide enough to grip
HOLE_Y, HOLE_Z = 4.9, 11.0         # the 1.3 mm bump on top clicks past HOLE_Y
BUMP = 1.3
BOSS_HY = 14.0
# Boss grows to one side of the 12 mm plate so that face sits on the bed.
BOSS_X0, BOSS_X1 = -FRAME_T / 2 - 14.0, FRAME_T / 2

# ----------------------------------------------------------------- DERIVED
GAP = PT + FOAM
ZS0, ZS1 = GAP, GAP + SPINE
BEAM_Z0 = ZS1 + 1.6
BEAM_Z1 = BEAM_Z0 + BEAM_DZ
# lock sits in the upper half of the beam so material remains underneath it
LOCK_Y = 3.0
PIN_Z = (BEAM_Z0 + BEAM_Z1) / 2
BEAM_HX = 124.0
YT = PH / 2 + FIT
T = math.radians(TILT)
CT, ST = math.cos(T), math.sin(T)


def h2w(y, z):
    return (y * ST + z * CT, y * CT - z * ST)


def w2h(b, h):
    return (h * CT + b * ST, -h * ST + b * CT)


def rect(y0, y1, z0, z1):
    return sbox(min(y0, y1), min(z0, z1), max(y0, y1), max(z0, z1))


def isect(p1, p2, p3, p4):
    (x1, y1), (x2, y2), (x3, y3), (x4, y4) = p1, p2, p3, p4
    den = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
    t = ((x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)) / den
    return (x1 + t * (x2 - x1), y1 + t * (y2 - y1))


def box(x0, x1, y0, y1, z0, z1):
    return (cq.Workplane("XY")
            .box(x1 - x0, y1 - y0, z1 - z0, centered=False)
            .translate((x0, y0, z0)))


def to_origin(s):
    bb = s.val().BoundingBox()
    return s.translate((-bb.xmin, -bb.ymin, -bb.zmin))


def side_profile():
    yb, ytop = -YT - HOOK_WALL, YT + HOOK_WALL
    parts = [rect(yb, ytop, ZS0, ZS1)]
    for s in (1, -1):
        parts.append(rect(s * YT, s * (YT + HOOK_WALL), -LIP_T, ZS0 + 0.1))
        parts.append(rect(s * (YT - LIP), s * (YT + 0.1), -LIP_T, 0))
    hd = min(h2w(yb, z)[1] for z in (-LIP_T, ZS1))
    bf = h2w(yb, -LIP_T)[0]
    leg_w = [(bf, hd), (FOOT, hd), (FOOT - 10, hd + 12), h2w(BRACE_Y, ZS1 + 12),
             h2w(BRACE_Y, ZS1 - 0.5), h2w(yb, ZS1 - 0.5), h2w(yb, -LIP_T)]
    parts.append(Polygon([w2h(*p) for p in leg_w]))
    prof = unary_union(parts)
    d1, d2 = w2h(0, hd), w2h(100, hd)
    b1, b2 = w2h(FOOT - 10, hd + 12), (BRACE_Y, ZS1 + 12)
    A = isect((0, ZS1), (1, ZS1), b1, b2)
    B = isect((0, ZS1), (1, ZS1), d1, d2)
    C = isect(d1, d2, b1, b2)
    hole = Polygon([A, B, C]).buffer(-8, join_style=1)
    return prof.difference(hole).simplify(0.01)


def poly_solid(poly, plane, t):
    s = cq.Workplane(plane).polyline(list(poly.exterior.coords)[:-1]).close().extrude(t / 2, both=True)
    for ring in poly.interiors:
        s = s.cut(cq.Workplane(plane).polyline(list(ring.coords)[:-1]).close().extrude(t, both=True))
    return s


def side_frame():
    """Panel slot and leg. Each crossbar height has a drop-in socket and a lock hole."""
    s = poly_solid(side_profile(), "YZ", FRAME_T)
    for y0 in CROSSBAR_Y:
        s = s.union(box(BOSS_X0, BOSS_X1, y0 - BOSS_HY, y0 + BOSS_HY, ZS1 - 3.0, BEAM_Z1 + 3.0))
        # slot the beam drops into, open at the top
        s = s.cut(box(BOSS_X0 - 1, BOSS_X1 + 1,
                      y0 - BEAM_HY - 0.45, y0 + BOSS_HY + 1,
                      BEAM_Z0 - 0.45, BEAM_Z1 + 0.45))
        # rib in the floor. The pocket in the beam lands on it and stops the bar sliding.
        s = s.union(box(-4.0, 4.0, y0 - BEAM_HY - 0.45, y0 - BEAM_HY + 2.6,
                        PIN_Z - 3.0, PIN_Z + 3.0))
        # lock hole through the side walls. Axis is the frame thickness, so it prints vertical.
        s = s.cut(box(BOSS_X0 - 1, BOSS_X1 + 1,
                      y0 + LOCK_Y - HOLE_Y / 2, y0 + LOCK_Y + HOLE_Y / 2,
                      PIN_Z - HOLE_Z / 2, PIN_Z + HOLE_Z / 2))
    return s


def crossbar():
    """Straight beam. Notch at each frame lets the lock pass; a pocket locates the rib.
    Built at y=0. Translate by CROSSBAR_Y to assemble."""
    s = box(-BEAM_HX, BEAM_HX, -BEAM_HY, BEAM_HY, BEAM_Z0, BEAM_Z1)
    for xc in (-FRAME_X, FRAME_X):
        s = s.cut(box(xc + BOSS_X0 - 0.5, xc + BOSS_X1 + 0.5,
                      LOCK_Y - HOLE_Y / 2 - 0.35, BEAM_HY + 1,
                      PIN_Z - HOLE_Z / 2 - 0.4, PIN_Z + HOLE_Z / 2 + 0.4))
        s = s.cut(box(xc - 4.6, xc + 4.6, -BEAM_HY - 1, -BEAM_HY + 3.3,
                      PIN_Z - 3.5, PIN_Z + 3.5))
    # rail detents, clear of the sockets
    for x in range(-90, 91, 18):
        s = s.cut(box(x - 5.5, x + 5.5, BEAM_HY - 1.4, BEAM_HY + 1,
                      BEAM_Z0 + 3, BEAM_Z1 - 3))
    return s


def lock_bar():
    """Solid bar with a ramp on top. The shaft bows as the ramp passes the hole,
    then the step at the back of the ramp catches the inner face.
    Bottom face is flat. Prints with the ramp on top. No floating finger."""
    y0 = -BAR_Y / 2
    boss_w = BOSS_X1 - BOSS_X0
    exit_x = 8.0 + boss_w
    shaft_x1 = exit_x + 14.0
    head = box(0, 8, y0, y0 + 12, -9, 9)
    shaft = box(8, shaft_x1, y0, y0 + BAR_Y, -BAR_Z / 2, BAR_Z / 2)
    ramp = (cq.Workplane("XY")
            .polyline([(exit_x + 0.3, y0 + BAR_Y),
                       (exit_x + 0.3, y0 + BAR_Y + BUMP),
                       (exit_x + 0.3 + BUMP + 3.5, y0 + BAR_Y)])
            .close().extrude(BAR_Z - 2, both=True))
    s = head.union(shaft).union(ramp)
    s = s.cut(box(shaft_x1 - 2.2, shaft_x1 + 1, y0 - 1, y0 + BAR_Y + BUMP + 1, -BAR_Z, BAR_Z)
              .rotate((shaft_x1 - 2.2, y0 + BAR_Y / 2, BAR_Z / 2),
                      (shaft_x1 - 1.2, y0 + BAR_Y / 2, BAR_Z / 2), 30))
    s = s.cut(box(shaft_x1 - 2.2, shaft_x1 + 1, y0 - 1, y0 + BAR_Y + BUMP + 1, -BAR_Z, BAR_Z)
              .rotate((shaft_x1 - 2.2, y0 + BAR_Y / 2, -BAR_Z / 2),
                      (shaft_x1 - 1.2, y0 + BAR_Y / 2, -BAR_Z / 2), -30))
    return s


def _saddle(cy):
    """Snap over the beam from behind. Lips are 45 degrees so they print and spring open."""
    arm = 2.8
    outer = BEAM_HY + 0.5 + arm
    z_lip = BEAM_Z0 - 2.2
    z_back = BEAM_Z1 + 5.0
    block = box(-8, 8, cy - outer, cy + outer, z_lip, z_back)
    block = block.cut(box(-9, 9, cy - BEAM_HY - 0.5, cy + BEAM_HY + 0.5, z_lip - 1, BEAM_Z1 + 0.35))
    # 45 degree lips in front of the beam. Throat is ~1 mm tighter than the beam per side.
    for i in range(2):
        inset = 0.6 * (i + 1)
        za, zb = z_lip + 0.7 * i, min(BEAM_Z0 - 0.25, z_lip + 0.7 * (i + 1))
        for side in (-1, 1):
            y_wall = cy + side * (BEAM_HY + 0.5)
            ya, yb = sorted((y_wall, y_wall - side * inset))
            block = block.union(box(-8, 8, ya, yb, za, zb))
    # detent tooth in the top arm, sitting in a beam notch (does not bite solid plastic)
    block = block.union(box(-2.4, 2.4, cy + BEAM_HY - 1.2, cy + BEAM_HY + 0.4,
                            BEAM_Z0 + 4, BEAM_Z1 - 4))
    return block


def rail():
    y0, y1 = CROSSBAR_Y[0] - 34, CROSSBAR_Y[1] + 34
    back0, back1 = BEAM_Z1 + 0.6, BEAM_Z1 + 5.0
    body = box(-7, 7, y0, y1, back0, back1)
    stem = box(-2.3, 2.3, y0, y1, back1, back1 + 3.0)
    cap = box(-6.0, 6.0, y0, y1, back1 + 3.0, back1 + 5.8)
    for y in range(int(y0) + 10, int(y1) - 6, 12):
        cap = cap.cut(box(4.5, 7.2, y, y + 5.0, back1 + 2.6, back1 + 6.2))
    s = body.union(stem).union(cap)
    for cy in CROSSBAR_Y:
        s = s.union(_saddle(cy))
    return s


def board_clip():
    """Print orientation. Groove on the bottom fits the rail cap. Slot grips the board edge."""
    cap_w, cap_t, stem_w, stem_l = 6.0, 2.8, 2.3, 3.0
    c = 0.45
    body = box(-11, 11, -9, 13, 0, 16)
    body = body.cut(box(-(cap_w + c), cap_w + c, -10, 14, -0.2, cap_t + c))
    body = body.cut(box(-(stem_w + c), stem_w + c, -10, 14, -0.2, cap_t + stem_l + c))
    # 2.4 mm slot, open both sides, for a 1.2–2.0 mm board
    body = body.cut(box(-12, 12, -1.2, 1.2, 8.0, 16.2))
    body = body.union(box(cap_w - 0.3, cap_w + 1.4, 3, 7, cap_t + 0.3, cap_t + 2.2))
    return body


def lay_up(s):
    """Assembly +Y (the open side of notches and the lock bump) becomes print +Z."""
    return to_origin(s.rotate((0, 0, 0), (1, 0, 0), 90))


def lay_frame(s):
    s = s.rotate((0, 0, 0), (1, 0, 0), TILT).rotate((0, 0, 0), (0, 1, 0), 90)
    s = s.rotate((0, 0, 0), (0, 0, 1), 90)  # long axis along X so a bed has a strip left over
    return to_origin(s)


def lay_rail(s):
    """Saddle opening up, back of the rail on the bed."""
    s = s.rotate((0, 0, 0), (1, 0, 0), 180)
    s = s.rotate((0, 0, 0), (0, 0, 1), 90)
    return to_origin(s)


def _inside(solid, p):
    return solid.val().isInside(p)


def _hit(a, b):
    hit = a.intersect(b)
    sols = hit.solids().vals()
    return sum(v.Volume() for v in sols) if sols else 0.0


def _report(name, solid):
    bb = solid.val().BoundingBox()
    print(f"{name:14s} {bb.xlen:6.1f} x {bb.ylen:6.1f} x {bb.zlen:5.1f}  "
          f"vol={solid.val().Volume()/1000:6.1f} cm3  valid={solid.val().isValid()}")


if __name__ == "__main__":
    here = os.path.dirname(os.path.abspath(__file__))
    out, prev = os.path.join(here, "stl"), os.path.join(here, "preview")
    os.makedirs(out, exist_ok=True)
    os.makedirs(prev, exist_ok=True)

    sf, cb, lk, rl, cl = side_frame(), crossbar(), lock_bar(), rail(), board_clip()
    print(f"beam z {BEAM_Z0:.1f}-{BEAM_Z1:.1f}  lock y {LOCK_Y:.1f}  pin z {PIN_Z:.1f}")

    # joint probes. Void where a part must pass, solid where it must catch.
    print("beam in socket (want void)", _inside(sf, (0, CROSSBAR_Y[0], PIN_Z)))
    print("rib solid", _inside(sf, (0, CROSSBAR_Y[0] - BEAM_HY + 1.2, PIN_Z)))
    print("lock hole void", _inside(sf, (10, CROSSBAR_Y[0] + LOCK_Y, PIN_Z)))
    print("pocket void", not _inside(cb, (FRAME_X, -BEAM_HY + 1.0, PIN_Z)))
    print("shelf under lock", _inside(cb, (FRAME_X, -4.0, PIN_Z)))
    print("notch void", not _inside(cb, (FRAME_X, LOCK_Y, PIN_Z)))

    frames = [sf.translate((x, 0, 0)) for x in (-FRAME_X, FRAME_X)]
    bars = [cb.translate((0, y, 0)) for y in CROSSBAR_Y]
    for fi, f in enumerate(frames):
        for bi, b in enumerate(bars):
            print(f"frame{fi} x bar{bi}  {_hit(f, b):7.1f} mm3")
    print(f"rail x lower bar {_hit(rl, bars[0]):7.1f} mm3")

    parts = {
        "side_frame": lay_frame(sf),
        "crossbar": lay_up(cb),
        "lock": to_origin(lay_up(lk).rotate((0, 0, 0), (0, 0, 1), 90)),
        "rail": lay_rail(rl),
        "board_clip": to_origin(cl),
    }
    for n, p in parts.items():
        _report(n, p)
        cq.exporters.export(p, os.path.join(out, n + ".stl"), tolerance=0.05, angularTolerance=0.2)
        cq.exporters.export(p, os.path.join(out, n + ".step"))

    asm = {}
    for i, x in enumerate((-FRAME_X, FRAME_X)):
        asm[f"side_frame_{i}"] = sf.translate((x, 0, 0))
    for i, y in enumerate(CROSSBAR_Y):
        asm[f"crossbar_{i}"] = cb.translate((0, y, 0))
    for i, x in enumerate((-70, 0, 70)):
        asm[f"rail_{i}"] = rl.translate((x, 0, 0))
    for n, p in asm.items():
        cq.exporters.export(p, os.path.join(prev, n + ".stl"), tolerance=0.15, angularTolerance=0.4)
    print("wrote stl/ and preview/")
