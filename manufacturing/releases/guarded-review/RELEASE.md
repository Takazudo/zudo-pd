# Guarded compact prototype — 2026-09-20

Board B is **110 × 85 mm**: 10.5% less area than the previous 110 × 95 mm
revision and 45.8% less than the original 150 × 115 mm prototype. The targets
remain +12 V / 1.2 A, −12 V / 0.8 A and +5 V / 0.5 A, with two synth sockets.

All seven test contacts now sit along the top edge at 2.54 mm pitch: ATT, PDOK,
GND, NC, TP3, TP4 and TP5. The three rail pads share P1's ground contact; the NC
contact remains unconnected. Pads have no paste openings and are excluded from
assembly orders.

The four Fastons are on the bottom, facing inward, with their metal inside the
board outline. A printed guard separates the four terminal bays. Three rounded
T-shaped PCB notches and press-fit caps retain it; a separate sliding shutter
shields the last cable exit from the synth socket's solder tails. Board P is
rotated under the upper-left corner, leaving its USB connector accessible.

| Board | Size | Copper | JLCPCB files | Preview |
|---|---|---|---|---|
| P | 27 × 40 mm | 2 layers, 1 oz | [Gerbers](board-p/board-p-gerbers.zip), [BOM](board-p/bom.csv), [CPL](board-p/cpl.csv) | [3D](board-p/3d-top.png) |
| B | 110 × 85 mm | 2 layers, 2 oz | [Gerbers](board-b/board-b-gerbers.zip), [BOM](board-b/bom.csv), [CPL](board-b/cpl.csv) | [3D](board-b/3d-top.png) |

Both PCBs are 1.6 mm FR-4. The B placement file contains 69 top-side and five
bottom-side fitted parts; the four Fastons and the PD mating connector are on
the bottom. Confirm the exact parts and rotations in the assembly service's
preview before ordering.

Print and assembly files:

- [Print ZIP: five assembly pieces plus ten fit coupons](mechanical/faston-cover/generated/print-parts.zip)
- [Assembly instructions and mating envelope](mechanical/faston-cover/README.md)
- [Guard-only STEP](mechanical/faston-cover/generated/faston-cover.step)
- [Underside assembly image](mechanical/faston-cover/generated/preview/populated-stack.png)
- [Complete assembly STEP](mechanical/faston-cover/generated/preview/populated-stack.step)
- [Interactive KiCad assembly preview](mechanical/faston-cover/generated/preview/guarded-assembly-preview.kicad_pcb)

The interactive assembly is a review copy with bundled component models. Use
`boards/board-b/board-b.kicad_pcb` in the repository for PCB edits; do not use the
assembly-preview PCB for fabrication.

Both boards have **zero ERC/DRC errors and zero unrouted connections**. Board B
has zero schematic parity issues. Its 48 thermal vias, seven ground stitches,
wide load paths and segmented ground cross-sections pass the geometry checks.
Independent Gerber/drill parsing, BOM/CPL identity/coordinates, ZIP contents and
source/artifact checksums pass. Negative controls reject wrong connector
positions, damaged edge geometry, misplaced pogo contacts, missing vias, wrong
power nets, narrowed load paths and tampered release files.

All 31 active STEP/WRL model pairs pass a sampled alignment screen. The populated
assembly and nominal cable/shutter insertion sweeps pass CAD collision checks.
The guard's 15 print meshes are checked for closed surfaces and valid volume.
Documentation checks passed 512 tests and all published references. These checks
verify the nominal files; they do not establish hardware performance.

Board B retains 27 vendor artwork-over-pad warnings and two intentional header
artwork/library differences. Board P retains its reused artwork/library warnings
and three intentional mounting footprints. All warnings remain in the reports;
silkscreen plotting subtracts solder-mask openings.

**This is a prototype package.** Actual female receptacles and sleeves have not
been selected. They must fit the stated bay and stepped J8 envelope; arbitrary
Faston crimps are not proven compatible. Print the coupons first, then verify
key/cap/shutter retention, solder-tail clearance, cable access and the PD stack's
seated height. The guard is not a rated strain relief. Test startup, ripple and
full-load temperatures with the guard installed before claiming the output
ratings. Read [ORDER-NOTES](ORDER-NOTES.md), especially current-limited **5 V-only
initial programming with Board B disconnected** and verified 15 V-only PD
configuration. No order has been placed.
