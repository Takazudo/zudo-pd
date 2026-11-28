# Supply observation, 2026-11-27 UTC (2026-11-28 JST)

Read-only public catalog lookups for the [PD20 order sheet](../../releases/pd20-sourcing-review-20261122/ORDER-SHEET.md)
and the [P15 owner handoff](../../p15-order-handoff.md), recorded under parent
[#228](https://github.com/Takazudo/zudo-pd/issues/228). Nothing here is a quote, cart, upload, reservation or order, and
stock is not reserved. Both release folders were read, never written. Repository revision: main
`3a55b4c551e111c0c2e73751cf2c2cce0603164d`. The [2026-11-22 observation](../pd20-order-day-20261122/README.md) is kept
unchanged with its own dates.

## Commands

- PD20, all 99 BOM codes of `pd20-sourcing-review-20261122`:
  `python3 manufacturing/verification/pd20-order-package-20261120/scripts/fetch-parts.py manufacturing/releases/pd20-sourcing-review-20261122 <this>/pd20 > <this>/pd20/parts-availability.json`,
  2026-11-27T20:25:32Z–20:26:30Z. `pd20/fetch.err` is the empty stderr. Raw rows: `pd20/jlc/`.
- PD20 flags at one pair: `python3 manufacturing/verification/pd20-order-closeout-20261121/scripts/stock-review.py <this>/pd20/parts-availability.json 1`
  → [`pd20/stock-review-1-pair.json`](pd20/stock-review-1-pair.json). One pair is a per-pair demand basis, not the order
  quantity, which the owner has not chosen.
- P15, all 14 BOM codes of `corner-support-review/board-p15`:
  `P15_EVIDENCE_DIR=<this>/p15 python3 manufacturing/verification/p15-order-refresh-20261120/scripts/fetch-parts.py`,
  2026-11-27T20:26:31Z–20:26:46Z (JLC and LCSC retail). The script names its output `parts-availability-2026-11-20.json`;
  it is stored as [`p15/parts-availability.json`](p15/parts-availability.json), and its stderr summary as
  `p15/fetch-summary.txt`. Its `raw_file` / `webData_extract_file` fields keep the script's `evidence/...` relative paths;
  the files are under `p15/jlc/` and `p15/lcsc/`.

Signed, short-lived image and datasheet query strings in the raw rows were replaced with `?<signed-query-redacted>`, so
`raw_sha256` describes the bytes as received, not the stored files. `MANIFEST.sha256` lists the stored files.

## PD20: all 99 codes found; three exact lines are not covered by JLC public stock

Every model string matches its BOM comment (C970687 adds its value text). Demand is per pair (one Board P r3 + one
B20). "Pairs covered" is ⌊(stock − `lossNumber`) / per-pair placements⌋, a screen only.

| LCSC | Part, placement | Per pair | JLC stock 2026-11-22 | JLC stock 2026-11-27 | `minPurchaseNum` | `leastPatchNumber` | `lossNumber` | Pairs covered | stock-review flag (1 pair) |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| C523793 | TI TVS2200DRVR, Board P D5 | 1 | 2 | **1** | 21 | 5 | 0 | 1 | stock below `minPurchaseNum` and `leastPatchNumber` |
| C861076 | YAGEO RT0603BRD0710K4L, B20 R66 | 1 | 11 | 11 | 1 | 20 | 6 | 5 | stock below `leastPatchNumber` |
| C861233 | YAGEO RT0603BRD07226KL, B20 RVU1 | 1 | 15 | **0** | 178 | 20 | 8 | 0 | **zero stock** |
| C179864 | TI INA301A3QDGKTQ1, B20 U11/U12 | 2 | 13 | **10** | 1 | 0 | 0 | 5 | none |

Every other line has JLC stock covering at least 13 pairs after `lossNumber` (the lowest: C1334133 ASPI-0630LR-100M-T15,
7 per pair, stock 92, 13 pairs), with no `minPurchaseNum` or `leastPatchNumber` above stock. The three fields are
separate, publicly undefined JLC observations; none of them alone sets the billed or usable quantity.

**Not checked in this observation:** LCSC retail, TI and other distributor stock for the PD20 lines (the PD20 fetcher
reads JLC only), JLC Global Sourcing / consignment / pre-order availability, and any account-specific private parts
library. These are NOT CHECKED, not zero. External or private stock is never added to JLC's public stock.

## P15: all 14 codes found and covered for two boards

Every JLC row matches its BOM comment and has stock above two boards plus `lossNumber`, with no `minPurchaseNum` or
`leastPatchNumber` above stock. The lowest JLC stocks are C2678061 STUSB4500QTR 5,528, C192739 BZT52C18-7-F 5,896 and
C74561 SMAJ16A 13,978. LCSC retail pages exposed all 14 codes.

## Package bytes re-checked at the same revision

- PD20: `python3 scripts/pcb/pd20-order/verify-upload-files.py` → UPLOAD FILE INTEGRITY PASS 6/6, pinned manifest
  `940e805f…` ([`pd20/verify-upload-files.txt`](pd20/verify-upload-files.txt)).
- P15: `python3 scripts/pcb/board-p15/verify-shared-reference.py --rev HEAD` → SOURCE IDENTITY MATCH, 7/7
  ([`p15/verify-shared-reference.txt`](p15/verify-shared-reference.txt)); `sha256sum -c SHA256SUMS` in
  `corner-support-review/` → 150 OK, 1 unreadable local-only STEP ([`p15/sha256sum-c.txt`](p15/sha256sum-c.txt)).

These are byte-integrity checks, not fresh native KiCad runs or a historical replay (NOT RUN).

## Boundary

A catalog row is not a supplier acceptance. Whether JLC accepts each line at the chosen quantity in Standard PCBA, and
what it bills, is known only from the owner's placement preview and quotation.
