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
that worked for the tested rail. The part needs no external supports; the small
internal shoulder above the screw-tip pocket is part of this new print geometry.

| Feature | Dimension |
|---|---|
| Adhesive face to PCB seating face | 18 mm |
| Base | 14 × 14 × 2 mm, rounded corners R2 |
| Main pole | Ø8 mm |
| PCB seating face | Ø7 mm, tapering to Ø8 over 2 mm |
| Pole-to-base reinforcement | R2 fillet |
| M3 gripping section | Exact reference polygon, 4.5 mm deep |
| Lower screw-tip pocket | Ø3.4 mm; total blind depth 10 mm |
| Solid material below blind hole | 8 mm |

The measured reference hole is slightly lobed, with 27 straight edges and a
2.8928 × 2.9149 mm bounding box. Those dimensions are not a circular drill size.
[reference-bore.json](reference-bore.json) retains the exact polygon from source
hole 12, its original coordinates and source hash. The upper 4.5 mm gripping
section preserves that profile without taper, smoothing or an entrance chamfer.
The larger blind pocket below is a new feature that gives the screw tip space
without increasing the tested gripping length. The original rail STL is unchanged.

Start with an **M3 × 8 mm non-countersunk screw**, inserted from the visible PCB
back into the leg. Through the 1.6 mm board this inserts 6.4 mm into the leg:
4.5 mm of gripping length and 1.9 mm into the clearance pocket, leaving 3.6 mm to
the blind floor. Any washer subtracts its thickness from that insertion. Fit the
legs and screws before applying adhesive to the flat undersides.

The existing PCB corner holes are nominally **3.0 mm**, so a nominal Ø3 mm screw
has zero designed passage clearance. Check that the actual screw passes freely
through the finished PCB hole; this STL task does not enlarge the PCB holes or
change the JLCPCB package. The copied plastic gripping aperture and the PCB
passage hole serve different purposes.

The four feet sit at H4 (106,4), H5 (4,81), H6 (106,81) and H7 (4,4). Their bases
extend 3 mm beyond the PCB edges, requiring a **116 × 91 mm** adhesive footprint.
The PCB remains 110 × 85 mm. The 7 mm seating diameter keeps the leg clear of the
nearby top-right fuse; the pole widens below that component. With an 18 mm seating
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
single STL, four-part plate, STEP and rendered views. The verifier checks the
actual exported geometry and assembly; its optional reference-STL argument can
also recheck the user-supplied rail. Existing PCB and manufacturing files are
read-only inputs.
