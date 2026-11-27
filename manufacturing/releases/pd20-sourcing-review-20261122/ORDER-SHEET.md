# PD20 prototype order sheet: Board P r3 + B20 (sourcing review, 2026-11-22)

**This sheet prepares an order; it is not one.** Nothing has been uploaded, quoted, paid for or ordered. The owner
decides the quantity and places the order. Electrical acceptance of PD20 is NOT ESTABLISHED, and every bench test
(T1–T8) is NOT RUN. This file sits outside `SHA256SUMS`, so it can be corrected without touching the package. Everything
it names is locked there.

This package supersedes `../pd20-prototype-review/` for ordering. It carries the 12 substitutions adopted under the
[sourcing policy](../../../doc/src/content/docs/decisions/sourcing.mdx) after the
[2026-11-22 audit](../../../doc/src/content/docs/research/parts-sourcing-audit-20261122.mdx) (#326): 7 placements on
Board P r3 and 25 on B20. Placements, rotations and copper are unchanged: both `cpl.csv` files are byte-identical to the
earlier package. The earlier package is kept unchanged as history.

## Files to upload

Upload one board at a time. Each board is a separate JLC PCB + PCBA order line. Upload exactly these six files:

| Board | Upload | Path in this folder | SHA-256 |
| --- | --- | --- | --- |
| Board P r3 | Gerber/drill ZIP | `board-p/board-p-gerbers.zip` | `fdc169a4855321f7cb8c768cd0489a1da46d30f11fef28ea4594a4b1ee52148f` |
| Board P r3 | BOM | `board-p/bom.csv` | `5a2b0fc01f7e26fc06d1f9fcbb7aa7cf8f27b3a8f6f11e90574d7dde7b53dcb8` |
| Board P r3 | CPL | `board-p/cpl.csv` | `65ea17213125c8f6060ce3a869a86d9e2eb4ba20c02efb09c5f77647640362bf` |
| B20 | Gerber/drill ZIP | `board-b20-draft/board-b20-draft-gerbers.zip` | `cd75b83d175f6e6eb299a60786d99f2e58abc56a08c4b82f72250a3e1a443120` |
| B20 | BOM | `board-b20-draft/bom.csv` | `52b553966e5566bdb39f999329fc45c19b5a8d41af04ca5a8c7307676d41481e` |
| B20 | CPL | `board-b20-draft/cpl.csv` | `6e0c04ed35ef2a7ca17278d95be1b452c12d04aa2c755c966540b7d9636ca3a2` |

`excluded.csv` in each board folder is for review only and is not uploaded. It lists the bare-copper pads and DNP
parts that are intentionally absent from the BOM and CPL.

### Check the upload files: UPLOAD FILE INTEGRITY

From the repository root:

```sh
python3 scripts/pcb/pd20-order/verify-upload-files.py
```

The default release is this folder, pinned to its exported manifest `940e805f…`. Success prints
`UPLOAD FILE INTEGRITY: PASS (6/6 …)`. It proves only that the upload bytes are the ones this package locked. It is not
an engineering replay, native KiCad validation or electrical qualification.

Do not use `sha256sum -c SHA256SUMS` as the upload check. In a checkout one of its 161 entries,
`mechanical/assembly/populated-stack.step` (SHA-256 `f90177a1d19d93468faba81b36748e739391efff0529aef317c5114f9c6e24f9`,
367,630,999 bytes), is a local-only derivative intentionally absent from Git
(`manufacturing/local-only-assembly-previews.json`). It is not uploaded.

The package was verified at export: `verify-jlcpcb.py --write` passed (`independent-validation.json`). The export and
native evidence are in [the package evidence](../../verification/pd20-sourcing-review-20261122/README.md). A later full
replay needs a tree matching every recorded source hash and the original local-only STEP; otherwise report it as
NOT RUN.

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

Any other fabrication option is the owner's choice in the order form. The design does not ask for filled or capped
vias. If the review flags via-in-pad on the SON / PowerDI lands, accept JLC's standard handling or ask before paying,
and record the answer.

## Checks to make in JLC's placement preview

`cpl.csv` has no pad or pin data. Take pad 1 and its net from the package PCBs (`board-p/source/board-p.kicad_pcb`,
`board-b20-draft/source/board-b20-draft.kicad_pcb`); `python3 scripts/pcb/pd20-order/polarity-reference.py` lists them
for this package. Take the meaning of pad 1 from the exact part's owner pin map. The JSCJ BZT52C11 / BZT52C18 owner
(`.claude/skills/component-jscj-bzt52-zeners/`) records the cathode as pad 1 on the SOD-123 land.

- **B20 top:** D1–D3 (D3 B560C-13-F, SMC: its cathode is pad 1 on `C_SW`), DZ1–DZ3 (JSCJ BZT52C11), U1–U3 and U10, the
  VSSOP-8 amplifiers including U11 / U12 INA301A3QDGKTQ1, Q1–Q6 (VSON-8), every SOT-23 FET, and the electrolytics C1
  and CAF1 / CBF1 / CCF1 / CSO3 (on −12 V, CCF1's positive pin 1 goes to GND).
- **B20 bottom:** D4 JSCJ BZT52C11 and D5 BZT52C3V9 (SOD-123), Q51 / Q52 / Q55 (VSON-8), Q8 (PowerDI3333-8) and
  Q7 / Q9 / Q13 (SOT-23). **The bottom preview is mirrored.**
- **Board P r3:** top D5 TVS2200DRVR (WSON-6), D9 / D11 JSCJ BZT52C18 and D10 BZT52C20, U1 STUSB4500QTR, U2
  TPS16630PWPR, U3 LM74700, Q1, Q3, Q5 / Q6, C3, J1 and JOUT1. Bottom: D8 / D13 JSCJ BZT52C11 and D12 JSCJ BZT52C18,
  in the mirrored bottom preview.
- **Stencil and paste:** confirm both sides get a stencil. The shared Q1 / Q3 land and paste on Board P keep the
  `dec-pd20-land-paste-prototype` disposition.

## Supply to confirm first

Re-read 2026-11-22 06:11:44–06:13:05 UTC (15:11–15:13 JST) for all 99 codes; stock is not reserved. Evidence and the
route research are in [the order-day evidence](../../verification/pd20-order-day-20261122/README.md) (#329). Re-read
every line on the order day. Demand is per pair (one Board P r3 + one B20); the quantity is undecided.

| LCSC | Part | Placements (per pair) | JLC stock | `minPurchaseNum` | `leastPatchNumber` | `lossNumber` | Action |
| --- | --- | --- | ---: | ---: | ---: | ---: | --- |
| C523793 | TVS2200DRVR | Board P D5 (1) | 2 | 21 | 5 | 0 | Two fields exceed stock. Confirm JLC accepts the line at the real quantity, or bring in the exact TI part (below). No same-name substitute |
| C861076 | RT0603BRD0710K4L | B20 R66 (1) | 11 | 1 | 20 | 6 | `leastPatchNumber` exceeds stock. Confirm Standard PCBA use, or bring in the exact part. Do not change the value |
| C861233 | RT0603BRD07226KL | B20 RVU1 (1) | 15 | **178** | 20 | 8 | **New on 2026-11-22**: the 2026-11-20 UTC reads showed stock 55 and `minPurchaseNum` 1. Two fields exceed stock. Confirm or bring in the exact part |
| C179864 | INA301A3QDGKTQ1 (adopted) | B20 U11, U12 (2) | 13 | 1 | 0 | 0 | Stock covers 6 pairs; nothing reserved. Re-check at the chosen quantity |

**Re-read 2026-11-27 UTC (2026-11-28 JST)**, 20:25:32–20:26:30 UTC, all 99 codes found
([evidence](../../verification/supply-observation-20261127/README.md)). The table above keeps its 2026-11-22 values.

| LCSC | Placements (per pair) | JLC stock | `minPurchaseNum` | `leastPatchNumber` | `lossNumber` | Pairs covered by stock − loss |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| C523793 | Board P D5 (1) | **1** | 21 | 5 | 0 | 1 |
| C861076 | B20 R66 (1) | 11 | 1 | 20 | 6 | 5 |
| C861233 | B20 RVU1 (1) | **0** | 178 | 20 | 8 | 0 |
| C179864 | B20 U11, U12 (2) | 10 | 1 | 0 | 0 | 5 |

On that date RVU1 has no JLC public stock and D5 is below two of its own fields, so neither exact line is covered from
JLC's public pool even for one pair. Every other line covered at least 13 pairs after `lossNumber`, with no field above
stock. LCSC retail, TI and other distributors and JLC private-library routes were NOT CHECKED in this re-read.

On 2026-11-22, every other line had stock above two pairs plus `lossNumber`, with no field above stock. The earlier R35, RVX1 and
R22 / R31 flags stay resolved by the adopted parts. `minPurchaseNum`,
`leastPatchNumber` and `lossNumber` are separate observations that JLC does not publicly define; none of them alone
sets the billed or usable quantity.

**Routes for the exact parts (documented, not confirmed for this order).** JLC's help pages describe Global Sourcing,
consignment and parts pre-order, each into the account's private parts library. They give no numeric minimum,
cut-tape or leader rule and do not state Standard PCBA applicability, so confirm all of that in the order flow. LCSC
retail showed 0 of C523793, C861076 and C861233. TI's store inventory endpoint returned 113,626 TVS2200DRVR while its
product page said out of stock, so TI supply is unconfirmed. No other distributor gave a current number. Never add
external or private stock to JLC's public stock. If no route gives the exact part, the fallback is an engineering
change, which needs its own evidence and is outside this package.

## Quantity: undecided

The prototype quantity is the owner's decision. No new total is computed for this package. Against the earlier
labelled two-pair catalog estimate (USD 527.34, `../pd20-prototype-review/ORDER-SHEET.md`), the mounted-part comparison
of the 12 substitutions is +USD 1.6274 for two pairs (INA301 +3.5928, the other eleven −1.9654). That is a comparison
metric, not a purchase cost: it excludes minimums, loss, setup, PCB, assembly, shipping and tax, and is not added to the
earlier estimate. Standard PCBA setup is $1.53 per unique SMT part for Basic and Extended alike (JLC price list,
2026-11-22 JST); recheck at quote time. No supplier quote exists.

## Owner steps before ordering

1. Decide the PD20 assembled quantity.
2. Confirm exact-part supply for the four lines above at that quantity, from a new same-day observation.
3. Run the upload-file integrity check, then upload both boards.
4. Set Standard PCBA, **both sides**, on both boards.
5. Make the placement-preview checks above, including bottom-side rotations in the mirrored view and via and stencil
   handling.
6. Obtain the supplier quote, review it, and record it with its date.
7. Record order status only after a real order is placed.

## After arrival (all NOT RUN)

Incoming inspection, then the PD20 bench plan T1–T8 (`doc/src/content/docs/verification/pd20-verification.md`). The
20 V NVM image is provisioned only after a reviewed, program-ready image and its procedure exist (T4). No such binary
exists yet. The readiness ledger (`manufacturing/prototype-order-readiness.md`) lists the residuals each disposition
carries into those tests.
