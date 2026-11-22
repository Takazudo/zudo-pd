# Order-day procurement evidence, 2026-11-22 (#329)

Desk evidence for the [PD20 order sheet](../../releases/pd20-sourcing-review-20261122/ORDER-SHEET.md) and the
[P15 owner handoff](../../p15-order-handoff.md). Nothing here is a quote, cart, upload, reservation or order. Both
release folders are read, never written. Repository revision: `edfd69056cd192139930d018d8bc8f4fd2489255`.

## Upload files still match their packages

| Check | Command | Result (2026-11-22 UTC) |
| --- | --- | --- |
| PD20 upload integrity | `python3 scripts/pcb/pd20-order/verify-upload-files.py` | PASS 6/6, pinned manifest `940e805f…` |
| PD20 refusal tests | `python3 -m unittest discover -s scripts/pcb/pd20-order -p test_verify_upload_files.py` | 17 tests OK |
| P15 source identity | `python3 scripts/pcb/board-p15/verify-shared-reference.py --rev HEAD` (full clone) | 7/7 MATCH, ancestry OK: [`p15/verify-shared-reference.txt`](p15/verify-shared-reference.txt) |
| P15 package checksums | `sha256sum -c SHA256SUMS` in `corner-support-review/` | 150 OK, 0 mismatch, 1 unreadable local-only STEP: [`p15/sha256sum-c.txt`](p15/sha256sum-c.txt) |
| P15 non-replay subset | `uv run --no-project --with gerbonara python3 manufacturing/verification/p15-order-refresh-20261120/scripts/verify-p15-subset.py` | PASS, all 13 checks: [`p15/verify-p15-subset.json`](p15/verify-p15-subset.json) |

Full historical replay of either package is NOT RUN: it needs the original local-only STEP and matching source locks.

## Catalog re-read: 99 PD20 codes and 14 P15 codes, all found

- PD20: `fetch-parts.py RELEASE EVIDENCE` from `../pd20-order-package-20261120/scripts/`, pointed at
  `pd20-sourcing-review-20261122`, 2026-11-22T06:11:44Z–06:13:05Z: [`parts-availability.json`](parts-availability.json),
  raw rows in `evidence/jlc/`.
- `stock-review.py` from `../pd20-order-closeout-20261121/scripts/`, for one pair
  ([`stock-review-1-pair.json`](stock-review-1-pair.json)) and a **provisional** two-pair comparison
  ([`stock-review-2-pairs-provisional.json`](stock-review-2-pairs-provisional.json)). Two pairs is not the order
  quantity; the owner has not chosen one.
- P15: `P15_EVIDENCE_DIR=<scratch> python3 ../p15-order-refresh-20261120/scripts/fetch-parts.py`, 06:13:47Z–06:14:01Z.
  The script names its output `parts-availability-2026-11-20.json`; it is stored here as
  [`p15/parts-availability.json`](p15/parts-availability.json), and its `raw_file` paths resolve under `p15/`.
  Every P15 line has JLC stock above two boards plus `lossNumber`, and no field above stock.

Signed, short-lived image and datasheet query strings in the raw rows were replaced with `?<signed-query-redacted>`.
The `raw_sha256` values therefore describe the bytes as received, not the stored files.

## Four PD20 lines need an owner supply decision

Per-pair demand (one Board P r3 + one B20). JLC stock is the public catalog pool, not reserved.

| LCSC | Part | Per pair | JLC stock | `minPurchaseNum` | `leastPatchNumber` | `lossNumber` | Pairs covered by stock − loss | LCSC retail stock |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| C523793 | TVS2200DRVR, Board P D5 | 1 | 2 | 21 | 5 | 0 | 2 | 0 |
| C861076 | RT0603BRD0710K4L, B20 R66 | 1 | 11 | 1 | 20 | 6 | 5 | 0 |
| C861233 | RT0603BRD07226KL, B20 RVU1 | 1 | 15 | **178** | 20 | 8 | 7 | 0 |
| C179864 | INA301A3QDGKTQ1, B20 U11/U12 | 2 | 13 | 1 | 0 | 0 | 6 | 13 |

C861233 is new: on 2026-11-20 and 2026-11-21 it read stock 55 and `minPurchaseNum` 1. Its row also carries
`preMinPurchaseNum` 178 and `canPresaleNumber` −7. For C523793, C861076 and C861233 a field exceeds stock, so JLC may
refuse or extend the line at quote time. None of these fields alone sets the billed or usable quantity.

## Fulfillment routes are documented, not confirmed

[`external-routes.json`](external-routes.json) records the JLC help pages, LCSC retail rows and TI store reads.

- JLC documents three routes into a private parts library: Global Sourcing, consignment and parts pre-order. None of
  the pages states a numeric minimum, cut-tape or leader requirement, or Standard PCBA applicability. The JLC field
  meanings are undocumented.
- TI's inventory endpoint returned 113,626 TVS2200DRVR and 77,578 INA301A3QDGKTQ1 at 06:14:55Z, but the TVS2200DRVR
  page data said "OutOfStock". TI stock is UNCONFIRMED.
- LCSC retail has 0 of C523793, C861076 and C861233 (packing minimum 20 for the resistors).
- Mouser, DigiKey, Arrow, Farnell, RS and Octopart gave no fresh numbers. The Mouser 8,215-unit R66 read from
  2026-11-21 is not current.

No substitution is proposed. Each route keeps the exact MPN.
