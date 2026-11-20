# Straight starburst bands — prototype 03

A **2.4 mm thin base plus six 13 mm single-piece bands**, approximately 116 mm across
and 86.4 mm tall excluding projecting fasteners. All star profiles align straight:
no twist and no assembly seams inside a band.

## Parts and color experiments

| File | Suggested color | Function |
| --- | --- | --- |
| 00-base | Clear | Thin mounting/access plate |
| 01-band-usb | Clear | 13 mm bottom band with USB notch |
| 02-band | Clear | 13 mm interchangeable middle band |
| 03-band | Amber | 13 mm interchangeable middle band |
| 04-band | Teal | 13 mm interchangeable middle band |
| 05-band | Clear | 13 mm interchangeable middle band |
| 06-band-top | Smoke | 13 mm top band without exposed pins |

Print each band in any color. **Bands 02–05 have identical geometry** and can be
reordered. Band body height excludes its 1 mm locating pins, which nest into the
next band and do not add to assembled height.

The current ZIP contains **21 assembly parts and eight fitting coupons**: seven
base/band pieces, eight PCB spacers, three feet and three flat-printable square posts. Replace your old extracted set.
The historical download name remains `smoke-reversing-stls.zip`; its contents are v3.
Find it in `doc/public/assets/enclosure/`, alongside `assembly-step.zip` containing
the complete assembled STEP. Reference electronics/hardware are excluded from print STLs.
The doc page `/docs/architecture/enclosure/` embeds the interactive preview.

## Connections and access

Three Ø2.4 × 1 mm pins enter Ø2.8 × 1.35 mm sockets and key the band orientation.
Three **printed 4 × 4 × 85.4 mm cuboid posts** pass through centered square holes
in the bands, base and feet. The default hole is exactly **4 × 4 mm** in CAD,
matching the requested post size. The posts are exported flat on an 85.4 × 4 mm
long face (only 4 mm tall on the print bed), but appear upright in the assembly.

The feet are **printed Ø12 × 6 mm round pads with centered square through-holes**,
without nut recesses. Try TPU for the feet and a rigid material for the posts.
Their intended assembled position leaves the post ends 1 mm above the bottoms
of the feet and flush with the top band; check that depth when fitting them.

There are no shell nuts, washers or threaded rods in this revision. Straight posts
provide fit-based retention, not positive axial locking or screw clamping. Support
the base when lifting the prototype; verify that parts do not slide unintentionally.

Print the 20 mm-long square-post coupon lying flat and the 13 mm-tall square-hole
coupons before the long posts. Holes of 4.0, 4.2 and 4.4 mm are supplied. Equal
nominal dimensions may bind after printing. If the 4.2 mm coupon fits best, regenerate
with `--post-clearance 0.2`; 0.4 selects 4.4 mm holes. The default remains zero.

The potentiometer opening is now a **30 × 38 mm rounded rectangular finger window**
instead of Ø24 mm. It extends toward the free side of the wheel while preserving the
nearby shared PCB mounting post. Corner radius is 6 mm. The switch retains its
20 × 24 mm opening. The wheel is still recessed: try actual fingertip adjustment
through a base print before committing to all bands.

The first band has an **18 × 13 mm full-height USB notch**. The second band closes
the roof during assembly, avoiding a wide printed bridge. Clearance checks use a
16 × 8 mm overmold to the PCB edge and an 8.4 × 2.6 mm metal-nose corridor.
Actual cable engagement is a physical check. Open top/base vents are not a thermal qualification.

## Print and assemble

1. Print the pin/socket coupons in the intended PETG. The 0.4 mm diametral-clearance
   coupon matches the enclosure. Adjust `socket_diameter` and regenerate if needed.
2. Print the base and spacers; dry-fit both boards and try operating the wheel by finger.
3. Board P uses three 5 mm spacers. Secure its independent hole before fitting the
   two 11 mm shared interboard spacers, three 17.6 mm Board L supports, and Board L.
   LEDs face upward, controls downward. The default 11 mm facing-surface gap is a
   prototype assumption: measure the naturally seated header pair before tightening.
4. PCB hardware: five approximately M3 × 25 mm nylon screws, one M3 × 14 mm nylon
   screw for Board P's independent hole, and six nylon nuts. Verify engagement and
   adjust lengths for your actual hardware.
5. Print the bands flat with pins upward, as separate objects in Bambu Studio.
   No additional rotation is required; an AMS is optional. Exchange middle bands freely.
6. Print the square posts in their supplied long-side-down orientation. Print the
   round feet flat, optionally in TPU using your filament/printer profile. Slide the
   feet, base and bands onto the square posts; keep the bottom post ends recessed
   1 mm above the feet bottoms. No metal shell fasteners are needed.
7. Check cable fit, slider travel, finger access, solder/lead clearance, retention
   and powered temperatures on the physical prototype.

Use the intended PETG profile, initially a 0.4 mm nozzle, 0.2 mm print layers and at
least three walls. Compare one thick band before the batch; solid/100% infill is an
optical starting point, not a tuned profile. Inspect the small locating-socket
bridges in the slicer; avoid supports inside sockets. The feet have open through-holes
and no internal nut-pocket roofs. Follow filament/plate instructions.
Material guidance: https://wiki.bambulab.com/en/knowledge-sharing/transparent-petg

## Regenerate and verify

`uv` and KiCad (`kicad-cli` on PATH) are enough; no CAD GUI is needed.

```sh
uv run enclosure/generate.py
# Optional measured facing-surface gap:
uv run enclosure/generate.py --board-gap 11.0
# Optional fit adjustment after testing the square-hole coupons:
uv run enclosure/generate.py --post-clearance 0.2
cd doc
pnpm generate:enclosure-viewer
pnpm build
```

Pinned CadQuery 2.6.1 and trimesh 4.8.3 run in an isolated uv environment.
The generator checks connected print bodies, watertight meshes, Z=0 placement,
PCB mounting/connector alignment, assembled solid interference and cable clearance.
The manifest records dimensions and source/mesh hashes and takes precedence after
custom regeneration. `--skip-pcb-models` is for debugging, not clearance validation.
Physical fit, fingertip ergonomics, solder, optical appearance and temperature still
need testing. Preview colors are illustrative; no optical or thermal simulation is claimed.
