# Board P 15 V (separate 15 V zudo-pd product)

**Unvalidated draft. Not for fabrication or ordering.** No layout review exists, and nothing here is
measured. The as-built `../board-p/board-p.kicad_pcb` and the `corner-support-review` package are unchanged
and remain the ordered-revision files.

The user chose separate products on 2026-11-01 (`dec-separate-products`). The 15 V zudo-pd keeps the
as-built 15 V Board P, except for the RESET subset of the common controller block (`dec-p15-reset-subset`,
LED requirements R1.1 to R1.3).

## Schematic: as built plus the RESET subset

Source: `scripts/schgen/board_p15_spec.py`, generated into `board-p15.kicad_sch`.

**Stage 1 matched the as-built board pin for pin.** That spec copied the as-built design: D5 SMAJ16A,
Q1 AO3401A, VDD on VBUS_IN, R13/R14 470 Ω and R21 10 kΩ. Three comparisons matched exactly:

- `check_baseline.py` against `scripts/schgen/baselines/board-p.json`;
- `scripts/pcb/board-p15/pcb-net-parity.py` against the as-built PCB: 18 nets and the 5 no-connect pins;
- the LCSC codes and DNP flags of the package BOM, all 25 references.

**Stage 2 is the committed spec.** `scripts/schgen/baselines/board-p15-allow.json` declares every delta from
the as-built baseline:

- R21 becomes a 0 Ω C21189 strap from U1.6 RESET to GND;
- J2.4 is not connected;
- R15/R16 are removed, so the I2C pull-ups live on the programming jig.

Native KiCad 10.0.6 ERC reports 0 errors and 29 `pin_to_pin` warnings, all caused by the STUSB4500
symbol's unspecified pin types. `verify_netlist.py` passes: 24 nets and 87 nodes.

## Draft PCB: as-built placement with RESET re-routed

Build it with `scripts/pcb/board-p15/build-draft.py`, which only reads the as-built file. Every as-built
placement and track is kept, apart from these changes:

- R15/R16 and their SCL, SDA and VREG_2V7 branches are removed.
- J2.4 has no net, and its silk label reads NC.
- R21 is an R0603 0 Ω strap beside U1.6 at (8.6, 20.0). Its GND end has a via into the B.Cu GND pour.
- VBUS_VS_DISCH leaves its two vias beside the U1 RESET corner and runs on B.Cu only.

Checks are recorded in `draft-checks.json` and `net-parity.json`.

- **Net parity: PASS.** The PCB matches `board_p15_spec.py` pin for pin, with no-connects.
- **DRC: no errors and no unconnected items.** Warnings: `lib_footprint_mismatch` 21,
  `silk_overlap` 19, `text_height` 17, `silk_over_copper` 8, `lib_footprint_issues` 3 and
  `silk_edge_clearance` 2.
  - The as-built board under the same KiCad version has no `silk_overlap` warnings and 2
    `silk_over_copper` warnings.
  - The new silk warnings come from the R0603 silk around R21 meeting the U1 reference field.
    That silk is OPEN.
- **RESET clearance, same layer: met.** The closest VBUS-class copper on the same layer is 1.353 mm away
  (U1.6 to the U1.9 DISCH pin, fixed by the QFN). The target was at least 1.0 mm; the as-built board
  measured 0.222 mm.
- **RESET clearance, other layer:** the closest copper is 0.688 mm in plane, from R21.1 to the B.Cu
  VBUS_VS_DISCH track. The as-built board measured 0.0 mm, with B.Cu tracks under the RESET track.

The 1.0 mm target is the LED project's proposed RESET strap keep-out. It has no manufacturer source.
Leakage, I2C idle without pull-ups, and the 15 V NVM image with readback are all OPEN.
