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

## Fill-screen exception (open), recorded per the verifier owner's conditions

- **(c) Verifier refusals.** Both the `#286` verifier (origin/main `a36a021f`) and the slit-aware `#287`
  verifier (origin/main `224ef46a`, sha256 `37b6edea…`) refuse the refilled AFTER with the same line:
  `Fill of 66bdc61b-a697-57c7-8c21-d31d7ae259ea/In1.Cu changed outside the edit region, e.g. at ('14.048615', '60.833682')`
  (`insert-verification-filled.log`, `insert-verification-filled-main-224ef46.log`).
  - Zones with out-of-region vertex changes: GND_IN1 In1.Cu (68 vertices), GND_F F.Cu (328) and GND_B B.Cu (117).
- **(a) Area comparison.** `fill-slit-check.py` writes `fill-slit-check.json`. For each zone uuid and layer it
  gives the area outside the edit region before and after and the delta:
  - In1 −2.9e-7 mm²
  - F.Cu −3.4e-5 mm²
  - B.Cu −1.8e-6 mm²
  - The symmetric difference outside the region is at most 1.6e-4 mm².
- **(b) Slit test: FAILS as defined.** Of the out-of-region changed vertices, only 9 lie on reverse-edge slits.
  - **504 do not.** Each is listed with its distance to the other board's fill boundary for the same zone.
  - The maximum distance is **3.6 µm**, and 492 of them lie at about 0, which means collinear re-splits.
  - Example: the refused In1 vertex moves to (14.052342, 60.832941), a 3.7 µm shift along a via antipad arc
    next to a slit attachment.
  - This is consistent with KiCad re-tessellating the whole zone inside its 5 µm `max_error`, but that is
    **not confirmed**. The KiCad source was not traced.
- **(d) Other checks.** `verifier-fill-bypass.diff` is a scratch copy of the `#286` verifier with only the
  fill refusal turned into a recorded count. It passes on the refilled AFTER
  (`insert-verification-filled-fill-bypassed.json`):
  - 284 footprints identical;
  - 4,173 other-net copper items identical;
  - project rules identical.
  - The verifier itself is not changed on this branch.

## Decision: recorded exception (Takazudo, 2026-11-13 03:15Z)

Takazudo chose option A, "record as an exception and proceed with #283", on the decision card in the
"Retain primary sources for Board P evidence" thread. The record follows.

**Refusal.** The verifier on main (`224ef46a`) refuses with:
`Fill of 66bdc61b-a697-57c7-8c21-d31d7ae259ea/In1.Cu changed outside the edit region, e.g. at ('14.048615', '60.833682')`

**Size of the difference.**
- The fill-area delta outside the edit region is at most 3.4e-5 mm² (GND_F). The symmetric difference is at most 1.6e-4 mm².
- The largest distance from a changed vertex to the other board's fill boundary is 3.6 µm.

**12 unexplained GND_F F.Cu vertices.** These are the 12 with a distance above 0.1 µm (`fill-investigation/check1.*`, `check2.*`).
- Eleven form a cluster at (92.37–92.45, 54.06–54.10). It lies on the fill edge that follows the
  RAMP_RST track (94.5,55.9)-(92.3,53.4), 0.37 mm from that track and 0.68 mm from its via. It is
  7.0–7.75 mm from any D12 change and from the R79 courtyard.
- The twelfth is at (107.287, 49.259), 0.26 mm from pad R62.1 and 22–23 mm from any D12 change.
- Both lie in filled polygons with no changed vertex inside the edit region.
- They are not on reverse-edge slits and not on via or pad antipad arcs. Neither the slit-move nor the
  edit-reach explanation holds, so the cause is unexplained.

**Control.** One benign via on UV5_DIV at (68.36, 48.55) with a short In2 jog, added on a scratch BEFORE
copy, then one pinned refill (`fill-investigation/control-via-*`):
- 80 out-of-region vertices change;
- their largest distance to the other board's fill boundary is 4 nm;
- the area delta outside the region is at most 1.7e-7 mm².
The control does not reproduce µm-scale shifts.

**Rejected alternative.** A 5 µm-tolerance fill screen (PR #288, head `677f42cf`) was tried and closed
unmerged. It passed this board (`fill-investigation/insert-verification-pr288-677f42cf-closed.json`), but
review found it could pass an island over a far via hole.

All other verifier checks pass, as recorded above.
