# Open-frame stand — 15.6" panel + LCD driver board + any SBC

Two plain side frames hold the panel. Two bottom rails press onto the feet. Boards
screw down onto the rails. The frames have no crossbar brackets.

The rail is 238 mm long, inside the 359.5 mm panel, so it cannot hold the frames apart
or stop the screen from seating.

## Measure first
Edit the PARAMETERS at the top of `aio_frame.py` and run
`/tmp/cqenv/bin/python aio_frame.py`.
- `PW, PH, PT`: panel outer width × height × thickness. Nominal 359.5 × 223.8 × 6.0.
- `FRAME_X`: side frames at ±110 mm. The rails are sized to that spacing.
- `RAIL_LEN`: 238 mm. Keep it under the panel width.
- `RAIL_B`: where the preview places the two rails, in millimetres back along the foot.

## Parts
| File | Qty | Prints as |
|---|---|---|
| `side_frame.stl` | 2 | Flat, 229 × 196 × 12 mm. One per plate. |
| `bottom_rail.stl` | 2 | Flat, 238 × 18 × 15 mm. Both fit on one plate. |

PLA, 0.2 mm layers, 3 walls, 15% infill. Print the rail with the flat face on the bed and
the socket walls pointing up.

## Assembly
1. Stand both frames up, panel slots facing each other, feet pointing back. The screen
   slides in from the side, toward the front lips. A strip of foam tape in the slots
   keeps it from rattling.
2. Press a rail down onto the bottom bar of both feet. The mouth is wider than the
   foot, and the ribs tighten as the flat underside lands on the bar. Do the same with
   the second rail.
3. Slide the rails along the feet to the spacing the boards need. Keep them on the flat
   run of the foot, forward of the heel. The preview shows them 55 mm apart.
4. Screw the boards down through the holes. The holes are 3.4 mm, on an 8 mm grid, two
   rows staggered by 4 mm. Use an M3 screw from above and a nut under the rail. An
   M3×16 clears a 1.6 mm board plus the 8 mm bar.

## Not verified
- No test print of this socket yet.
- Panel dimensions are still estimates.
