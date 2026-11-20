# LED P15 r1 prototype-order handoff

Reviewed 2026-11-09 at lamp main `5726c8e6e89b5a03ba149c234cccda2f9afab6c8`.
Order **two assembled P15 r1 modules**, reuse both existing Board Ls, and order **zero new Board Ls and zero Board Bs**.
P15 remains 27 × 40 mm with the adopted 15 V / 3 A NVM image; keep Board L RS1 = 200 mΩ and `CTRL_FULL_CCR` = 2407.

The manufacturing owner is zudo-pd. Its [order-day handoff](https://github.com/Takazudo/zudo-pd/blob/44fd3ba810aad627fd461b90093a3482707b44da/manufacturing/p15-order-handoff.md)
and [decision packet](https://github.com/Takazudo/zudo-pd/blob/44fd3ba810aad627fd461b90093a3482707b44da/manufacturing/p15-order-decision-packet.md) are pinned to inspected commit
`44fd3ba810aad627fd461b90093a3482707b44da`, on zudo-pd main. External [PR #234](https://github.com/Takazudo/zudo-pd/pull/234)
is merged; these documents are no longer pending that integration. This does not advance our
[consumer source pin](../boards/p15-r1-reference.json). No owner fabrication files are copied here.

## Exact P15 order inputs

Use only `board-p15/` in the owner’s fixed `manufacturing/releases/corner-support-review/` package.
Its manifest base is `3b9821b48cf4c77e8512ce653cada3db962d2c88`; the document revision above and
this frozen manufacturing base have different roles. Neither repository’s `boards/board-p/` is P15.

| File at the inspected owner revision | Role | Observed SHA-256 |
| --- | --- | --- |
| [board-p15-gerbers.zip](https://github.com/Takazudo/zudo-pd/blob/44fd3ba810aad627fd461b90093a3482707b44da/manufacturing/releases/corner-support-review/board-p15/board-p15-gerbers.zip) | PCB upload | `e68a133e2a3fa610758ed0e183fb9c4e77e4a4bfff7a9a6bac5cd1ab7f8c14ae` |
| [bom.csv](https://github.com/Takazudo/zudo-pd/blob/44fd3ba810aad627fd461b90093a3482707b44da/manufacturing/releases/corner-support-review/board-p15/bom.csv) | Assembly selection upload | `23d6e2902307ce3920c405abe3296600610bcd5b54f0cca67ee0a8291ecfd59f` |
| [cpl.csv](https://github.com/Takazudo/zudo-pd/blob/44fd3ba810aad627fd461b90093a3482707b44da/manufacturing/releases/corner-support-review/board-p15/cpl.csv) | Placement upload | `a9116d1b9f1d7f092531173a7c8f4d49f4a4c282b9a88f449a89b0da3e030ce6` |
| [excluded.csv](https://github.com/Takazudo/zudo-pd/blob/44fd3ba810aad627fd461b90093a3482707b44da/manufacturing/releases/corner-support-review/board-p15/excluded.csv) | Supporting exclusions; do not upload | `16d6146bd3ca6f3fbca8adbc4ddcddb176659dcd5d016a27a699b41467e9f616` |

The four Git blobs were independently hashed on 2026-11-09 and matched the supplied frozen hashes.
Recheck the downloaded bytes before any upload; a missing file or mismatch blocks order-file acceptance.
Do not repair the frozen package, refresh its locks or regenerate outputs.

```sh
# From the lamp checkout, with an explicit read-only owner checkout:
python3 scripts/checks/verify-p15-reference.py --pd-repo /workspace/zudo-pd-readonly --pd-rev 8af9e5569c2534c03ce132515d1ec11f4c3f83d3
# Independently hash each frozen order input directly from the inspected Git revision:
for file in board-p15-gerbers.zip bom.csv cpl.csv excluded.csv; do
  git -C /workspace/zudo-pd-readonly show 44fd3ba810aad627fd461b90093a3482707b44da:manufacturing/releases/corner-support-review/board-p15/"$file" | sha256sum
done
```

## Owner checkout checks remain open

Before ordering, inspect the supplier placement preview against the owner’s
[exact placement maps](https://github.com/Takazudo/zudo-pd/blob/44fd3ba810aad627fd461b90093a3482707b44da/manufacturing/readiness/p15-first-placement-orientation.json):

- D5, Littelfuse SMAJ16A / C74561: cathode stripe on pad 1, VBUS_IN, smaller X.
- D9, Diodes BZT52C18-7-F / C192739: cathode band on pad 1, VDD_LOC, smaller X.
- Check every other polarized placement and IC/connector pin 1 against the owner package and exact pin maps.
  Local geometry and CPL agreement do not prove the supplier’s library placement. Stop on a reversal;
  the owner handoff describes correcting supplier-preview rotation without editing the frozen files.

These are owner preview criteria, not new primary-source clearance. D5’s `fact-c74561-polarity`
(`src-c74561-primary`, manufacturer-authored mirror, package/pad drawing) remains **UNSOURCED**
under the owner’s evidence contract because the primary binary is unavailable. D9’s
`fact-c192739-polarity` (`src-c192739-primary`, DS18004 Rev. 38-2 page 1 polarity row) is
primary-source confirmed; neither establishes assembled orientation.

Recheck exact BOM stock, assembly-service eligibility (including through-hole parts), quantity and
complete cost on the order day: PCB, parts, assembly, shipping and tax/duty. The owner’s dated
2026-11-03 and 2026-11-09 catalog snapshots establish observations only for their recorded dates.
Historical assembly estimates are not current quotes. Current checkout availability and total cost are **UNKNOWN**.
Record the preview approval, quote details and eventual order identity separately.

## Evidence and later gates

| Stage | Observed state | Remaining action |
| --- | --- | --- |
| Consumer source identity | MATCH at owner record `8af9e5569c2534c03ce132515d1ec11f4c3f83d3`; adoption commit `4a0741fabf8d2332848a3740708aab26b8504133` exists | Byte identity only; consumer pin unchanged |
| Four order-file identities | MATCH at owner commit `44fd3ba810aad627fd461b90093a3482707b44da` | Recheck downloaded files before upload |
| Full historical 151-file replay | NOT RUN: original local-only STEP absent | Requires matching frozen source tree and original `populated-stack.step`, 158,591,651 bytes, SHA-256 `b2d5d8da200c4f4e989e33d4190912054475fb17d601f2f76c0b347ab3508167`; never regenerate a substitute |
| Supplier preview / stock / eligibility / total cost | NOT RUN / UNKNOWN | Owner checkout checks above |
| P15 order / receipt | NOT ORDERED / NOT RECEIVED | Owner actions; no supplier interaction performed here |
| Programming / measurement | NOT RUN / NOT RUN | Equipped owner bench, after arrival |

Follow the owner’s [arrival and P15-NVM-1–7 procedure](https://github.com/Takazudo/zudo-pd/blob/44fd3ba810aad627fd461b90093a3482707b44da/doc/src/content/docs/architecture/board-p15-programming.md)
for each unit before any Board L connection, then the lamp’s
[before-programming checklist](../firmware/board-l/BEFORE-PROGRAMMING-CHECKLIST.md) and
[bench sheets](../firmware/board-l/BENCH-TEST-SHEETS.md).
[Current state](../doc/src/content/docs/architecture/current-state.mdx) retains the later sequence and open decisions.
Physical fit, programming, energization and measurements remain unperformed on this path.
Issues #34, #35 and #52 remain open; matching mirrors do not recover manufacturer-primary provenance.
P15 R2.3/R2.4/R2.6 remain FAIL and R2.5 UNKNOWN. Prototype residual acceptance is not qualification.

## Historical 2026-09-19 JLCPCB order files

The remainder of this page describes the historical LED Board P, Board L and SWD-adapter release.
It is not the new P15 order package or a request to reorder those boards.


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
