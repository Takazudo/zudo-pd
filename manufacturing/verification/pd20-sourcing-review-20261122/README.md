# PD20 sourcing-review package evidence (2026-11-22)

Scope: carry the 12 substitutions adopted under
[#326](https://github.com/Takazudo/zudo-pd/issues/326) into the Board P r3 and B20 layouts and export a new package at
`manufacturing/releases/pd20-sourcing-review-20261122/`. The earlier `pd20-prototype-review/` and
`corner-support-review/` packages are unchanged. Nothing was uploaded, quoted, ordered, programmed, energized or
measured. Electrical acceptance is NOT ESTABLISHED; T1–T8 are NOT RUN.

All native steps used `kicad/kicad@sha256:18693567392b80da435f9fa952ce3a3e534c66eb5a6033f5b9c80aa3b19dd3ec`
(KiCad 10.0.6) in a Linux cloud container.

## Board P r3 changed only the adopted identities

`scripts/pcb/board-p-r3-draft/run.sh` rebuilt `boards/board-p/board-p.kicad_pcb` from `board_p_spec.py` with the
committed placement. The PCB diff is limited to D8 / D9 / D11 / D12 / D13 (library identity
`SOD-123_L2.8-W1.8-LS3.7-RD` → `SOD-123_Pad0.90x0.95mm_P3.15mm`, descr, model path, Value, LCSC; the library-inherited
`LCSC Part` alias is gone) and the R23 / R26 LCSC field. PCB `3fc44335…` → `3cc1affe…`.

- Native DRC with schematic parity and all severities: 0 errors, 0 unconnected, 3 reviewed MH1–MH3 parity items and
  the same 95 warnings by type as before (`boards/board-p/r3-draft/native-drc.json` and its receipt).
- `verify-corrections.py`: PASS. It now accepts exactly this rebind for the five zeners, with position, rotation,
  layer and placed pads required to equal the historical baseline.

## B20 used the unchanged value-only field sync after a geometry-identical rebind

[`field-sync/field-sync.sh`](field-sync/field-sync.sh) runs:

1. `scripts/pcb/board-b20/sync-footprint-identity.py` for D4 / DZ1 / DZ2 / DZ3. Library pads are identical; only the
   library identity, descr, model path and `LCSC Part` alias change, and a reverting comparison proves the rest of
   the board is identical ([`footprint-identity.json`](field-sync/footprint-identity.json), `bc16fc9b…` → `9a8188df…`).
2. The unchanged `sync-fields.py` on the 25 adopted refs, `finalize_refill.py`, and `verify-field-sync.py`: fills and
   all non-field content identical (`9a8188df…` → `b4de1f6b…`).
3. Re-derived report-input receipt, loop, current, thermal and power reports; routing-report counts unchanged.

DRC with refill and parity: 0 errors, 0 unconnected, 0 parity, and the same four reviewed J6 / J7 / J10 / J11
`lib_footprint_mismatch` warnings ([`drc-summary.json`](field-sync/drc-summary.json)). ERC: 0.

## Pair checks and export passed

- STEP datums: 48 model pairs PASS (`footprints/kicad/step-datum-verification.json`). The neutral SOD-123 pair is a
  byte copy of the already-normalized pair and is recorded in `scripts/pcb/step-datum-normalizations.json`.
- Pair assembly preview (`scripts/pcb/board-b20/assembly-preview.py`): PASS for populated cross-board clearance, the
  C5 envelope, the support collars and the supplemental envelopes. Nominal CAD only.
- `export-jlcpcb.py --boards board-p board-b20-draft`: DRC 0 errors and 0 unconnected on both boards; B20 ERC 0.
  Board P r3 44 fitted / 27 lines; B20 294 fitted / 88 lines. Both `cpl.csv` files are byte-identical to the
  earlier package.
- `verify-jlcpcb.py --write`: PASS (`independent-validation.json`); 161 `SHA256SUMS` entries, manifest `940e805f…`.
- `verify-upload-files.py` (default release now this package): UPLOAD FILE INTEGRITY PASS 6/6.

The large `populated-stack.step` (`f90177a1…`) is local-only and listed in `manufacturing/local-only-assembly-previews.json`.
