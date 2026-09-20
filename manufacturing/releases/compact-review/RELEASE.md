# Compact prototype review — 2026-09-20

Board B is **110 × 95 mm**, reduced from 150 × 115 mm: **39.4% less PCB area**.
The +12 V / 1.2 A, −12 V / 0.8 A and +5 V / 0.5 A targets and both synth sockets
are retained. The earlier larger prototype is archived under
`boards/board-b/archive/150x115` in the repository.

- Four Faston blades face outward from the left edge. Their model transforms now align with the actual mounting holes.
- P1 is on the top edge: ATT, PDOK, GND, NC; 2.54 mm pitch and 0.55 mm copper-to-edge setback.
- Board P's broken model paths and USB-shell model offset are corrected. All 19 fitted P parts and 74 fitted B parts have visible models. L1 is a clearly documented maximum-dimension envelope, not detailed manufacturer CAD.
- Board P's electrical copper and placement are unchanged by these model fixes. The shared connector and three mounting holes retain their mating XY geometry.

| Board | Size | Copper | JLCPCB files | Preview |
|---|---|---|---|---|
| P | 27 × 40 mm | 2 layers, 1 oz | [Gerber ZIP](board-p/board-p-gerbers.zip), [BOM](board-p/bom.csv), [CPL](board-p/cpl.csv) | [3D](board-p/3d-top.png) |
| B | 110 × 95 mm | 2 layers, 2 oz | [Gerber ZIP](board-b/board-b-gerbers.zip), [BOM](board-b/bom.csv), [CPL](board-b/cpl.csv) | [3D](board-b/3d-top.png) |

Both use 1.6 mm FR-4. Native ERC/DRC reports have **zero errors and zero unrouted
connections**. Board B has zero schematic parity issues. Its 48 thermal vias,
wide main current paths and connected ground pours pass the geometry checks;
independent Gerber/drill, BOM/CPL, archive and checksum verification also passes.
Negative tests reject corrupted files, wrong coordinates, missing thermal/ground
vias, a wrong tab net and narrowed load paths. Documentation checks passed 512
tests and 36 browser cases.

Warnings remain visible in the full reports: Board B has 27 vendor artwork-over-pad
warnings and seven intentional per-instance artwork differences; Board P retains
its reused artwork/library warnings. Silkscreen exports subtract mask openings.

**These are prototype fabrication files.** Reduced copper area does not establish
full-load cooling. Temperature rise, startup, ripple, physical cable/clip/stack fit,
and exact-part JLCPCB assembly orientation still need verification. Read
[ORDER-NOTES](ORDER-NOTES.md), especially the current-limited **5 V-only initial
programming with Board B disconnected** and verified 15 V-only PD configuration.
No order has been placed.
