# Corner supports and accessible probes — 2026-09-21

Board B remains **110 × 85 mm**, with the same output targets and fitted parts.
The PD module moves **12 mm down and 0.5 mm left** on the front/component side.
USB still opens at the left edge. The module no longer covers the independent
top-left corner support or the seven edge test contacts.

The PD transform is **P(x,y) → B(y−0.5,x+12)**. J5 is at (37.2,24.9), on F.Cu at
270°. All six mating nets are checked pin-to-pin. PD mounting holes H1–H3 remain
3.2 mm at (3.5,16), (3.5,35), and (32.1,24.8). Board P itself is unchanged.
The nominal CAD face spacing remains 11.1 mm; physical connector seating and
mount hardware still need confirmation.

Four separate **3.0 mm NPTH support holes** sit 4 mm from the adjacent board edges:
H7 (4,4), H4 (106,4), H5 (4,81), and H6 (106,81). The supplier-linked
[HC-11 drawing and limitations](mechanical/supports/README.md) are bundled. These
board-only holes are excluded from the electrical BOM and placement files.

All seven pogo contacts move **20 mm right**, retaining 2.54 mm pitch,
1.5 × 2.5 mm bare-copper pads, no paste, and a 0.55 mm copper setback from the top
edge. Left to right they are ATT, PDOK, GND, NC, TP3 +13.44 V PRE, TP4 +6.519 V PRE,
and TP5 −14.145 V PRE, at X=56.19 through 71.43 mm and Y=1.8 mm. Their labels move
with them. The four screw-terminal rail labels remain on both sides.

C5 moves to (18,6), rotated 0°, outside the PD substrate projection; C46 moves to
(28,6.5). C32/R3/R4 sit to the left of the relocated PD mounting hole. D2 moves
1.25 mm left to clear J5. The local buck switching/bootstrap/feedback routing and
negative-converter loops are preserved. Input feeds retain 1.5 mm traces and load
outputs retain their checked ≥1 mm paths. The new 0.25 mm signal and measurement
branches do not carry the LDO load currents. A short local via connects the moved
feedback divider's ground to the common return.

| Board | Size | Copper | Fabrication and assembly |
|---|---|---|---|
| P | 27 × 40 mm | 2 layers, 1 oz | [Gerbers](board-p/board-p-gerbers.zip), [BOM](board-p/bom.csv), [CPL](board-p/cpl.csv) |
| B | 110 × 85 mm | 2 layers, 2 oz | [Gerbers](board-b/board-b-gerbers.zip), [BOM](board-b/bom.csv), [CPL](board-b/cpl.csv) |

Both PCBs use 1.6 mm FR-4. The 72 fitted B parts and 19 fitted P parts are on each
board's front. Exact-part rotations and through-hole assembly scope must be
reviewed with the assembly vendor.

Open the [portable KiCad assembly](mechanical/assembly/preview.kicad_pcb), with
bundled models, or see the [populated stack](mechanical/assembly/top.png) and
[back view](mechanical/assembly/bottom.png). This display copy is excluded from
manufacturing; edit `boards/board-b/board-b.kicad_pcb` in the repository.

Native checks report **zero ERC/DRC errors and zero unrouted connections** on both
boards, with zero Board B schematic parity issues. Power/ground connectivity,
model registration, populated cross-board collision, C5 maximum envelope and the
project's assumed support-column clearance are checked. The support-column
screen uses a 6 mm diameter assumption: the supplier does not dimension the full
head, pillar or adhesive foot, so this is not an exact HC-11 fit certification.
Board B retains 27 vendor silkscreen-over-pad warnings and two intentional socket
artwork/library differences. Independent Gerber/drill, BOM/CPL and file-integrity
checks are retained with the package.

**HC-11 height remains an unresolved enclosure constraint.** Board B installs
front/components down. The nominal 11 mm support cannot clear a flat floor:
Board P's substrate reaches 12.7 mm and terminal height reaches 14.2 mm at the
drawing maximum. Solder tails and mounting hardware also need clearance. Taller
supports/risers or real floor cutouts are required; no alternative support or
finished enclosure has been selected or qualified. A proposed 16 mm support is
only a candidate, not a guaranteed completed assembly fit.

This is a prototype package. Keep shared targets of +12 V / 1.2 A, −12 V / 0.8 A
and +5 V / 0.5 A across terminals and synth sockets. Verify finished-hole retention,
adhesive/base fit, connector seating, wire and screwdriver access, then measure
startup, ripple and full-load heating. See [ORDER-NOTES](ORDER-NOTES.md), including
current-limited **5 V-only initial programming with Board B disconnected** and
verified 15 V-only PD configuration. No order has been placed. Earlier packages
are historical revisions.
