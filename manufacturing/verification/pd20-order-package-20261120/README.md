# PD20 order package evidence, 2026-11-20 (cloud, pinned KiCad 10.0.6)

Supplier-side evidence for `manufacturing/releases/pd20-prototype-review/` and its
[order sheet](../../releases/pd20-prototype-review/ORDER-SHEET.md). Nothing here is a quote, cart, upload or order.

## The package was rebuilt from the 2026-11-20 B20 PCB and passes its verifier

The chain ran with the pinned image `kicad/kicad@sha256:18693567…` through the cloud wrappers in place of the
selected Mac:

1. `uv run --python 3.12 scripts/pcb/verify-step-datums.py`: 47 pairs PASS, written to
   `footprints/kicad/step-datum-verification.json`.
2. `scripts/pcb/board-b20/assembly-preview.py`: PASS, 13,275 cross-board pairs, no unintended intersection; the
   J5 / JOUT1 mating contact stays inside its contact columns. The populated stack STEP is local-only and listed in
   `manufacturing/local-only-assembly-previews.json`.
3. `scripts/pcb/export-jlcpcb.py --boards board-p board-b20-draft`, then `verify-jlcpcb.py --write`: PASS.
   Board P r3 has 44 fitted (22 top, 22 bottom, 27 lines); B20 has 294 fitted (268 top, 26 bottom, 88 lines).
   DRC has 0 errors and 0 unconnected items on both boards; B20 ERC has 0 errors.

The package was re-exported twice after its `ORDER-NOTES.md` source (`manufacturing/package-notes-b20.md`) was
corrected (stale counts, then an independent review's wording fixes). Only the last export is kept. Gerber ZIP bytes
differ between exports, so its `SHA256SUMS` is the binding record.

## Two catalog lines had zero JLC stock

`scripts/fetch-parts.py` read JLC's public component catalog for all 99 LCSC codes on both BOMs
(`parts-availability-2026-11-20.json`, raw responses in `evidence/jlc/`). Two codes had zero stock:

| LCSC | Part | Placements | Minimum purchase |
| --- | --- | --- | --- |
| C2861552 | INA301A3IDGKR | B20 U11, U12 | 4 |
| C861332 | RT0603BRD0733RL | B20 R35 | 200 |

They need a JLC parts pre-order (purchasing, an owner step) or a separately reviewed substitute before the assembly
order. Stock changes daily; re-read it on the order day.

## The two-pair catalog estimate is USD 527.34 before PCB fabrication and shipping

`scripts/estimate.py` (`catalog-estimate-2026-11-20.json`) applies the retained fee model in
`scripts/pcb/calculate-lineup-cost.py` (Standard PCBA, double side: setup 51.12, stencil 16.42, feeder loading 1.53 per
line, 0.0016 per SMT joint) to two of each board:

| Board | Parts (USD) | Assembly (USD) |
| --- | --- | --- |
| Board P r3 | 24.12 | 128.64 |
| B20 | 148.64 | 225.94 |

The parts figure buys at least each line's minimum tier, so it includes the zero-stock lines at catalog price. PCB
fabrication (four-layer B20, two-layer P), shipping, duties and any pre-order fee are not included. It is not a
supplier quote.

## The D2 retiming changed only four values on the PCB

`field-sync/field-sync.sh` replays the steps of `.github/workflows/b20-field-sync.yml` locally with the same pinned
image (`dec-b20-d2-firing-threshold-band`):

- `sync-fields.py` changed exactly RDG12 / RDG5 (10k 1 % C25804 → 4.02k 0.1 % C705781) and CDG12 / CDG5 (22 nF
  C1729 → 27 nF C0G C3882413), on their existing footprints (`field-sync/sync-fields.json`).
- `verify-field-sync.py`: fills and all non-field content are identical; PCB `7a8270f5…` → `bc16fc9b…`
  (`field-sync/field-sync-verification.json`). `finalize_refill.py` passes.
- DRC with refill and schematic parity on `bc16fc9b…`: 0 errors, 0 unconnected items, 0 parity findings, and only the
  four reviewed J6 / J7 / J10 / J11 `lib_footprint_mismatch` warnings (`field-sync/drc-summary.json`).
- The loop, current, thermal and power reports were re-derived; only their input hashes changed.
