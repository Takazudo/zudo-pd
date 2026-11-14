# D2 native layout of the B20 discharge network (2026-11-14, cloud, pinned KiCad 10.0.6)

CALCULATED geometry evidence for readiness D2 (`dec-b20-d2-sequenced-fast-discharge`, layout disposition
`dec-b20-d2-back-side-layout`). It is not electrical, thermal, supplier or order acceptance.

## Edit: 26 parts on B.Cu, everything else unchanged

The input is the BEFORE board from `main` `b377136`, sha256 `83e369f6…` (the D12 PCB). `tooling/build.sh` runs the
edit with the pinned image `kicad/kicad@sha256:18693567…` (`tooling/kpy.sh`):

1. `tooling/apply.py` applies `tooling/plan.json` in pcbnew. It deletes the six swapped footprints and their stubs,
   adds 26 B-side footprints bound to their schematic symbols, adds the routed copper, and syncs the R61 / R62
   Value and LCSC fields that #303 changed.
2. A DRC-driven prune (`tooling/prune_step.py`, log `tooling/prune-log.json`) removes or trims copper that KiCad
   reports as dangling. This is the old stubs of the removed lands, never GND.

Placement (`tooling/plan_bl.py`, `tooling/plan_um.py`) and routing (`tooling/route_all.py`, `tooling/d2route.py`
with the repository A* core) are scripted and deterministic.

There is no free WSL2512 site on F.Cu: front courtyards cover about 61 % of the board. The parts therefore sit on the
back, which faces up when installed. They clear the H1–H7 screw-head courtyards, THT pins by 0.9 mm and the B.SilkS
rail labels.

| Cluster | Parts (x, y mm; rotation) |
| --- | --- |
| +12 / +5 V, beside J6 / J7 | RX12 (3.0, 69.65; 90), RX5 (7.9, 69.65; 90), Q51 (2.68, 75.6; 180), Q52 (7.43, 75.6; 180), CDG12, RDG12, CDG5, RDG5 |
| −12 V and the sequencer, upper middle | Q55 (50, 25; 90), RXN3 (56, 23), RXN2 (64, 23), R76 (63, 18), C44, C45, D4, Q9, RSQ3, Q13, RSQ4, D5, Q8, RSQ2, RSQ1, Q7, R81, R82 |

- **Pulse paths.** P12_DX, P5_DX, M12_DX, M12_DXA and M12_DXB are 1.2 mm B.Cu and contain no vias. RX12 / RX5 reach
  J7 by 1.2 mm B.Cu. Q51 / Q52 sources have three GND vias each, and R76.1 has four.
- **Q55 to M12_OUT.** This path is 1.0 mm B.Cu / In2 with paralleled vias.
- **DIS_P chain.** The retained DIS_P chain from R60 to Q56 ran through the old Q51.1 pad. A 0.25 mm F.Cu bridge
  from (96.7, 68.3) to (97.6, 67.6) replaces that junction.
- **GND vias.** Eleven GND stitching vias under the new courtyards are removed. Two GND vias at (58.45, 41.5) and
  (55.7, 39.5) keep a B.Cu GND island that the new M12_OUT track cuts off. Without them, the refill drops 80.7 mm²
  of B.Cu pour.

## DRC and finalization: PASS

- DRC with refill and schematic parity, under unchanged authored rules:
  - 0 errors, 0 unconnected items, 0 parity findings;
  - only the four reviewed J6 / J7 / J10 / J11 `lib_footprint_mismatch` warnings;
  - no silk or courtyard findings for the back parts.
- `finalize_refill.py` passes (`refill-finalization.log`):
  - two fresh refills are byte-identical;
  - non-fill geometry and native IDs are unchanged;
  - the output PCB sha256 is `b59d7a36…`; see `boards/board-b20-draft/refill-finalization.json`.
- The unfilled AFTER board (sha256 `4a8b2c41…`) is the finalization input.

## Bounded edit: verifier PASS on the unfilled board; filled-board screen recorded

`verify-insert-parts.py` is extended on this branch with three options:

- `--replace` covers a land swap that keeps the reference. Both the old and new courtyards anchor the edit, and the
  old and new pad nets are allowed.
- `--field-sync` covers a Value / LCSC-only change.
- `--added-reach-mm` sets a separate reach for added copper.

Copper on a net whose every BEFORE pad is on a replaced footprint is reported as a re-laid-out net instead of being
reach-checked.

```sh
python3 scripts/pcb/board-b20/verify-insert-parts.py BEFORE.kicad_pcb AFTER.kicad_pcb \
  --refs C44,C45,CDG12,CDG5,D4,D5,Q13,Q7,Q8,Q9,R81,R82,RDG12,RDG5,RSQ1,RSQ2,RSQ3,RSQ4,RXN2,RXN3 \
  --replace Q51,Q52,Q55,RX12,RX5,R76 --field-sync R61,R62 --reach-mm 12 --added-reach-mm 26 --output OUT.json
```

**Unfilled AFTER: PASS** (`insert-verification-unfilled.json`).

- 288 existing footprints are identical.
- 3,310 copper items on other nets are identical.
- The project rules are identical.
- 101 copper items are removed, including the 11 GND vias, and 195 are added. Each one is listed.
- Re-laid-out nets: M12_DX (62 old items), P5_DX (6) and P12_DX (1).
- The farthest removed item is 11.9 mm from an edited courtyard: the old RX12 F.Cu feed at y = 70.1, whose ends
  were both on replaced parts.
- The farthest added item is 25.7 mm away: the long DIS_P and M12_DG feeds from the sequencer to the existing nets.
  The sequencer sits at the top of the board and DIS_P runs along the bottom.

**Refilled AFTER: the vertex screen refuses** (`insert-verification-filled.log`), as it did for D12. The
refusal is `Fill of …/In1.Cu changed outside the edit region`. `fill-slit-check.py` (the D12 tool) with
`edit-region.json` (`edit-region.py`) gives the following outside the region (`fill-slit-check.json`):

| Zone | Area delta outside region | Reading |
| --- | --- | --- |
| GND In1 | +2.3e-4 mm² | Re-tessellation scale |
| GND F.Cu | +4.98 mm² | Four gained pieces, at most 2.6 mm². The pour is retained around the two new island vias and fills a removed stub at (44.7, 38) |
| GND B.Cu (main) | +64.5 mm² | Four gained pieces, at most 31.4 mm², in space vacated by the retired M12_DX / P5_DX copper. No piece is lost |
| GND B.Cu (second zone) | 0 | — |

No copper is lost outside the edit region. Every out-of-region difference is a gain. This is a recorded
reading of the screen, not a waiver of it.

## Pulse paths and loop resistance (CALCULATED, project assumption)

- **Heating.** The adiabatic I²t for each discharge uses the simulated per-resistor energies divided by 0.5 Ω:
  8.96 / 12.95 / 1.04 mJ for +12 / −12 / +5 V ([d2-sequenced-20261114.md](../../sim/board-b20-phase33/d2-sequenced-20261114.md)).
  On the narrowest segment between a rail connector and its switch (0.6 mm, 1 oz) it gives under 0.3 K. A single
  0.3 mm via barrel gives under 0.3 K too.
- **Loop resistance.** Routed copper from each discharge part's rail pad to the connector pads is computed by
  `loop-resistance.py` (`loop-resistance.txt`, 1 oz at 20 °C, In1 GND return not included).

| Rail | Part | To J7 / J6 | To J10 | To J11 | Share of the load |
| --- | --- | --- | --- | --- | --- |
| +12 V | RX12 | 3.4 mΩ | 22 mΩ | 44 mΩ | 0.7–9 % of 0.5 Ω |
| +5 V | RX5 | 0.6 mΩ | 26 mΩ | 61 mΩ | 0.1–12 % of 0.5 Ω |
| −12 V | Q55 | 34 mΩ | 61 mΩ | 83 mΩ | 2–6 % of 1.5 Ω |

Charge stored behind J11 discharges up to 12 % slower than simulated. This is not re-simulated. A slower +12 V
discharge only lengthens the sequencer's −12 V hold. The 100 ms level limit has about 80× margin over the 1.224 ms
simulated maximum.

## Re-derived reports, STEP datums and export

- **Reports.**
  - Re-derived from the saved native copper: report-input receipt, loop, current, thermal and power reports.
  - Their calculated values are unchanged; only the input bindings change.
  - `routing-report.json` counts are now the native 3,566 tracks / 812 vias, with a note.
- **STEP datums.** The WSL2512 model `R2512_WSL_MaxEnvelope_L6.61-W3.44-H0.89` joins
  `scripts/pcb/step-datum-normalizations.json`.
  - Its screen passes at 5.7e-12 mm.
  - Its independent review is PENDING.
  - The proof passes 47 pairs (`footprints/kicad/step-datum-verification.json`).
- **Assembly preview and development export.** These are recorded in `execution.json`. They ran through cloud
  wrappers of the same pinned image instead of the selected Mac.

## Remaining residuals

- **Two-sided assembly.** B20 becomes a two-sided assembly. At JLC's published Standard PCBA price (read
  2026-11-14), setup goes from $25.56 single side to $51.12 double side and the stencil from $8.21 to $16.42, so
  the fixed cost rises by $33.77 per order. Bottom-side CPL rotations must be checked in JLC's placement preview
  before an order.
- **Tool history.** The tooling was run from `tmp/d2/` and `tmp/d2v/`. It is kept here as the record of the edit.
- **Open checks.** The WSL repetitive-pulse residual (D7) and bench T5 stay open.
