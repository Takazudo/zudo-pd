# Screw-terminal prototype — 2026-09-20

Board B now uses **two Kangnex WJ500V-5.08-2P / C8465 screw-terminal blocks** in
place of four Fastons. Both are on top, with wire openings facing left and their
housings inside the board outline. The PCB remains **110 × 85 mm**. The left edge
is straight; no printed terminal guard, retaining notches, caps or shutter are
needed for this revision.

Viewed from the front with the pogo pads at the top, the terminals run from top
to bottom as follows. The two pins in each block are electrically separate.

| Position | Terminal pin | Rail |
|---|---|---|
| First | J6.2 | −12 V |
| Second | J6.1 | GND |
| Third | J7.2 | +12 V |
| Fourth | J7.1 | +5 V |

The existing +12 V / 1.2 A, −12 V / 0.8 A and +5 V / 0.5 A targets are shared
across these terminals and the two synth sockets. The component's current rating
does not increase any board output budget.

All 83 nonterminal footprints, 619 retained track segments and 99 vias match the
archived guarded board exactly. Twelve old terminal segments were removed and
nine new 1 mm segments added. Ground uses both connected pours. Filled copper
was regenerated and checked. Seven edge pogo contacts, the rotated PD-module
interface and all mounting holes are retained.

| Board | Size | Copper | JLCPCB files | Preview |
|---|---|---|---|---|
| P | 27 × 40 mm | 2 layers, 1 oz | [Gerbers](board-p/board-p-gerbers.zip), [BOM](board-p/bom.csv), [CPL](board-p/cpl.csv) | [3D](board-p/3d-top.png) |
| B | 110 × 85 mm | 2 layers, 2 oz | [Gerbers](board-b/board-b-gerbers.zip), [BOM](board-b/bom.csv), [CPL](board-b/cpl.csv) | [3D](board-b/3d-top.png) |

Both PCBs use 1.6 mm FR-4. Board B has 72 fitted parts: 71 on top and the PD
mating connector on the bottom. Board P has 19 fitted parts. The screw terminals
are through-hole components; confirm assembly-service scope and placement
orientation before ordering.

[Assembly bottom view](mechanical/assembly/bottom.png).

The [portable KiCad assembly preview](mechanical/assembly/preview.kicad_pcb)
shows Board B with its stacked PD module. It includes its model files and is a
review copy, not a manufacturing PCB. Use the active repository
`boards/board-b/board-b.kicad_pcb` for PCB edits.

Both boards have **zero ERC/DRC errors and zero unrouted connections**. Board B
has zero schematic parity issues. Mechanical, exact pin-map, wide current-path,
thermal-via and ground-connectivity checks pass. Independent Gerber/drill,
BOM/CPL, ZIP and checksum checks also pass. The component documentation and
published model/footprint references pass their build and validation gates. Negative controls reject swapped
terminal polarity, wrong side/direction, retained notches, narrowed output
routes, missing thermal/ground vias and tampered fabrication files.

Board B retains 27 vendor artwork-over-pad warnings and two intentional synth
header artwork/library differences. Board P retains its reused artwork/library
warnings and three intentional mounting footprints. These remain visible in the
reports; silkscreen exports subtract solder-mask openings.

**This is a prototype package.** The terminal footprint uses reviewed 1.30 mm
finished holes versus the drawing's 1.20 ± 0.05 mm recommendation. Confirm fit
with the purchased parts. The imported visualization has 3.50 mm tails versus
4.50 ± 0.20 mm in the drawing; model alignment is verified, while the conservative
clearance screen uses 4.70 mm. It is not an exact physical-fit certification.
Check actual wire preparation, screw tightening, strain relief, stack fit and
clearance; then test startup, ripple and full-load temperatures. Read
[ORDER-NOTES](ORDER-NOTES.md), especially current-limited **5 V-only initial
programming with Board B disconnected** and verified 15 V-only PD configuration.
No order has been placed. The previous guarded files remain historical and must
not be mixed into this order.
