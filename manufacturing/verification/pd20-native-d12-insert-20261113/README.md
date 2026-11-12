# D12 native insertion of R77–R80 (2026-11-13, selected Mac)

CALCULATED geometry evidence for the readiness D12 series resistors. It is not electrical,
thermal, supplier or order acceptance.

## Edit

`d12-insert.py` applies `insert-plan.json` with the pinned KiCad 10.0.6 pcbnew
(`tmp/mac-kicad-tools/kicad-python`, image `kicad/kicad@sha256:18693567…`).

- Input is the BEFORE board, sha256 `579385ac…`, from #283 head `a2186810`, with the D11 field sync.
- Footprints are `zudo-pd:R0402`, 100k, LCSC C25741. Each one is bound to its schematic symbol path.
- Pad 1 is `*_DIV` and pad 2 is `*_IN`. This follows the exported schematic netlist.

| Ref | Net pair | At (mm) | *_IN routing |
| --- | --- | --- | --- |
| R77 | OV12 | (67.46, 60.00), 270° | F.Cu 1.65 mm to U6.3. The old pin-side via is removed. |
| R78 | UV12 | (70.61, 57.16), 0° | F.Cu 2.55 mm + In2 3.63 mm, 2 vias, to U6.6 |
| R79 | OV5 | (84.20, 55.00), 0° | F.Cu 4.12 mm, no vias, to U7.3 |
| R80 | UV5 | (69.02, 48.18), 0° | F.Cu 2.43 mm + In2 16.91 mm, 2 vias, to U7.6 |

No copper or footprint on any other net was moved. The only free 0402 site next to U7 went to R79.
A search that allowed GND stitching vias to move found no shorter UV5 site. Takazudo accepted the
UV5 route on 2026-11-13 over the alternative of moving P5_SUP and GND copper above U7.

## Stray capacitance on *_IN (CALCULATED, project assumption)

Per-mm figures are F.Cu 0.09–0.15 pF/mm and In2 0.11–0.134 pF/mm. In2 sits 0.2 mm above the
B.Cu GND pour with εr 4.6 and has no pour of its own. Each via counts as 0.2–0.4 pF.

| Net | Stray C |
| --- | --- |
| OV12_IN | 0.15–0.25 pF |
| OV5_IN | 0.37–0.62 pF |
| UV12_IN | 1.03–1.67 pF |
| UV5_IN | **2.48–3.43 pF** |

The UV5 upper bound exceeds the 3 pF stray PA in D12. With 3.43 pF, the input RC grows by at most
about 0.04 µs over the ≤1.8 µs figure. The IB-based threshold screen does not depend on capacitance.
D12's input RC must be recomputed with this figure.

## Checks

- DRC under the unchanged authored rules (kicad-cli, refill, schematic parity):
  - 0 errors, 0 unconnected, 0 parity findings;
  - only the four reviewed J6/J7/J10/J11 `lib_footprint_mismatch` warnings.
- `finalize_refill.py`: PASS. Two fresh pinned refills are byte-identical, and non-fill geometry and IDs are unchanged.
  - Output PCB sha256 `83e369f6…`; see `boards/board-b20-draft/refill-finalization.json` and `refill-finalization.log`.
  - The first attempt was rejected because the new parts' hidden LCSC field lacked the 0.15 mm font thickness.
    The applicator now sets it, and the rerun passed.
- `verify-insert-parts.py` (origin/main `a36a021f`, sha256 `3c68ad14…`) on BEFORE → unfilled AFTER (`416f2c45…`): PASS with `--reach-mm 32`.
  - 284 existing footprints are identical, as are 4,173 copper items on other nets. The project rules are identical.
  - The reach is widened because splitting a long In2 segment replaces it whole. The three long added
    segments (OV12_DIV 29.2 mm, UV5_DIV 12.1 mm, UV5_IN 15.5 mm) are collinear sub-pieces of the
    removed segments. The verifier lists each added and removed item.
- The same verifier on the refilled AFTER **fails its fill-vertex screen**. Fill vertices on GND_IN1, GND_F
  and GND_B change outside the 2 mm region, at the y of the edit (`insert-verification-filled.log`).
  - These are KiCad's zero-width fracture slits, which join a new or removed antipad to the zone outline.
  - The polygon-area comparison (`fill-area-check.py`, `fill-area-outside-region.json`) puts the
    symmetric difference outside the region at 5e-7, 1.6e-4 and 5.7e-6 mm² respectively.
  - The vertex screen is the verifier's own limitation. It is recorded here, not waived.
- Report re-derivation: report-input receipt, loop, current, thermal and power reports.
  - Only the input bindings change; the calculated values do not.
  - `routing-report.json` counts are now the native 3503 tracks / 781 vias, with a note.
  - `test_load_cases` OK, including the thermal freshness test that #283 expected to fail until this step.
