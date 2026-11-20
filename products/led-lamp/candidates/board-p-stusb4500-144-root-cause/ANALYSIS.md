# Issue #144: STUSB4500 Board P fails to hold 15 V (desk root-cause ranking)

Status: desk analysis only. Nothing was measured, energized, flashed or reworked.
No hardware file changed. Rankings are hypotheses for a future, owner-performed
safe measurement, not a diagnosis.

Inputs read: issue #144 (owner observations + owner audit comment), #143 silk notes,
`scripts/schgen/board_p_spec.py`, the ordered PCB
`manufacturing/jlcpcb/2026-09-19/board-p/source/board-p.kicad_pcb`, main's
`boards/board-p/board-p.kicad_pcb`, the STUSB4500 owner bundle, and DS12499 Rev 7
(ST GitHub `usb-c/STUSB4500` @55d1109e, file sha256 `407ee676…`).

## Observations being explained (from #144)

| # | Observation |
| --- | --- |
| O1 | Both assembled PCBAs show the same failure. |
| O2 | Early: VBUS reached 15 V but VBUS_EN_SNK / Q1 gate stayed near 15 V (sink switch not enabled). |
| O3 | Once, with Board L connected: JOUT1 briefly 15 V, LEDs lit, then went out. |
| O4 | Now VBUS never leaves 5 V. |
| O5 | RESET (U1 pin 6) reads 0.93 V while powered from 5 V. |
| O6 | ST GUI now reports "I2C read error"; NVM write + readback had worked earlier. |
| O7 | Active CC reads 1.43 V. |
| O8 | Unpowered: RESET-GND 6.93 kOhm, RESET-SCL 13 kOhm, RESET-CC2DB open. |

Datasheet anchors (DS12499 Rev 7): RESET is active-high, VIL max 0.35 V, VIH min 1.2 V,
no internal bias specified; ST's application figure uses a 10 kOhm pull-down.
0.93 V is inside the undefined band. VDD abs max 28 V.

## Layout facts found in the ordered PCB (new)

| Item | Value | Note |
| --- | --- | --- |
| RESET F.Cu trace x=5.632, y 22.526-26.082 | passes **between the pads of R13** (470 Ohm, VBUS_OUT to DISCH) | 0.222 mm to each pad; flux/residue under a 0603 bridges RESET to a VBUS-level node |
| RESET trace segment at y=20.918 | 0.326 mm from a VBUS_VS_DISCH via at (8.63, 20.218) | that net is VBUS_IN via R14 470 Ohm: 5-15 V |
| RESET-SCL | 0.368 mm (QFN pins 6/7 adjacent) | SCL is pulled to VREG_2V7 by R15 4.7 k |
| RESET-CC2DB | 0.22 mm (QFN pitch) | O8 shows no continuity |
| J2.4 | RESET on a bare pogo pad; #143 notes silk mislabelled "NC" | ESD/miswire exposure |
| DRC | clean | clearance rules do not catch contamination paths |

**Erratum (phase 8, replaces an earlier claim):** this section first called R19 a latent BOM
defect. That was wrong. In `boards/board-p/board-p.kicad_pcb` the schematic-derived `LCSC`
property of R19 is C21189 (0 Ohm), matching the generator. Only the second, imported
`LCSC Part` field carries the stale generic-footprint value C25803. The same holds for 10
other Board P footprints (C2, C35, R12-R18, R20) and 20 Board L footprints. This is the
documented condition in `manufacturing/README.md` ("Traceability and coordinates"): the export
script rewrites both fields from the generator identity, and the 2026-09-19 release records
exactly these 11 + 20 corrections in `checks/export-validation.json`. The ordered BOM is correct.

The active board files are not edited for this. `manufacturing/jlcpcb/2026-09-19/manifest.json`
pins their SHA-256 (`source_hashes`), so any edit makes `verify-jlcpcb.py` report "source
changed since export" for the historical release. Normalize the `LCSC Part` fields in the next
board revision, not in the ordered source.

## Ranked candidate causes

| Rank | Candidate | For | Against / gap |
| --- | --- | --- | --- |
| 1 | **VBUS-proportional leakage into RESET** (contamination under R13 or near the VBUS_VS_DISCH via, under the QFN, or via the jig's J2.4 wire) | A ~44 kOhm path from VBUS against R21 10 k (or ~30 k against the measured 6.93 k) gives 0.93 V at 5 V and ~2.8 V (> VIH) at 15 V. That resets U1 right after the 15 V transition, which explains O2 (15 V seen, VBEN released), O3 (lit then out), and a reset-loop / undefined state for O4 and O6. Same layout on both boards fits O1. | Leak value not measured; O8 (6.93 k to GND instead of 10 k) implies an extra ~23 k path to *something* unpowered, consistent with a leak but not proving which node. |
| 2 | **Leakage from the 2.7 V / SCL domain** (RESET-SCL 13 k, SCL at VREG_2V7) | Divider 2.7 V x 6.93k/(6.93k+13k) ~ 0.94-0.98 V: fits O5 numerically. | Predicts a level that is constant with VBUS, so by itself it does not reset U1 at 15 V; it explains O5 but not O2/O3 well. Can coexist with rank 1. |
| 3 | **U1 internal damage from a common stress** | SMAJ20A clamp Vc 32.4 V @ 12.3 A exceeds the 28 V VDD abs max; hot-plug ringing or a source fault could exceed it. Exposed J2.4 invites ESD. Damage could create the RESET leak and the I2C failure (O6). | No evidence of an overvoltage event; would need two boards to be damaged the same way (O1). |
| 4 | **VREG_2V7 loaded by R15/R16 I2C pull-ups** | Owner audit: documented-use violation (VREG_2V7 is not specified for external load). | 2 x 4.7 k at 2.7 V is ~1.1 mA; low causal weight for loss of 15 V. Fix anyway. |
| 5 | **NVM image wrong or lost** | Factory image has 20 V/1 A as highest priority and POWER_ONLY_ABOVE_5V=0; a lost image would pass 5 V or 20 V. | Programmed image (2 PDOs, PDO2 15 V/3 A, POWER_ONLY_ABOVE_5V=1) read back correctly earlier. No 40-byte dump retained: evidence gap. |
| 6 | **VBUS window / inrush dip on Board L hot-plug** | Board L input capacitance at hot-plug could dip VBUS below VMONUSBL (~12 V at the default shift) and trigger hard reset: explains O3 only. | Does not explain O2, O4, O5, O6. |
| - | Ruled out / low | CC wiring and U1 rotation (I2C programming worked; O7 valid CC), R14 divider, Q1 permanently off (O3 shows it conducted). | |

## Discriminating checks (proposed, owner-performed, no rework needed for 1-4)

| Check | Discriminates |
| --- | --- |
| 1. Unpowered RESET to VBUS_IN (J3.4) and to VBUS_OUT resistance, both meter polarities | Symmetric finite value: PCB leak (rank 1). Diode-like: U1 internal (rank 3). Open: rank 1 unlikely. |
| 2. Powered from a fixed 5 V supply: RESET at 4.6 V vs 5.4 V VBUS | RESET tracks VBUS: rank 1. Constant: rank 2. |
| 3. Powered: hold SCL low (J2.1 to J2.3) and read RESET; read VREG_2V7 and SCL | RESET falls: rank 2 path. |
| 4. Repeat 2-3 with the programming jig unplugged | Jig wiring contribution. |
| 5. IPA clean around R13, the via at (8.63, 20.218) and the QFN edge; dry; repeat 1-2 | Recovery after cleaning: contamination (rank 1). |
| 6. Rework (owner audit, needs explicit permission): R21 to 0 Ohm strap, remove R15/R16, ground SCL/SDA; then retry a 15 V source with Board L disconnected, then connected | Holding 15 V with RESET hard-grounded confirms a RESET-path cause. Still failing points to U1 damage (rank 3) or NVM (rank 5). |
| 7. Before any of the above that changes state: dump and retain the 40-byte NVM image | Closes the rank-5 evidence gap. |

## What the common STUSB4500 block must not inherit

1. RESET hard-tied to GND by a short, dedicated connection (or a 0 Ohm strap adjacent to the pin); no RESET routing under resistors or near any VBUS/DISCH/VBUS_VS_DISCH copper; keep-out at least to the HV clearance class used for VBUS nets.
2. RESET not on a bare pogo pad. If a programming-time reset is wanted, put it behind a series resistor on the jig side and label the pad correctly on silk.
3. I2C pull-ups on the programmer rail (jig side), not on VREG_2V7.
4. VDD clamp that guarantees <= 28 V at the clamp current that the input protection can deliver (SMAJ20A does not).
5. Retained NVM dump per unit (before and after programming) and a power-cycle readback.
6. A hardware voltage window downstream of VBUS_EN_SNK that is independent of the NVM image.
7. Silk audit against nets for every test pad (#143).
