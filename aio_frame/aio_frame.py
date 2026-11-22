"""
Open-frame stand for a 15.6" panel + LCD driver + SBC.

The side frames are already printed. The only new parts are two bottom rails.
Each rail presses onto the foot of both frames and carries a grid of M3
through holes, so boards screw down onto the rails.

Coordinates (assembly): X = width, Y = up the panel, Z = depth (Z=0 = panel front).
The rails are built on the floor (world Y up, world Z back) and rotated into
this frame. Millimetres.  /tmp/cqenv/bin/python aio_frame.py
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

# Bottom rails, the only parts still to print. Sockets press onto the foot sole,
# which is the 12 mm plate under the lightening hole (8 mm tall).
SOLE_H = 8.0
BAR_T = 8.0
RAIL_V = 9.0              # half-width along the foot
CHEEK_CLEAR = 1.0         # socket stops this far above the floor
CHANNEL = 12.3            # 0.3 mm loose on the plate; the ribs make the press
# 238 mm overall, inside the 359.5 mm panel, so the rail cannot stop the screen seating.
RAIL_LEN = 238.0
CHEEK_T = RAIL_LEN / 2 - FRAME_X - CHANNEL / 2
RIB = 0.40                # rib thickness where the rail is fully seated
RIB_W = 0.8
FLARE = 1.3               # mouth wider than the plate, so it starts by hand
FLARE_H = 2.4
HOLE_D = 3.4              # M3 clearance
HOLE_PITCH = 8.0
HOLE_ROW = 4.5            # the two hole rows sit this far off the rail centre
RAIL_B = (50.0, 105.0)    # preview positions, mm back along the foot

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


def floor_height():
    """World height of the foot sole. The side-frame profile is built so this edge is flat."""
    yb = -YT - HOOK_WALL
    return min(h2w(yb, z)[1] for z in (-LIP_T, ZS1))


def _wp(solid):
    return cq.Workplane("XY").newObject([solid])


def _cyl_y(x, z, y0, y1, radius):
    return cq.Solid.makeCylinder(radius, y1 - y0, cq.Vector(x, y0, z), cq.Vector(0, 1, 0))


def _prism(pts, z0, z1):
    solid = cq.Workplane("XY").polyline(list(pts)).close().extrude(z1 - z0)
    return solid.translate((0, 0, z0))


def _hole_xs(offset):
    xs = []
    x = -96.0 + offset
    while x <= 96.0 - offset + 0.01:
        xs.append(x)
        x += HOLE_PITCH
    return xs


def bottom_rail_world(b_center, ribs=True):
    """Rail in floor coordinates: X across, Y up, Z back along the foot.

    The bar sits on the sole. Cheeks hang down either side of the 12 mm plate.
    Wedge ribs thicken toward the sole, so the socket starts loose and presses
    as it seats. Holes run through the bar on an 8 mm grid, the two rows
    staggered by half a pitch.
    """
    hd = floor_height()
    z0, z1 = b_center - RAIL_V, b_center + RAIL_V
    y_cheek = hd + CHEEK_CLEAR
    y_sole = hd + SOLE_H
    y_top = y_sole + BAR_T
    half = CHANNEL / 2.0
    outer = half + CHEEK_T

    s = box(-FRAME_X - outer, FRAME_X + outer, y_sole, y_top, z0, z1)
    flares = []
    rib_solids = []
    for xc in (-FRAME_X, FRAME_X):
        for sign in (-1, 1):
            face = xc + sign * half
            cheek_a, cheek_b = sorted((face, face + sign * CHEEK_T))
            s = s.union(box(cheek_a, cheek_b, y_cheek, y_top, z0, z1))
            flares.append(_prism(
                [(face, y_cheek),
                 (face + sign * FLARE, y_cheek),
                 (face, y_cheek + FLARE_H)],
                z0, z1))
            if ribs:
                y_rib0 = y_cheek + FLARE_H + 0.4
                y_rib1 = y_sole - 0.4
                tip = face - sign * RIB
                for zv in (-5.5, 0.0, 5.5):
                    rib_solids.append(_prism(
                        [(face, y_rib0), (face, y_rib1), (tip, y_rib1)],
                        b_center + zv - RIB_W / 2, b_center + zv + RIB_W / 2))
    if rib_solids:
        s = s.union(_wp(cq.Compound.makeCompound([r.val() for r in rib_solids])))
    s = s.cut(_wp(cq.Compound.makeCompound([f.val() for f in flares])))

    holes = []
    radius = HOLE_D / 2
    for x in _hole_xs(0.0):
        holes.append(_cyl_y(x, b_center - HOLE_ROW, y_sole - 0.6, y_top + 0.6, radius))
    for x in _hole_xs(HOLE_PITCH / 2):
        holes.append(_cyl_y(x, b_center + HOLE_ROW, y_sole - 0.6, y_top + 0.6, radius))
    s = s.cut(_wp(cq.Compound.makeCompound(holes)))
    return s


def bottom_rail(b_center, ribs=True):
    """Assembly coordinates, same frame as the side frames."""
    return bottom_rail_world(b_center, ribs=ribs).rotate((0, 0, 0), (1, 0, 0), -TILT)


def lay_frame(s):
    s = s.rotate((0, 0, 0), (1, 0, 0), TILT).rotate((0, 0, 0), (0, 1, 0), 90)
    s = s.rotate((0, 0, 0), (0, 0, 1), 90)  # long axis along X so a bed has a strip left over
    return to_origin(s)


def lay_bottom_rail(world):
    """Mounting face on the bed, socket cheeks pointing up, holes vertical."""
    return to_origin(world.rotate((0, 0, 0), (1, 0, 0), -90))


def place_rail(world, b_center):
    """A rail built at Z=0, shifted along the foot, then turned into assembly coordinates."""
    return world.translate((0, 0, b_center)).rotate((0, 0, 0), (1, 0, 0), -TILT)


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


def _at(x, u, b):
    y, z = w2h(b, floor_height() + u)
    return (x, y, z)


def _expect(cond, msg):
    if not cond:
        raise SystemExit("check failed: " + msg)


def _check(frame, world, rails):
    hd = floor_height()
    bb = world.val().BoundingBox()
    _expect(abs(bb.ymin - (hd + CHEEK_CLEAR)) < 0.05, f"cheek tip {bb.ymin}")
    _expect(abs(bb.ymax - (hd + SOLE_H + BAR_T)) < 0.05, f"bar top {bb.ymax}")
    _expect(abs(bb.zlen - 2 * RAIL_V) < 0.05, f"width {bb.zlen}")
    _expect(abs(bb.xlen - RAIL_LEN) < 0.15, f"length {bb.xlen:.2f}, want {RAIL_LEN}")
    _expect(bb.xlen < PW - 40, f"rail {bb.xlen:.1f} is too close to the {PW:.1f} mm panel")

    laid = lay_bottom_rail(world)
    lb = laid.val().BoundingBox()
    _report("bottom_rail", laid)
    _expect(lb.zlen < 16 and lb.ylen < 20 and lb.xlen < 250, "print orientation")
    mid = (lb.xmin + lb.xlen / 2, lb.ymin + lb.ylen / 2)
    _expect(_inside(laid, (mid[0], mid[1], 0.4)), "mounting face not on the bed")
    _expect(not _inside(laid, (mid[0], mid[1], 12.0)), "span should be open above the bar")

    n_holes = len(_hole_xs(0.0)) + len(_hole_xs(HOLE_PITCH / 2))
    print(f"holes {n_holes}   print {lb.xlen:.1f} x {lb.ylen:.1f} x {lb.zlen:.1f}")

    frames = [frame.translate((x, 0, 0)) for x in (-FRAME_X, FRAME_X)]
    b = RAIL_B[0]
    rail = rails[0]
    # Ribs bite the plate. The mouth and the side clearance stay open.
    _expect(_inside(rail, _at(-115.90, 7.4, b)) and _inside(frames[0], _at(-115.90, 7.4, b)),
            "left rib does not bite")
    _expect(_inside(rail, _at(115.90, 7.4, b)) and _inside(frames[1], _at(115.90, 7.4, b)),
            "right rib does not bite")
    gap = _at(-116.05, 5.0, b + 2.0)
    _expect(not _inside(rail, gap) and not _inside(frames[0], gap), "clearance gap is blocked")
    _expect(_inside(rail, _at(-FRAME_X, 12.0, b)) and not _inside(frames[0], _at(-FRAME_X, 12.0, b)),
            "bar collides with the frame above the sole")
    _expect(_inside(rail, _at(-118.0, 4.0, b)) and not _inside(frames[0], _at(-118.0, 4.0, b)),
            "cheek missing")
    _expect(not _inside(rail, _at(-117.0, 1.3, b)), "mouth is not open")
    _expect(not _inside(rail, _at(-118.0, 0.4, b)), "cheek reaches the floor")
    _expect(not _inside(rail, _at(0.0, 12.0, b - HOLE_ROW)), "hole missing")
    _expect(_inside(rail, _at(4.0, 12.0, b - HOLE_ROW)), "bar missing between holes")
    _expect(not _inside(rail, _at(-92.0, 12.0, b + HOLE_ROW)), "staggered hole missing")

    for i, one in enumerate(rails):
        for j, fr in enumerate(frames):
            hit = _hit(one, fr)
            print(f"rail{i} x frame{j}  {hit:7.2f} mm3")
            _expect(0.2 < hit < 40, f"rail{i} frame{j} intersection {hit:.1f}")
    _expect(_hit(rails[0], rails[1]) < 0.1, "rails intersect")
    _expect(laid.val().isValid() and frame.val().isValid(), "invalid solid")


def write_outputs():
    here = os.path.dirname(os.path.abspath(__file__))
    out, prev = os.path.join(here, "stl"), os.path.join(here, "preview")
    os.makedirs(out, exist_ok=True)
    os.makedirs(prev, exist_ok=True)

    frame = side_frame()
    world = bottom_rail_world(0.0)
    rails = [place_rail(world, b) for b in RAIL_B]
    _check(frame, world, rails)

    prints = {
        "side_frame": lay_frame(frame),
        "bottom_rail": lay_bottom_rail(world),
    }
    for name, solid in prints.items():
        if name != "bottom_rail":
            _report(name, solid)
        cq.exporters.export(solid, os.path.join(out, name + ".stl"),
                            tolerance=0.05, angularTolerance=0.2)
        cq.exporters.export(solid, os.path.join(out, name + ".step"))
    for name in os.listdir(out):
        stem, ext = os.path.splitext(name)
        if ext.lower() in (".stl", ".step") and stem not in prints:
            os.remove(os.path.join(out, name))

    asm = {}
    for i, x in enumerate((-FRAME_X, FRAME_X)):
        asm[f"side_frame_{i}"] = frame.translate((x, 0, 0))
    for i, solid in enumerate(rails):
        asm[f"bottom_rail_{i}"] = solid
    asm["panel"] = box(-PW / 2, PW / 2, -PH / 2, PH / 2, 0, PT)
    written = set()
    for name, solid in asm.items():
        cq.exporters.export(solid, os.path.join(prev, name + ".stl"),
                            tolerance=0.12, angularTolerance=0.35)
        written.add(name + ".stl")
    for name in os.listdir(prev):
        if name.lower().endswith(".stl") and name not in written:
            os.remove(os.path.join(prev, name))
    print("wrote stl/ and preview/")


if __name__ == "__main__":
    write_outputs()
