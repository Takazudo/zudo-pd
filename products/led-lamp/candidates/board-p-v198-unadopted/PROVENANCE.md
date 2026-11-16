# V198 shared Board P candidate — field-sync successor of V196 (UNADOPTED)

**Status:** isolated, unadopted engineering candidate and unvalidated draft. V198 is V196
with **property fields only** changed. Copper, geometry, nets, footprints, libraries and
project are unchanged. Not order-ready. No fabrication or assembly output exists.

## Identity

| File | V196 SHA256 | V198 SHA256 |
| --- | --- | --- |
| `board-p-COUT1206-TRIAL.kicad_pcb` | `c191997b3b34856076bc89df435684de5cd15f7636d6e2a216cc7652f4c02ad2` | `762ff264a2f4717ae792af008e510eb8af37cee15887f187af1fc3d00466a8b2` |
| `board-p-COUT1206-TRIAL.kicad_sch` | `16375e410046f8c11b5e40fa0c74647fcd4dde9e44632d123236b3ad620aee25` | `373bb8d3880f7e1b28cd6b40414ccf7126c2ee7afb62e8d4d595d52f7bdb167b` |
| `BOM-TRIAL.csv` | `57e58a4c…` | `e9b19387d21cc0c39c7bd65bbadfb0bfa9f2cc4bb16263118f83f77157561b45` |
| `.kicad_pro`, `fp-lib-table`, `sym-lib-table`, `libraries/` | unchanged | unchanged (byte-identical) |

The basename is kept for library lookup behaviour. Parent: V196 in
`../board-p-v196-unadopted/` (source commit `ef0178d0`, local provenance only).

## What changed (reproducible)

`tools/sync_fields.py` applied to the V196 PCB and schematic. Re-running it on a fresh V196
copy gives the same hashes and the same `tools/SYNC-LOG.tsv` (49 field changes).
`tools/check_field_only.py` strips every `(property …)` element and confirms that the
remaining bytes of both the PCB and the schematic equal V196 exactly.

1. **PCB footprint fields synced from the schematic.**
   - Added an `LCSC` property to the 24 footprints whose symbols have one.
   - Overwrote the stale `LCSC Part` values. That is 13 R0603 footprints that said
     C25803, and CMON, which said C15849 (now C14663).
   - Added `LCSC Part` where it was missing.
   - Added COUT `Manufacturer`.
2. **J1 exact orderable bound: `USB4105-GF-A`, Global Connector Technology, LCSC `C3020560`.**
   This was added to the schematic J1 symbol (MPN, Manufacturer, LCSC), the PCB footprint
   and `BOM-TRIAL.csv`. Value text and footprint are unchanged.
   - Manufacturer evidence: GCT drawing USB4105 Rev B4 (drawing date 18/12/23),
     https://gct.co/files/drawings/usb4105.pdf, retrieved 2026-10-31, SHA256
     `fb331fbabee8392ed2937ed757c1610cb0f174b84625147c0b580a18eea8c0e5`.
     Its ordering grid is `USB4105-XX-A-XXX`: contact plating GF = gold flash
     (standard) / 15 / 30; A = tape & reel; stake blank = 0.95 mm. So `USB4105-GF-A`
     = gold flash, T&R, 0.95 mm stake.
   - Plating is an ordering-grid option on the **same** mechanical drawing. This closes
     the earlier GF-vs-15 identity question for the land pattern. The retained STEP
     remains the 15-A variant, so it is 3D evidence only.
   - Distributor binding: https://jlcpcb.com/partdetail/C3020560 (retrieved 2026-10-31,
     HTML SHA256 `aefcabe2b545e2577b8d9ffb875121d9fc349bc7f60c225601e8845263a4ef69`)
     lists `USB4105-GF-A`, brand Global Connector Technology. Snapshot values: overseas
     stock 2998, pre-order minimum 7. Observation only, not a quote.
   - Assembly route (SMT + shell THT) and JLC assembly eligibility are **not** confirmed.

## Native DRC (2026-10-31) — FAIL (exit 5), same 22 findings

Pinned `kicad/kicad@sha256:18693567…dd3ec`, `kicad-cli version` 10.0.6, no network,
2 CPU / 6 GB, `flock /tmp/kicad-native.lock`, timeout 600 s, no fill. Run on a scratch
copy; inputs unchanged. Command in `evidence/native-20261031/COMMAND.txt`.

| Run | Exit | Violations | Unconnected | Parity |
| --- | --- | --- | --- | --- |
| No parity (`V198-drc.json`, SHA256 `a6cf031c…a1ef1f`) | 5 | 22 — **all equal to the original V196 records** (type, numeric description, UUIDs, positions) | 0 | — |
| With parity (`V198-drc-with-parity.json`, SHA256 `8b68b722…aa7ff`) | 5 | 22 | 0 | **10** (was 33 for V196) |

The 10 remaining parity notices:

- 9 benign `net_conflict` notices: NC pins named `unconnected-(…)` in the schematic.
- 1 `footprint_symbol_field_mismatch`: COUT `Datasheet` is empty on the PCB. The
  schematic holds the Samsung URL. Left unsynced so that the single confirming native
  run matches this file set; it is to be included in the next field revision.

The classification of the 22 findings in `../board-p-v196-unadopted/DRC-CLASSIFICATION.md`
applies unchanged. The V197 inert rules are bound to the V196 hash and are **stale for
V198**.

## Not changed on purpose

- U1/J1 geometry (the J1 GND 0.025 mm trim is a pending owner decision).
- No input TVS added.
- RMH2 stays 180 k: the FAILOFF-WINDOW.md option O3 retune waits for approval.
- No `.kicad_dru`.
