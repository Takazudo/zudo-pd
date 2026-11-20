# Independent review of the D2 layout (PR #307), 2026-11-20

Reviewed head: `9312dc6` merged with main `ea0a4a8` (merge `dc1df18`; main added orchestration documents only).
B20 PCB `7a8270f5…`, unchanged by the merge. Reviewer: an independent cloud worker; the campaign manager re-ran the
checks marked below. Campaign tracker [#318](https://github.com/Takazudo/zudo-pd/issues/318). Nothing here is measured.

## Native DRC reproduces on the merged head

The manager re-ran pinned KiCad 10.0.6 (`kicad/kicad@sha256:18693567…`, pulled by digest) DRC with refill and
schematic parity on a staged copy: 0 errors, 0 unconnected items, 0 parity findings, and only the four reviewed
J6 / J7 / J10 / J11 `lib_footprint_mismatch` warnings. This matches the layout record.

## Both pending models are accepted

| Model | Verdict | Basis |
| --- | --- | --- |
| `R2512_WSL_MaxEnvelope_L6.61-W3.44-H0.89` | ACCEPT | One box, 6.61 × 3.44 × 0.89 mm, Z 0 to 0.89: the WSL2512 maxima recorded in the C511023 owner (L 0.260 in, W 0.135 in, H 0.035 in) rounded up. STEP and WRL corners are identical. The long axis follows the pad axis (pads at ±2.855 mm), the body sits inside the courtyard (±3.93 × ±2.35 mm), and no instance has a model offset |
| `R0402` (C25741) | ACCEPT WITH LIMITS | Third-party EasyEDA/LCSC model, nominal 1.00 × 0.50 × 0.36 mm, seated at Z 0 and oriented along the pad axis. It is up to 0.05 / 0.025 / 0.04 mm under the C25741 maxima (1.10 / 0.55 / 0.40 mm), and its STEP file name says H0.4 while the body is 0.36 mm. The courtyard (±1.19 × ±0.75 mm) carries the clearance, so no collision result changes |

`uv run --python 3.12 scripts/pcb/verify-step-datums.py` passes 47 pairs and matches the committed proof. Plain
`uv run` picks Python 3.13, which has no vtk 9.3.1 wheel.

## Schematic, spec, PCB and export agree for the 26 bottom parts

Refs, values, LCSC codes and footprints of the 26 B.Cu parts agree across `board_b20_spec.py`,
`board_b20_components.py --check`, the schematic and the PCB. D4 / D5 pad nets match their intended polarity. The
development export manifest has no per-part list, but its PCB, schematic, project and spec hashes match and it records
26 bottom placements.

## The filled-board refusal is a gain-only change, now checked by a narrow option

`fill-slit-check.py` and `edit-region.py` reproduce the committed results exactly. An independent shapely audit
(`fill-gain-audit.py` → `fill-gain-audit.json`) gives these out-of-region changes:

| Zone | Gain | Largest loss |
| --- | --- | --- |
| GND B.Cu (main) | 64.5 mm² | re-tessellation only |
| GND F.Cu | 5.0 mm² | re-tessellation only |
| GND In1 | 2.3e-4 mm² | 2.4e-4 mm² sliver, 9 µm deep at (77.7, 14.46) |

Every loss is within twice the project `max_error` (0.005 mm), so it is re-approximation, not lost copper. The layout
README's "no copper is lost" is true at that resolution only. Gained copper keeps at least 0.2505 mm to other-net
copper (zone clearance 0.25 mm). One B.Cu island is split inside the edit region and every piece is kept.

`verify-insert-parts.py` gains `--allow-outside-fill-gain`. It accepts an outside change only when every removed fill
corner lies inside (or within 2 × `max_error` of) the AFTER fill and every added corner lies outside (or within that
distance of) the BEFORE fill, and only for allowed nets. Seven controls in `test_verify_insert_parts.py` refuse a removed
island, a new hole, a gain on a net that is not allowed, other-net copper and a zone-setting change. A real-pair test
runs when `B20_D2_BEFORE` points at the `b377136` board. On this head all 27 tests pass with that variable set, and
the D2 pair passes with the option (`insert-verification-filled-gain.json`). It still refuses without it. A pass is not
a clearance or connectivity proof; the DRC above remains required.

This disposition covers the D2 edit only. It does not change the D12 record, whose open fill-screen exception was
accepted by Takazudo on its own terms.

## D2 sensitivity: layout parasitics keep the pre-registered margins; switch-threshold spread does not

`sensitivity.py` → `sensitivity.json` (CALCULATED; the manager reproduced it byte-equal in its results) and
`resim.py` → `resim.json` (exploratory SIM, not pre-registered; ngspice-44.2 in the pinned image). Details are in
[`d2-sensitivity.md`](d2-sensitivity.md).

- **Parasitics.** With hot RDS(on), the In1 GND return, WSL tolerance and 85 °C copper, the worst series total is
  +20 % / +24 % / +11 % on +12 / +5 / −12 V, about twice the layout README's "up to 12 %", which left out RDS(on) and
  the return. On the pre-registered timing grid, every corner still passes, in calculation and in SIM (high corner
  5.653 V against 6 V; low corner 0.906 V against 0.6 V; onset at least 16.6 µs after disconnect; levels by 1.3 ms).
- **Fitted values.** R62 47.5k and 47 nF + 22 nF set the Q55 firing delay and move it by +0.58 µs.
- **Threshold spread.** With the CSD18543Q3A guaranteed VGS(th) of 1.5–2.7 V (25 °C) and the gate-capacitor
  tolerances, Q51 / Q52 fire about 40–243 µs after disconnect and Q55 about 19–63 µs. The pre-registered sweep covered
  +12 V at 120–190 µs only. Exploratory decks at that band's edges fail R-VEE in both directions (|−12 V| 0.39 V while
  +12 V is present; 6.09 V once +12 V is absent with hot-threshold terms). The mechanism is the timing network, not the
  layout: parasitics move these margins by 0.03 V or less.

The threshold-spread result means the D2 discharge is not yet shown to meet R-VEE across its guaranteed part spread.
Its disposition is recorded in the readiness ledger D2 row.

## Smaller corrections

- Q51 has two GND source vias, not three as the layout README says (Q52 has four, R76 four).
- JLC's bottom-side placement-preview rotations were not checked here; they remain a supplier step.
