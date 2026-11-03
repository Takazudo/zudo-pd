# Board P 15 V (separate 15 V zudo-pd product)

**Unvalidated draft. Not for fabrication or ordering.** No layout review exists, and nothing here is
measured. The as-built `../board-p/board-p.kicad_pcb` is unchanged. On 2026-11-01 this draft was exported with Board B into
the `corner-support-review` directory as development review files, not an order; the ordered revision S3 stays at
commit `f25194f`.

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
VDD_LOC. The 1.47 kΩ feed and C2 + C38 (1.1 µF nominal) set τ ≈ 1.62 ms (phase 20 correction of 1.47 ms).
DS12499 Rev 7 gives no VDD ramp or UVLO requirement to check it against (UNKNOWN); the attach waveform is a
bench check.

**D9 window (phase 20, review F7):** D9's guaranteed VZ minimum is 16.8 V at 25 °C, but 15.76 V at −40 °C with
the TC maximum (16.0 mV/°C). That is only +0.01 V above a 15.75 V (+5 %) input, so knee leakage at the cold
+5 % corner is possible; sub-mA through 1.47 kΩ costs at most a few hundred mV of VDD and is functionally
benign. BZT52C20-7-F (C260890) was evaluated with `scripts/pcb/board-p15/zener-choice.py`
(`d9-zener-choice.json`): its 23.041 V pin bound at 28.6 V / 125 °C leaves 4.959 V to 28 V, under the 5 V
adoption margin, and its 22.64 V VZ maximum at 105 °C exceeds the 22 V VDD operating row. D9 stays BZT52C18.
At the surge row R29 dissipates 77.1 mW and R30 36.2 mW (0.1 W rating at ≤ 70 °C; derating above 70 °C
UNKNOWN), and D9 at most 183.5 mW (370 mW at 25 °C on FR-4).

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
- Back silk (phase 20, review F5, text only): the variant mark reads `P15 r1` instead of the as-built `rev2`, so
  a 15 V unit is not taken for an ordered rev2 board. The longer text is moved 3.071 mm up so it ends where
  `rev2` ended; at the `rev2` anchor it crossed the bottom edge. The wording is reversible.

Checks are recorded in `draft-checks.json` and `net-parity.json`.

- **Net parity: PASS.** The PCB matches `board_p15_spec.py` pin for pin, with no-connects.
- **DRC: no errors and no unconnected items** (phase 20 rerun, same counts as phase 18), with schematic parity: only the `extra_footprint` items
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

## Common Board P: P15 r1 serves LED and zudo-pd (user decision 2026-11-03)

On 2026-11-03 the user chose P15 r1 as the common Board P for the LED project and zudo-pd. Both use the same PCB, the same
population and the same 3 A NVM image (`nvm/stusb4500-15v.bin`). This is a documentation record. The PCB, the BOM
and the exported review package are unchanged.

- **LED first, then zudo-pd.** LED bring-up with the existing Board L uses a P15 r1 unit first. The same board then goes
  to zudo-pd Board B without a rewrite.
- **Program and verify before any mating.** Board L and Board B stay disconnected through all three stages, in this order:
  1. On a current-limited 5 V-only source: write, power-cycle, then pass P15-NVM-4 and P15-NVM-5.
  2. Still with no load connected, move to a current-limited PD test source that also offers 20 V and pass P15-NVM-6
     (15 V contract; VBUS_OUT off at 5 V). A 5 V-only source cannot exercise this test.
  3. Only after P15-NVM-6 passes may the board mate with Board L or Board B.
- **The voltage window depends only on the NVM.** P15 r1 has no hardware window or eFuse after the sink switch, and no
  footprint for one. A factory or lost image can pass 5 V, or request 20 V into the SMAJ16A D5. At the prototype stage
  this is an accepted residual (LED requirement R2.3, with R2.4 and R2.6 for the same cause). Per-unit NVM acceptance
  is the only mitigation, and it is NOT RUN.
- **Desk evidence: manager report `led-p15-compatibility.md` (2026-11-03, desk only, nothing built or energized).** It
  found:
  - **Mechanics: PASS (desk).** The outline (27 × 40 mm), the three Ø3.2 mm holes, J1 and JOUT1 equal the ordered LED
    Board P. JOUT1 mates with Board L J2 and Board B J5, which share the pin map 1/2 VBUS, 3 ATT, 4 PDOK, 5/6 GND.
  - **Added parts: PASS (desk).** All parts added on F.Cu sit at least 7.9 mm from a hole and at least 5 mm from Board L
    J2. The LED enclosure STEP interference pass is NOT RUN.
  - **Electrical rows:** R1.1–R1.4, R3.1–R3.3 and R3.5 are PASS (desk). R1.5 and R1.6 are PASS as procedures, with
    execution NOT RUN. R2.3, R2.4 and R2.6 are FAIL (no hardware window), and R2.5 is UNKNOWN.
  - **NVM image.** The image intent (two PDOs, PDO2 15 V, POWER_ONLY_ABOVE_5V = 1) equals the image the LED's as-built
    Board P was programmed with. The 3 A PDO2 only narrows charger compatibility, because a 15 V charger rated below
    3 A gives Board L nothing.
  - **Current limit.** P15 sets no current limit toward Board L, whose only limit is its F1 PPTC (0.75 A hold). The
    report advises a current-limited bench source for the first energizing of each Board L.

## Programming: jig pull-ups, power-cycle reload, NOT RUN

The procedure is [Board P15 NVM Programming](../../doc/src/content/docs/architecture/board-p15-programming.md).
The desk image is `nvm/stusb4500-15v.bin` (sha256
`76622e14862e53cf318b24eb662f7dc9f34d48134867cf954b30c195c26e8eeb`), built and checked by
`scripts/pcb/board-p15/nvm-image.py --check`. It has never been written or read back.
