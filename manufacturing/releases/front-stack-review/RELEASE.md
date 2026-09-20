# Front-side PD stack — 2026-09-20

Board B keeps its **110 × 85 mm** outline and the same output targets. The PD
mating connector **J5 now mounts on the front/component side**, with Board P
facing it on that same side. In the installed orientation, Board B's components
face down on legs and its back is visible from above.

C5 moves below the PD-module area. The two screw-terminal blocks shift down to
make room, and R1/R2 shift 0.5 mm for header courtyard clearance. The six mating
pins and three shared holes are checked through the new P(x,y) → B(y,x) mapping.
The nominal CAD face spacing is **11.1 mm**, preserving contact insertion without
modeled housing overlap. It is not a qualified spacer or seating tolerance.

The four screw-terminal voltages are now printed on **both sides**. Back labels
are mirrored in the KiCad file so they read normally when viewed from the back.
The user's C36/C37 reference positions, top test-point voltage legend and backside
`rev1` marking are preserved.

PTC1/PTC2 had existing 3D bodies displaced by stale footprint model offsets.
Fresh downloads for the exact parts matched the existing WRL files. Corrected
zero offsets place the bodies on their pads; PTC3 needed no change. Every fitted
part now passes both model-path and opaque-body registration screens: 72 on B
and 19 on P. Those screens supplement the STEP datum and mechanical checks;
they do not certify every manufacturer dimension.

| Board | Size | Copper | JLCPCB files | Preview |
|---|---|---|---|---|
| P | 27 × 40 mm | 2 layers, 1 oz | [Gerbers](board-p/board-p-gerbers.zip), [BOM](board-p/bom.csv), [CPL](board-p/cpl.csv) | [3D](board-p/3d-top.png) |
| B | 110 × 85 mm | 2 layers, 2 oz | [Gerbers](board-b/board-b-gerbers.zip), [BOM](board-b/bom.csv), [CPL](board-b/cpl.csv) | [3D](board-b/3d-top.png) |

Both PCBs use 1.6 mm FR-4. All 72 Board B fitted parts are now on the front; P's
independent PCB still has its 19 fitted parts on its own front side. Through-hole
assembly scope and exact-part rotations need review with the assembly vendor.

Open the [portable KiCad assembly](mechanical/assembly/preview.kicad_pcb) to see
both boards together. Its component models are bundled locally. The
[assembled top](mechanical/assembly/top.png) and
[assembled back](mechanical/assembly/bottom.png) show the complete stack and rear
labels. This display copy is excluded from manufacturing; edit the active
repository `boards/board-b/board-b.kicad_pcb` instead.

Both boards have **zero ERC/DRC errors and zero unrouted connections**. Board B
has zero schematic parity issues. Input paths from J5 through C5 to both LM2596
stages and the buck input bank pass the 1.5 mm trace screen. Load outputs pass the
1 mm trace screen; thermal vias and connected ground pours pass their checks.
TP5 uses a 0.25 mm measurement branch, excluded from all load-path proofs.
Independent Gerber/drill, BOM/CPL, ZIP, source and artifact checks pass.

The populated fit screen considers all 1,460 cross-board component/substrate
pairs. Only the intended J5/JOUT1 contact columns overlap; there is no unintended
modeled volume. Maximum C5 and terminal housing/tail envelopes also pass.
Regressions reject reversed header nets/side, wrong mounting transforms, wrong or
missing mirrored labels, stale model offsets, invisible model bodies, missing
thermal/ground vias, narrowed input/output paths and tampered packages.

The reports retain Board B's 27 vendor artwork-over-pad warnings and two
intentional synth-header artwork/library differences. Board P retains its reused
artwork/library warnings and three intentional mounting footprints. Silkscreen
plotting subtracts solder-mask openings.

**This is a prototype package.** Keep the shared targets of +12 V / 1.2 A,
−12 V / 0.8 A and +5 V / 0.5 A across screw terminals and synth sockets. Validate
wire preparation, screw torque, finished-hole fit, leg/enclosure clearance,
connector seating and retention, then measure startup, ripple and full-load
heating. The terminal visualization has shorter tails than its drawing; the
clearance screen uses the drawing's 4.70 mm maximum. Read
[ORDER-NOTES](ORDER-NOTES.md), especially current-limited **5 V-only initial
programming with Board B disconnected** and verified 15 V-only PD configuration.
No order has been placed. Earlier terminal and guarded packages are historical.
