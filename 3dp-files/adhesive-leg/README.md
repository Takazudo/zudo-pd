# Adhesive PCB leg with M3 screw grip

Print **four legs** for the current Board B. The leg has an **18 mm seating height**,
a broad flat adhesive base and a screw hole copied from the user's repeatedly
tested `bar-30hp.stl`. No modeled thread, tap or threaded insert is required by this
design; the screw engages the same printed aperture as the reference rail.

- [Single leg STL](generated/adhesive-leg-18mm-m3.stl)
- [Four separate legs on one print plate](generated/adhesive-leg-18mm-m3-4x.stl)
- [Preview](generated/preview.png) and [section view](generated/section.png)
- [Editable STEP](generated/adhesive-leg-18mm-m3.step)
- [Installed assembly](generated/installed.png) and [fit report](generated/fit-check.json)

All dimensions are millimetres. Print at **100% scale**, with the flat base on the
bed and the screw opening upward. Use the material and hole-compensation settings
that worked for the tested rail. The straight vertical bore needs no supports.

| Feature | Dimension |
|---|---|
| Adhesive face to PCB seating face | 18 mm |
| Base | 14 × 14 × 2 mm, rounded corners R2 |
| Pole and PCB seating face | Straight Ø7 mm; no top taper |
| Pole-to-base reinforcement | R2 fillet |
| M3 gripping section | Exact reference polygon, 4.5 mm deep |
| Total blind depth | 4.5 mm; no lower cavity |
| Solid material below blind hole | 13.5 mm |

The measured reference hole is slightly lobed, with 27 straight edges and a
2.8928 × 2.9149 mm bounding box. Those dimensions are not a circular drill size.
[reference-bore.json](reference-bore.json) retains the exact polygon from source
hole 12, its original coordinates and source hash. The upper 4.5 mm gripping
section preserves that profile without taper, smoothing or an entrance chamfer.
The hole ends after that 4.5 mm section; everything below it is solid.
The original rail STL is unchanged.

Use an **M3 × 5 mm non-countersunk screw**, inserted from the visible PCB back
into the leg. Through the 1.6 mm board it enters 3.4 mm, leaving 1.1 mm to the
blind floor. An M3 × 6 mm screw with a washer at least 0.5 mm thick enters at
most 3.9 mm, leaving at least 0.6 mm. These are nominal dimensions; verify the
actual hardware stack. **The earlier M3 × 8 mm screw is too long for this revision.**
Fit the legs and screws before applying adhesive to the flat undersides.

The existing PCB corner holes are nominally **3.0 mm**, so a nominal Ø3 mm screw
has zero designed passage clearance. Check that the actual screw passes freely
through the finished PCB hole; this STL task does not enlarge the PCB holes or
change the JLCPCB package. The copied plastic gripping aperture and the PCB
passage hole serve different purposes.

The four feet sit at H4 (106,4), H5 (4,81), H6 (106,81) and H7 (4,4). Their bases
extend 3 mm beyond the PCB edges, requiring a **116 × 91 mm** adhesive footprint.
The PCB remains 110 × 85 mm. The 7 mm seating diameter keeps the leg clear of the
nearby top-right fuse. The earlier taper served this clearance; a straight
7 mm pole maintains it throughout the post. With an 18 mm seating
height, the 14.2 mm terminal envelope has 3.8 mm nominal floor clearance. Adhesive
tape adds its compressed thickness; no tape allowance is needed to obtain the
18 mm geometry.

The [fit report](generated/fit-check.json) records checks against the current
populated B+P assembly, including the four whole legs and conservative component
envelopes. Printed fit, screw retention/torque, adhesive grip and temperature
performance remain physical checks. The user's proven rail geometry is the screw
fit reference; it is not a new load or material qualification for these legs.

Regenerate and verify:

```sh
uv run 3dp-files/adhesive-leg/generate.py
uv run 3dp-files/adhesive-leg/verify.py
```

[spec.json](spec.json) holds the editable dimensions. The generator emits the
single STL, four-part plate, STEP and rendered views for the current design. The verifier checks the
actual exported geometry and assembly; its optional reference-STL argument can
also recheck the user-supplied rail. Existing PCB and manufacturing files are
read-only inputs.
