# Open-frame stand — 15.6" panel + LCD driver board + any SBC

Two side frames hold the panel and act as the legs. Two crossbars drop into sockets on the
frames and are pinned with printed lock bars. Three rails snap onto the crossbars and carry
the boards. No screws, nuts, or heat-set inserts.

## Measure first
Edit the PARAMETERS at the top of `aio_frame.py` and run
`/tmp/cqenv/bin/python aio_frame.py`.
- `PW, PH, PT`: panel outer width × height × thickness. Nominal 359.5 × 223.8 × 6.0.
- `FRAME_X`: side frames at ±110 mm. Keep the spines off the panel's rear PCB.
- `CROSSBAR_Y`: crossbar heights, −20 and +80 mm from panel centre.
- `TILT`: 12°. `FOOT`: 170 mm.

## Parts
| File | Qty | Prints as |
|---|---|---|
| `side_frame.stl` | 2 | Flat, 229 × 196 × 26 mm. One per plate. |
| `crossbar.stl` | 2 | Flat, 248 × 16 × 18 mm. Notch facing up. |
| `lock.stl` | 4 | Flat, bump on top. |
| `rail.stl` | 3 | Flat, saddle opening up. |
| `board_clip.stl` | 6 | Flat, groove on the bed. |

PLA, 0.2 mm layers, 3 walls, 15% infill. The frames are the long prints. Everything else
fits around them: plate 1 is one frame and both crossbars, plate 2 is the other frame,
three rails, four locks, and six clips.

The frames, crossbars, and rails from the screw-together version do not fit this joint.
The sockets are part of the frame, so both frames are reprinted.

## Assembly
1. Stand both frames up, panel slots facing each other, feet pointing back.
2. Drop one crossbar into the lower pair of sockets, then the other into the upper pair.
   The rib in the floor of each socket sits in the pocket on the underside of the bar.
   That sets the spacing. If a bar will not drop, the pocket is not over the rib.
3. Push a lock into each socket from the **outer** face of the frame (the face pointing
   away from the other frame), ramp up, until the ramp clicks out the inner face.
   The head stays on the outside. To remove one, push the tip back toward the head.
4. The panel can go in before or after the locks. Slide it in from the side, screen toward
   the front lips. A strip of foam tape in the slots keeps it from rattling.
5. Snap the three rails onto the crossbars from behind. They click over the beam and sit
   in the notches on top, so you can slide them left and right in steps. Use two under the
   driver board and the third under the SBC, or space all three under a wide board.
6. Slide the board clips onto a rail from either end, tooth toward the notches on the cap.
   Put a clip on each rail the board will use, at the same height. The slot is 2.4 mm,
   so it takes a 1.2–2.0 mm board. Slide the board in from the side. Tall parts on the
   board should face away from the rail.
7. Tape or hot-glue the button board. Route the LVDS cable so it misses the rails.

## Not verified
- No test print of this joint yet.
- Panel dimensions are still estimates.
