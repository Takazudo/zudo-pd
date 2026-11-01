# Board P 15 V (separate 15 V zudo-pd product)

**Unvalidated draft. Not for fabrication or ordering.** No layout review exists, and nothing here is
measured. The as-built `../board-p/board-p.kicad_pcb` and the `corner-support-review` package are unchanged
and remain the ordered-revision files.

The user chose separate products on 2026-11-01 (`dec-separate-products`). The 15 V zudo-pd keeps the
as-built 15 V Board P, except for the RESET subset of the common controller block (`dec-p15-reset-subset`,
LED requirements R1.1 to R1.3) and the phase 17 additions: SCL/SDA pull-downs (`dec-p15-i2c-pulldowns`) and the
VDD feed with a local clamp (`dec-p15-vdd-local-clamp`).

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
- R15/R16 are removed, so the I2C pull-ups live on the programming jig;
- R22/R23 (100 kΩ C25803) pull SCL and SDA to GND, so the pins are defined in normal use (phase 17);
- VDD no longer sits on VBUS_IN. R29 (1 kΩ C21190) and R30 (470 Ω C23179) feed it through VDD_MID to
  VDD_LOC, where U1.24, C2 and the D9 BZT52C18 (C192739) clamp meet (phase 17).

Native KiCad 10.0.6 ERC reports 0 errors and 29 `pin_to_pin` warnings, all caused by the STUSB4500
symbol's unspecified pin types. `verify_netlist.py` passes: 26 nets and 99 nodes.

**VDD margin (desk, `calculate-input-ovp-20v.py` local-clamp model with 1470 Ω):** the VDD pin peaks at
20.802 V at the 28.6 V hot input estimate, +7.198 V below the 28 V limit (was −0.6 V with VDD on VBUS_IN), and
at 20.721 V (+7.279 V) at 26.0 V. D9 carries at most 8.82 mA. At a 4.72 V attach input, VDD is 4.373 V at the
idle IDD maximum (+0.273 V over 4.1 V). IDD during PD communication is UNKNOWN, so attach headroom is OPEN.
C2 (100 nF) decouples U1.24, and phase 18 adds the r3 C38 1 µF (C15849, `dec-p15-vdd-decoupling`) on
VDD_LOC. The 1.47 kΩ × 1 µF feed sets a 1.47 ms rise; its effect on STUSB4500 start-up is OPEN.

## Draft PCB: as-built placement with RESET re-routed

Build it with `scripts/pcb/board-p15/build-draft.py`, which only reads the as-built file. Every as-built
placement and track is kept, apart from these changes:

- R15/R16 and their SCL, SDA and VREG_2V7 branches are removed.
- J2.4 has no net, and its silk label reads NC.
- R21 is an R0603 0 Ω strap beside U1.6 at (8.6, 20.0). Its GND end has a via into the B.Cu GND pour. It
  carries `LCSC`, `LCSC Part` (C21189) and `MPN` fields.
- VBUS_VS_DISCH leaves its two vias beside the U1 RESET corner and runs on B.Cu only.
- J2.4 is on its own `unconnected-(J2-Pad4)` net, which clears the phase 16 J2.4 net conflict.
- R22 at (4.54, 33.05) and R23 at (5.04, 30.55) sit beside the J2 SCL/SDA pads, each with a GND via or track.
- The VBUS_IN track to U1.24/C2.2 is cut. R29 (20.6, 26.7) and R30 (18.15, 26.7) form the feed from the
  VBUS_IN copper near J3; D9 (18.9, 24.95) clamps VDD_LOC, and a B.Cu track with two vias returns VDD_LOC
  to U1.24/C2.2.
- C38 (phase 18) sits right of C2/C30 at (19.85, 22.05). Its VDD_LOC track runs through the C2/C30 gap to C2.2,
  and its GND end joins the existing GND via right of C30. No part moved.
- Silk (phase 18, text only): the supplier fields of every added part are hidden on F.Fab; the J2 SCL/SDA, J3
  VBUS and U1 reference texts moved off the new pads; the C30 reference is on F.Fab because C38 occupies its
  as-built spot.

Checks are recorded in `draft-checks.json` and `net-parity.json`.

- **Net parity: PASS.** The PCB matches `board_p15_spec.py` pin for pin, with no-connects.
- **DRC: no errors and no unconnected items**, with schematic parity: only the `extra_footprint` items
  MH1–MH3. Warnings: `lib_footprint_mismatch` 27, `text_height` 16, `lib_footprint_issues` 3,
  `silk_over_copper` 2 and `silk_edge_clearance` 2.
  - The silk classes now equal the as-built board: no `silk_overlap`, and the same 2 `silk_over_copper`
    (J1 circle, R12 reference over D5) and 2 edge warnings.
  - The phase 17 silk warnings came from the added parts' supplier fields, which landed visible on F.SilkS,
    not from D9's library silk; the SOD-123 footprint is unchanged.
- **RESET clearance, same layer: met.** The closest VBUS-class copper on the same layer is 1.353 mm away
  (U1.6 to the U1.9 DISCH pin, fixed by the QFN). The target was at least 1.0 mm; the as-built board
  measured 0.222 mm.
- **RESET clearance, other layer:** the closest copper is 0.686 mm in plane, from R21.1 to the B.Cu
  VBUS_VS_DISCH track. VDD_LOC and VDD_MID are in the scanned set and are not among the closest items. The as-built board measured 0.0 mm, with B.Cu tracks under the RESET track.

The 1.0 mm target is the LED project's proposed RESET strap keep-out. It has no manufacturer source.
Leakage is OPEN.

## Programming: jig pull-ups, power-cycle reload, NOT RUN

The procedure is [Board P15 NVM Programming](../../doc/src/content/docs/architecture/board-p15-programming.md).
The desk image is `nvm/stusb4500-15v.bin` (sha256
`76622e14862e53cf318b24eb662f7dc9f34d48134867cf954b30c195c26e8eeb`), built and checked by
`scripts/pcb/board-p15/nvm-image.py --check`. It has never been written or read back.
