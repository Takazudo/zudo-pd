# Underside Faston guard

This is a **fit prototype** for the four inward-facing Board B terminals. The
male tabs remain inside the PCB outline. One printed guard separates the four
rails; three small removable caps hold its locating keys. A separate sliding
shutter shields the last cable exit from nearby synth-socket solder tails. The cover is not a
rated cable strain relief, electrical enclosure, or verified thermal solution.

The guard is adapted for this board from a pin/socket assembly pattern. Its CAD,
PCB-edge keys and dimensions are generated specifically for zudo-pd.

## Geometry shared with the PCB

`pcb-contract.json` is authoritative. It contains every line and arc for the
three rounded T-notches. Do not approximate them with rectangular slots.

| Item | Contract |
| --- | --- |
| PCB | 110 × 85 × 1.6 mm |
| Terminal centers | x=6; y=37, 49, 61, 73 mm |
| Terminal side/orientation | B.Cu, 270°; blades point inward along +X |
| Bare metal extent | Approximately x=2.74–23.06 mm |
| Guard footprint | Main body x=0–36; y=31–79 mm; shutter grip reaches x=38 mm |
| Guard bottom | 13.7 mm below PCB top; 12.1 mm below PCB bottom |
| Floor thickness | 1.6 mm |
| Key positions | Left-edge notches centered at y=43, 55, 67 mm |
| Notch shape | 3 mm neck, 6 mm pocket, 4 mm depth, R0.5 corners |
| Printed key clearance | 0.20 mm per side; 0.30/0.40 mm trial keys also supplied |
| Caps | 2.8 mm peg; default 2.7 mm socket, with fit coupons |

World coordinates use PCB top **Z=0** and bottom **Z=−1.6 mm**. CAD X matches
KiCad X; CAD Y is negative KiCad Y. The STEP and WRL files retain these assembly
coordinates. Print STLs are separate, oriented parts resting on Z=0.

Current JLCPCB guidance permits non-plated slots from 1.0 mm and lists ±0.2 mm
routed dimensional tolerance. Its rounded-corner guidance supports R0.5 with a
1 mm router bit. These bounds support the nominal notch, while actual fit still
needs checking. Sources: [capabilities](https://jlcpcb.com/capabilities/Capab),
[rounded corners](https://jlcpcb.com/blog/rounded-corners-pcb-design).

The T-heads provide geometric retention along the PCB plane. Cap retention in
Z depends on calibrated print fit. Default 0.1 mm diametral interference is
intentional, not a measured fit. The caps have no screw or independent latch.
Do not use the guard to carry insertion force or suspend the board by its cables.

## Print and assemble

1. Print the peg and socket coupons with the intended material and profile.
   Select a snug socket that can be removed without cracking the peg. Regenerate
   with `--socket-diameter` if a different coupon fits better.
2. Check a T-key coupon in an actual routed PCB notch. Fabrication tolerance,
   print shrinkage and surface roughness can change the nominal clearance.
3. Print the guard floor-down. Trial-fit the separate shutter in its groove
   coupon; its closed channel ends provide the inward stop. Outward retention
   remains a measured fit requirement. Print caps closed-face-down with sockets upward;
   the supplied STLs already have this orientation. The guard includes gussets
   under the key heads and narrow floor vents.
4. Install the guard from below after soldering and inspecting the terminals,
   with its shutter removed. Seat all three T-heads, then fit the caps from above.
5. Mate the cables within the stated envelope, then slide the J8 shutter inward
   from +X along its side grooves. Its motion passes above the crimp/wire tail
   and below the socket tails. Remove the shutter before servicing that cable.
6. Verify solder clearance, cap retention, cable access and repeated insertion
   on the physical assembly. Repeat the full-load temperature checks with the
   cover installed because it changes convection near the power stage.

A rigid PETG trial at 0.2 mm layers and a 0.4 mm nozzle is a starting assumption,
not a qualified process. Inspect small holes, overhangs and pin layers in the
slicer. Printer/material selection and thermal limits remain the builder's
measured inputs.

The usable envelope is at most 8.2 mm wide in Y. For J6/J9/J7 it spans
Z=−11.8 to−2.6 mm. J8 has a lower head limit: Z=−11.8 to−3.3 mm for
x=15–29.7 mm; its crimp/wire exit at x=29.7–36 mm must remain below Z=−4.8 mm.
These restrictions are measured from the PCB top, not the cover floor.

The earlier taller J8 envelope crossed nearby J10 solder tails; that diagnostic
is retained in `verification.json`. The revised envelope and separate shutter
are checked against the populated boards. The nominal female-envelope path is
swept 22 mm from +X with the shutter absent; the shutter then has its own 8 mm
straight insertion sweep. Intended contact with the male terminal is excluded
from that envelope check. Actual female contact geometry is still required.

No exact female terminal or insulating sleeve is selected. The manifest states
a nominal access envelope opening toward +X; it cannot establish compatibility
with an arbitrary receptacle, crimp, wire gauge or housing. Use an insulated
mating assembly and verify it before applying power.

## Generate and verify

```sh
uv run 3dp-files/faston-cover/generate.py
uv run 3dp-files/faston-cover/generate.py --socket-diameter 2.8
uv run 3dp-files/faston-cover/verify.py boards/board-b/board-b.kicad_pcb
python3 3dp-files/faston-cover/finalize-preview.py boards/board-b/board-b.kicad_pcb
python3 -m unittest discover -s 3dp-files/faston-cover -p 'test_*.py'
```

For a temporary PCB, append `--project-dir boards/board-b`. Verification compares
its exact outline and terminal placement, checks STL integrity and asset hashes,
and freshly exports populated native STEP geometry for solid collision checks.
`--geometry-only` explicitly skips the populated-model checks and reports that
limited result.

Outputs are under `generated/`: print STL files, a print ZIP, guard-only STEP/WRL,
a manifest, reference substrate and PNG previews. The set contains five
assembly pieces and ten small fitting coupons. The guard's STEP/WRL includes
only printed pieces. PCB and terminal reference geometry is excluded from print
files and from that guard-only model. A separate verification report binds the
checks to the exact PCB SHA-256.

After full verification, `generated/preview/guarded-assembly-preview.kicad_pcb`
opens the complete B/P/cover assembly in KiCad. It preserves all original Board B
geometry and adds one board-only model footprint excluded from BOM/CPL. Model
paths reference bundled WRL/STEP companions in its `models/` directory, so
the complete cover folder remains portable when copied into a release. This is an interactive review copy, not a
manufacturing PCB. `populated-stack.step` is a separate review assembly;
`board-p-stacked.step` places P at (x,y)→(y,27−x), nominal top Z=−12.6 mm.
The shared header's actual seated height still needs measurement.

The mesh preview is a geometric illustration. It does not prove physical fit,
current capacity, temperature, insulation compliance or retention force.
