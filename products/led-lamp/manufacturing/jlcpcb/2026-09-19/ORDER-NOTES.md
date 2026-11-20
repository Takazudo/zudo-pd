# JLCPCB order files

The `jlcpcb/2026-09-19/` release requests JLCPCB soldering for every intended
fitted component, including Board L J3 and SWD-adapter J1/J2. These three
previously hand-fit connectors are explicit **release population overrides**.
Original design sources retain their default population settings; the release's
`source/` snapshots, BOMs and CPLs use the assembly overrides consistently.

For each board, upload `<board>-gerbers.zip` for the PCB, `bom.csv` for component
selection, and `cpl.csv` for placement. Do not upload the overall handoff ZIP as a
single PCB: it contains three separate designs.

| Board | PCB | Assembly |
| --- | --- | --- |
| board-p | 27 × 40 mm, 2 layers, FR4, 1.6 mm, 35 µm outer copper | Top-side parts, including through-hole JOUT1 |
| board-l | 60 × 60 mm, 2 layers, FR4, 1.6 mm, 35 µm outer copper | Both sides; top SMD, bottom J2/J3/RV1/SW2 through-hole parts |
| swd-adapter | 36 × 18.1 mm, 2 layers, FR4, 1.6 mm, 35 µm outer copper | Both connectors on top, through-hole assembly |

Select a JLCPCB assembly service that accepts the listed through-hole parts and
Board L's two-sided component installation. Quantity, finish, mask color, stock,
assembly-service eligibility and price are selected in the quote; none are
reserved or purchased by this export. Copper and thickness above are taken from
the board stackups, not an independently approved factory quote.

## Before releasing the order

- **Board L RV1 requires assembler confirmation.** ALPS specifies manual
  soldering for RK10J11E0034 / C470643, while JLCPCB's listing describes wave
  soldering. Request a manufacturer-compatible process from JLCPCB, plus seating
  and retention confirmation for this project's 1.6 mm board. RV1 is included in
  the BOM/CPL; it has not been silently moved to user hand-soldering.
- Compare each JLCPCB placement preview with `assembly-top.svg` and
  `assembly-bottom.svg` (bottom drawing is mirrored to view from underneath).
  Native KiCad rotations are used with recorded JLCPCB corrections. **Board L
  RV1 is corrected from 0° to 180°**, matching the user's manual 180° rotation
  before the reviewed bottom preview on 2026-09-19. This corrects JLCPCB's library
  orientation only; no PCB geometry was rotated. Do not rotate RV1 another 180°
  after uploading the corrected CPL. Check all IC pin-1 marks, LED/diode polarity, USB-C mating direction,
  and connector keys/pin 1 before checkout.
- Read the retained DRC/ERC reports. The initial DRC has no errors or unconnected
  items, but existing silkscreen warnings remain. Board P also has one duplicate
  SCL via, a short dangling gate-track stub and three PCB-only mounting-hole
  parity warnings. SWD adapter J2 differs from the library copy; its numeric
  orientation is covered by `verify_swd_adapter.py`. These exports do not
  change no copper or mechanical geometry. A redundant zero-length SW2
  silkscreen line is omitted in the release snapshot because KiCad 10.0.0 exports
  it as invalid zero-aperture Gerber draws; the surrounding outline is retained.
  This cleanup adds an expected SW2 library-copy mismatch warning in the release
  snapshot. The source Board L has 58 silk warnings; the snapshot has those 58
  plus that one mismatch. ERC has six unspecified-pin warnings each on Boards
  P/L and none on the adapter, with zero ERC errors on all three.
- The existing project component evidence retains prototype/continuity and
  programmed-state checks. PCB fabrication and assembly do not program the
  STUSB4500 NVM or STM32 firmware. The Board P VREG_2V7 external-load question
  remains open before NVM-programming bench work.

Board P **R17/R18 (external Rd) and D6/D7 (optional CC protection) remain DNP**.
Pogo/test pads and mounting holes are not orderable components. `excluded.csv`
records exclusions; no user-soldered component is required by the fitted variant.

## Traceability and coordinates

The exact MPN/LCSC identity comes from the generator specs and validated component
inventory, checked against each PCB's schematic-derived `LCSC` property. Some
imported `LCSC Part` fields contain stale generic-footprint values; those are
normalized only in release snapshots and recorded in `checks/export-validation.json`.

All Gerbers, drills and CPLs use the same drill/place origin. CPL X/Y values are
the native KiCad CSV coordinates in millimetres, with no bottom-side X mirror and
no second Y inversion. This follows JLCPCB's current KiCad 10 guide. The older
personal conversion skill negates Y again; this release uses its BOM converter
only, avoiding that coordinate mismatch.

- [JLCPCB KiCad BOM/CPL guide](https://jlcpcb.com/help/article/how-to-generate-the-bom-and-centroid-file-from-kicad)
- [JLCPCB Gerber/drill guide](https://jlcpcb.com/help/article/how-to-generate-gerber-and-drill-files-in-kicad-7)
- [ALPS RK10J catalog](https://tech.alpsalpine.com/cms.media/product_catalog_rv_03_rk10j_en_780020d1ea.pdf)
- [JLCPCB RV1 listing](https://jlcpcb.com/partdetail/C470643)

`manifest.json` records source hashes, component counts, origins, population
overrides and field corrections. `source/` retains the actual export input with
refilled zones; `raw/` retains netlists and original position exports. `checks/`
contains commands and validation results.

`manufacturing/jlcpcb-rotation-corrections.json` is the part-number-locked source
for future export rotation corrections; `rotation-corrections.json` in the release
retains a copy. Raw KiCad positions remain unchanged for traceability.

`gerber-top.png` and `gerber-bottom.png` are independently rendered from each
actual Gerber ZIP, not screenshots of the PCB editor. Verification uses
`gerbonara==1.6.3` and `resvg-py`; run
`python3 scripts/pcb/verify-jlcpcb.py manufacturing/jlcpcb/NEW-RELEASE`
in an environment with those packages installed.

To regenerate into a **new, empty** release directory:

```sh
python3 .claude/skills/component-spec-audit/scripts/validate.py
python3 scripts/pcb/export-jlcpcb.py manufacturing/jlcpcb/NEW-RELEASE
```

The script requires KiCad 10 and the personal
`jlcpcb-bom-generate-from-kicad/scripts/convert_to_jlcpcb.py` BOM converter
(`--converter` can supply its path). It never overwrites an existing board release.
