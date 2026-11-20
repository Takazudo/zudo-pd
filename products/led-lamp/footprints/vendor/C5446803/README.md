# G-Switch C5446803: project-derived G020 model

Selected part: **SS-12D01-G020 / C5446803**. The component's electrical, supplier
availability and footprint evidence is maintained by its component record. This
folder documents the CAD correction only.

The corrected `SW-TH_SS-12D01-G020.step` and `.wrl` are **project-derived from
supplier family CAD**, not unmodified, exact manufacturer CAD. Both describe the
same solid. The WRL uses a neutral gray material; supplier material colors are not
preserved.

## Source discrepancy

The EasyEDA assets retrieved for C5446803 are named `SW-TH_SS-12D01-GX`, a family
model. Their original bytes are retained here for reproducibility:

- STEP SHA256: `f6c8743b8d28de4a7cbed027ee66539c66e565d853dd9f9d756137ad410e2356`.
- WRL SHA256: `8180e3e024b79f364bb46790d19ddc8ae63afa7a91d479e3e72e1c1cd8e6be80`.
- Manufacturer drawing `SS-12D01-GXXX`, revision X1, 2019-05-29; supplied PDF
  SHA256: `bdb6ae64b9de1156d00ad4aefee51b14a43ccd3aeaf1bdc2f86d2242f1fe68a1`.
  It gives a 3.5 mm case, G020 = 2.0 mm actuator projection, 1.5 mm square actuator,
  2 mm travel, 2.5 mm contact pitch, and 0.5 × 0.3 mm terminals.

The original STEP is one valid solid. Its case base/top planes are Z0 and Z3.5;
its actuator reaches Z7.5, hence **4 mm projection**, not the selected 2 mm.
The original WRL uses a different seating frame: case base/top approximately
Z0.4963/Z3.9962 and actuator top Z7.9962. Its tessellated lug tips are Z−4.3.
Using that unmodified family model would overstate the G020 actuator height.

## Exact correction and seating frame

`derive-model.py` performs an Open CASCADE Boolean cut above **source Z5.5**.
Only the actuator occupies that volume: X−1.75…−0.25, Y−0.75…+0.75, Z3.5…7.5.
The cut leaves a 1.5 × 1.5 × 2.0 mm exposed actuator in the source's left travel
position. It creates a flat actuator top; the taller family model's tip chamfer
is removed. The precise molding/chamfer of a purchased G020 remains unverified.

All geometry below the cut, including case, internal geometry and all three
terminals, is unchanged. Boolean difference checks verify this in both directions.
The model is **not scaled**. A rigid +0.5 mm Z translation places both outputs in
a common seating frame corresponding to the original WRL's approximate +0.4963
mm offset. This normalizes a roughly 0.004 mm mesh/frame discrepancy while keeping
the case tabs above the nominal PCB surface. The original STEP included case/tab
planes below its case-base Z0, down to Z−0.4; treating that original case base as
the PCB surface would bury those features.

Resulting coordinates, in mm:

| Feature | Geometry |
| --- | --- |
| Complete XY envelope | X−4.4…+4.4, Y−1.95…+1.95 |
| Housing base/top | Z0.5 / Z4.0 |
| Exposed actuator | Z4.0…6.0; 2.0 mm projection |
| Lug tips | Z−4.3 |
| Terminal centers | X−2.5, 0, +2.5; Y0 |
| Terminal section | 0.5 × 0.3 mm |
| Maximum reach above nominal PCB | 6.0 mm, including the 0.5 mm seating offset |

Thus 3.5 + 2.0 = 5.5 mm is **case-base-to-actuator-tip**, while this seated model
reaches 6.0 mm above the PCB plane. The 0.5 mm seating assumption and actual
insertion depth require prototype confirmation. On a 1.6 mm PCB, the retained
4.3 mm terminal reach gives about 2.7 mm protrusion on the opposite side, before
solder or trimming. Check that volume in the assembled enclosure.

## Project-adapted through-hole fit

The original supplier footprint's 0.9144 mm drill fits nominal terminals, but
not a conservative dimensional stack. Both canonical footprint copies now use
**1.600 mm circular plated holes, 2.250 mm copper pads and 2.5 mm pitch**. The
internal actuator sketch moves to F.Fab to clear the enlarged pads; the exterior
case outline remains on F.SilkS. This is a project-adapted land pattern, not a
manufacturer-recommended hole diameter or proof of assembly acceptance.

The drawing's general tolerances are ±0.20 mm for one-decimal dimensions,
±0.30 mm for integer dimensions and ±3° for angles. We conservatively apply these
to the 0.5 × 0.3 mm terminal section, 2.5 mm adjacent pitch and 5 mm outer span.
The maximum section is therefore 0.7 × 0.5 mm. Relative to the first terminal,
longitudinal center errors are `(0, e1, e2)`, with `|e1| ≤ 0.20` and `|e2| ≤ 0.30`.
Their largest possible spread is 0.50 mm. Translating the whole part to center
that spread during insertion bounds the residual error of every terminal by
**0.25 mm**. This is a best-fit insertion condition, not forced alignment of the
middle terminal to the footprint origin.

[JLCPCB's rigid PCB capabilities](https://jlcpcb.com/capabilities/pcb-capabilities/),
checked 2026-09-06 JST, specify finished through-hole diameter +0.13/−0.08 mm
and hole-position tolerance ±0.05 mm. We conservatively allow that position
error independently in X and Y. Adding ±3° terminal-section rotation, a bounding
corner in the smallest finished hole is:

```text
x = 0.35 cos(3°) + 0.25 sin(3°) + 0.25 + 0.05 = 0.662604 mm
y = 0.25 cos(3°) + 0.35 sin(3°) + 0.05        = 0.317975 mm
corner radius = sqrt(x² + y²)                = 0.734951 mm
minimum finished-hole radius = (1.60 − 0.08)/2 = 0.760000 mm
remaining radial fit margin                 = 0.025049 mm
```

Using both coordinate maxima together is conservative: they need not occur at
the same rotation. The calculation covers undeformed terminals sharing the
specified row centerline, dimensional pitch/span variation and hole placement;
independently bent leads or extra unspecified row straightness are not certified.
The footprint does not require force-fitting a misaligned part.

Nominal annulus is `(2.25 − 1.60)/2 = 0.325 mm`. At the largest finished hole,
with 0.05 mm drill-to-pad displacement, the remaining ring is
`(2.25 − 1.73)/2 − 0.05 = 0.210 mm`. Nominal adjacent-pad copper clearance is
`2.50 − 2.25 = 0.250 mm`; worst-case hole-edge spacing with two opposing
0.05 mm positional errors is `2.50 − 0.10 − 1.73 = 0.670 mm`.
[JLCPCB lists](https://jlcpcb.com/capabilities/pcb-capabilities/) a 0.45 mm
pad-hole spacing minimum and, for two-layer 1 oz boards, a preferred nominal
annulus of at least 0.25 mm with an absolute minimum of 0.18 mm. The project
geometry exceeds those values under the stated calculation.

These holes deliberately allow the drawing's loose general tolerances. Their
solder fill, insertion alignment and the switch's actual seating depth still
need fabricator/first-article confirmation. The retained CAD terminal reach is
4.3 mm below the seating plane: on a 1.6 mm PCB, allow **2.7 mm opposite-side
protrusion**, plus solder or any agreed trimming.

## Reproduction and validation

Use Python 3.12+ and `cadquery-ocp==7.9.3.1.1`, then run:

```sh
python footprints/vendor/C5446803/derive-model.py
```

The script hash-checks its input, checks the actuator-only cut volume, verifies
all three terminal sections and pitch, checks Boolean identity below the cut,
exports real STEP geometry, reloads it and verifies validity/volume/bounds. It
meshes that reloaded solid for WRL at 0.005 mm deflection, then divides coordinates
by 2.54 for KiCad's 0.1-inch WRL units. No footprint model scale correction is
required: both model transforms remain identity.

The result remains one valid solid. Its volume changes from 111.710729 to
107.444729 mm³. The WRL has 10,093 vertices and 12,380 triangles. Full measured
values and hashes are in `model-audit.json`. Repeated generation was checked to
produce identical output hashes:

- Derived STEP: `fc474ae1f7fde48b66f40c479a7e512004d33b76240da28d623a281ec1a7d261`.
- Derived WRL: `fe38c0a93172ea73ea736917b20612818d97438ed1d9c4d20911c7c4f35240e7`.

The CAD correction establishes the selected actuator projection without inventing
an exact supplier G020 model. It is an enclosure-layout aid, not certification of
as-built tolerances, insertion depth, molding details or assembly acceptance.
