# PD20 prototype order sheet: Board P r3 + B20

**This sheet prepares an order; it is not one.** Nothing has been uploaded, quoted, paid for or ordered. The owner
decides the quantity and places the order. Electrical acceptance of PD20 is NOT ESTABLISHED, and every bench test
(T1–T8) is NOT RUN. This file sits outside `SHA256SUMS`, so it can be corrected without touching the package. Everything
it names is locked there.

## Files to upload

Upload one board at a time. Each board is a separate JLC PCB + PCBA order line. Upload exactly these six files:

| Board | Upload | Path in this folder | SHA-256 |
| --- | --- | --- | --- |
| Board P r3 | Gerber/drill ZIP | `board-p/board-p-gerbers.zip` | `654c10110ba013b948c19f9b82664ed87505dc81559927eb517b5ba658eba7f2` |
| Board P r3 | BOM | `board-p/bom.csv` | `82a356e21d3ea5209257498a44f12864f293b3d99481f34a601d08e9d11afba9` |
| Board P r3 | CPL | `board-p/cpl.csv` | `65ea17213125c8f6060ce3a869a86d9e2eb4ba20c02efb09c5f77647640362bf` |
| B20 | Gerber/drill ZIP | `board-b20-draft/board-b20-draft-gerbers.zip` | `6748bfd214e12cf244424ea3d8e4ea4ef44953ccb5c898ddd9d3189374f8a181` |
| B20 | BOM | `board-b20-draft/bom.csv` | `eb4622bf36b95e51a6f18f24ecc91fe89df16dd6683e7a533c2f2cc3e9454778` |
| B20 | CPL | `board-b20-draft/cpl.csv` | `6e0c04ed35ef2a7ca17278d95be1b452c12d04aa2c755c966540b7d9636ca3a2` |

`excluded.csv` in each board folder is for review only and is not uploaded. It lists the bare-copper pads and DNP
parts that are intentionally absent from the BOM and CPL.

### Check the upload files: UPLOAD FILE INTEGRITY

From the repository root of any checkout, including a fresh clone:

```sh
python3 scripts/pcb/pd20-order/verify-upload-files.py
```

It reads only and requires the following:

- One well-formed, unique `SHA256SUMS` entry for `manifest.json` and for each of the six files above.
- `manifest.json` matching its entry and the pinned export manifest `f430a76a…`, checked first.
- The verified manifest's `artifact_hashes` agreeing with `SHA256SUMS` for all six files.
- The six files' actual bytes matching.

Success prints `UPLOAD FILE INTEGRITY: PASS (6/6 …)`. Any missing file, changed byte, duplicate or unsafe path, or
manifest/checksum disagreement fails with exit 1. The result was PASS on 2026-11-20 UTC at `e974d710`.

**Scope.** This proves only that the upload bytes are the ones the package locked, anchored to the 2026-11-20 export's
manifest hash. It is not a complete engineering
replay, native KiCad validation or electrical qualification.

Do not use `sha256sum -c SHA256SUMS` as the upload check. In a checkout it gives 158 of 159 OK. The 159th entry,
`mechanical/assembly/populated-stack.step` (SHA-256
`59b0e220e03d772599a5890c0ba7e92cb7c31ad20536e019644cd8d1df7cef77`, 367,630,999 bytes), is a local-only derivative
that is intentionally absent from Git (`manufacturing/local-only-assembly-previews.json`). That file is not uploaded.

### Complete historical replay: NOT RUN without the original inputs

The package was verified when it was exported. `verify-jlcpcb.py --write` passed, as recorded in
`independent-validation.json` and in [the package evidence](../../verification/pd20-order-package-20261120/README.md).
That PASS remains historical evidence. A new full replay runs the unmodified `scripts/pcb/verify-jlcpcb.py` on this
folder, and it can pass only when every one of these prerequisites holds:

1. **Every recorded source hash matches.** `manifest.json` locks 592 Board P and 731 B20 source files. Its `git_base`
   `914a9f6d…` is the export-time HEAD label, not the source identity. #307's final head `cc3f5904` carries this
   package, and the package files are unchanged from there to `e974d710`. Current `main` differs from the locks in
   `.claude/skills/component-pesd24vs1ub-c85382/routing.json` (both boards), which changed with the later
   identity-alias adoption. A replay therefore needs a tree whose files match the locks, not merely a commit label.
2. **The original populated-stack STEP is present at both locations.** These are
   `mechanical/assembly/populated-stack.step` in this folder and
   `boards/board-b20-draft/assembly-preview/populated-stack.step`, both with SHA-256 `59b0e220…`. A regenerated
   replacement does not qualify.
3. **The ignored source `boards/board-b20-draft/assembly-preview/board-p-stacked.step` is present.** Restore it
   only by copying the committed `mechanical/assembly/board-p-stacked.step` from this folder, and only after
   confirming that the copy's SHA-256 is
   `221a63e10c104b499c6ee7d8246b59789219acef12520a2ee90dc142ec0e160d`. That value is the one both the B20 source lock
   and `SHA256SUMS` record.

If any prerequisite is missing, report the full replay as **NOT RUN**. Do not refresh locks with `--write`, do not
add a skip, and do not regenerate the package to edit instructions.

## Board settings

| Setting | Board P r3 | B20 |
| --- | --- | --- |
| Size | 27 × 40 mm | 110 × 85 mm |
| Layers | 2 | 4 (F.Cu, In1.Cu, In2.Cu, B.Cu) |
| Thickness | 1.6 mm | 1.6 mm |
| Copper (from the job file) | 1 oz outer | 1 oz outer, 0.5 oz inner |
| Assembly | Standard PCBA, **both sides** (22 top, 22 bottom) | Standard PCBA, **both sides** (268 top, 26 bottom) |
| Fitted parts / BOM lines | 44 / 27 | 294 / 88 |
| Through-hole parts | Yes; hand-soldered by JLC | Yes; hand-soldered by JLC |

Any other fabrication option (finish, colour, via handling) is the owner's choice in the order form. The design does
not ask for filled or capped vias. If the review flags via-in-pad on the SON / PowerDI lands, accept JLC's standard
handling or ask before paying, and record the answer.

## Checks to make in JLC's placement preview

The CPL uses native KiCad rotations with one drill/place origin. Do not negate Y. **`cpl.csv` has no pad or pin
data**: it holds only the designator, centre, side and rotation. Body models alone do not establish pin 1 or
cathode orientation either. Take pin 1 and the cathode from these sources:

- **Pad 1 and its net:** the checksum-locked package PCBs `board-p/source/board-p.kicad_pcb` and
  `board-b20-draft/source/board-b20-draft.kicad_pcb`. They are listed per part, with pad-1 centres in the CPL frame, in
  [the polarity reference](../../verification/pd20-order-closeout-20261121/README.md#polarity-evidence-comes-from-the-package-pcbs-not-from-cplcsv),
  which `python3 scripts/pcb/pd20-order/polarity-reference.py` regenerates.
- **What pad 1 is:** the exact part's owner pin map under `.claude/skills/component-*/`, routed through
  `references/inventory.json`. For example, the BZT52 owners record K = pin 1 (band end) on these SOD-123 lands.

Compare the preview's marking with those sources for each of these:

- **B20 top:** D1–D3 (D3 B560C-13-F, SMC: its cathode is pad 1 on `C_SW`), DZ1–DZ3, U1–U3 and U10 (HSOP-8 /
  SOIC-8), the VSSOP-8 amplifiers, Q1–Q6 (VSON-8), every SOT-23 FET, and the electrolytics C1 (RVT1H101M0810)
  and CAF1 / CBF1 / CCF1 / CSO3 (25SVPF47M; on −12 V, CCF1's positive pin 1 goes to GND).
- **B20 bottom (new with D2):** D4 BZT52C11 and D5 BZT52C3V9 (SOD-123), Q51 / Q52 / Q55 CSD18543Q3A (VSON-8),
  Q8 DMP3036SFG-7 (PowerDI3333-8) and Q7 / Q9 / Q13 BSS138 (SOT-23). **The bottom preview is mirrored.** Read
  the bottom-side positions and marks as mirrored, not as a top view.
- **Board P r3, both sides:** top D5 TVS2200DRVR (WSON-6), D9 / D11 BZT52C18 and D10 BZT52C20 (SOD-123), U1
  STUSB4500QTR, U2 TPS16630PWPR, U3 LM74700, Q1 DMP3036SFG-7, Q3 CSD18543Q3A, Q5 / Q6 BSS138, the electrolytic
  C3 (RVT1H101M0810), J1 and JOUT1.
  Bottom: D8 / D13 BZT52C11 and D12 BZT52C18, in the mirrored bottom preview.
- **Stencil and paste:** confirm both sides get a stencil. The shared Q1 / Q3 land and paste on Board P keep the
  `dec-pd20-land-paste-prototype` disposition; note any DFM warning there.

**Clarification for the frozen `ORDER-NOTES.md`.** That file is locked in `SHA256SUMS`, and so is its source,
`manufacturing/package-notes-b20.md`, so neither is edited. It says to check polarized parts "against pad 1 of
`cpl.csv`". Read that instruction as the procedure above: pad 1 from the package PCB, its meaning from the owner pin
map. Its part list and its mirrored-bottom warning still apply. Its Board P polarized parts are the ones listed in
this sheet.

## Stock to resolve first

Two B20 lines had zero JLC stock on 2026-11-20 at 12:14–12:15 UTC, and a re-read at 18:16–18:18 UTC found the same.
The re-read is in
[`pd20-order-closeout-20261121/`](../../verification/pd20-order-closeout-20261121/README.md#jlc-stock-re-read-2026-11-20-181623181830-utc-unchanged-with-six-lines-to-resolve).
Four more exact lines have stock below the two-pair need plus attrition, or below JLC's minimum-purchase or
least-patch fields. Both snapshots show them identically; "every other line in stock" meant only stock > 0.

| LCSC | Part | Placements | Stock | Flag |
| --- | --- | --- | ---: | --- |
| C2861552 | INA301A3IDGKR | B20 U11, U12 | 0 | Zero stock; minimum purchase 4 |
| C861332 | RT0603BRD0733RL | B20 R35 | 0 | Zero stock; minimum purchase 200 |
| C705764 | RT0603BRD0730K1L | B20 RVX1 | 2 | Below 2 pairs + attrition (10); minimum purchase 255 |
| C523793 | TVS2200DRVR | Board P D5 | 2 | Below minimum purchase 21 and least-patch 5 |
| C861371 | RT0603BRD073K09L | B20 R22, R31 | 195 | Below minimum purchase 389 |
| C861076 | RT0603BRD0710K4L | B20 R66 | 11 | Below least-patch 20 |

JLC does not document what the attrition and least-patch fields mean, and these flags are not supplier-confirmed
shortages. Procure the existing exact parts first, for example through a JLC parts pre-order or through JLC's
matching in the quote. Do not substitute a part only to clear a stock warning. A substitute is a separately reviewed
component, design and package change. Re-read stock on the order day.

## Quantity: undecided; estimate for two pairs

The prototype quantity is the owner's decision. The labelled estimate below is for **two** Board P r3 and **two** B20
assembled, from the retained JLC fee model and the 2026-11-20 catalog rows:

| Board | Parts (USD) | Assembly (USD) |
| --- | --- | --- |
| Board P r3 × 2 | 24.12 | 128.64 |
| B20 × 2 | 148.64 | 225.94 |
| **Total** | **172.76** | **354.58** |

The total is USD 527.34, **before** PCB fabrication (a four-layer and a two-layer board), shipping, duties and any
parts pre-order fee. It is a catalog estimate, not a quote. Two assembled sets is the PCBA minimum (owner rule
2026-11-03). The bare-PCB quantity is set in the quote and was not re-read on 2026-11-20. No current supplier quote
exists.

## Owner steps before ordering

1. Decide the PD20 assembled quantity.
2. Resolve exact-part supply for the six lines above (pre-order or supplier matching), without substitution.
3. Run the upload-file integrity check above, then upload both boards.
4. Set Standard PCBA, **both sides**, on both boards.
5. Make the placement-preview checks: polarized parts against the package PCB pad 1 and the owner pin maps,
   bottom-side rotations in the mirrored view, and via and stencil handling.
6. Obtain the supplier quote, review it, and record it with its date, kept separate from the estimate above.
7. Record order status only after a real order is placed.

## After arrival (all NOT RUN)

Incoming inspection, then the PD20 bench plan T1–T8
(`doc/src/content/docs/verification/pd20-verification.md`). The 20 V NVM image is provisioned only after a reviewed,
program-ready image and its procedure exist (T4). No such binary exists yet.

The readiness ledger (`manufacturing/prototype-order-readiness.md`) lists the residuals each disposition carries
into those tests.
