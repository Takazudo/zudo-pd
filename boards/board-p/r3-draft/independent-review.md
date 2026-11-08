# Board P r3: independent desk review, 2026-11-08

**Unvalidated draft. This is a desk and native-tool review, not validation.** Reviewed file:
`boards/board-p/board-p.kicad_pcb` at `main` `6b08236`, SHA-256
`67b0e0960c8d5590dec0efc6de22218d3f7a21fa098abcaffdd57433f3e0058d`. The reviewer did not write the layout. Tracking:
Takazudo/zudo-pd#231.

## Native DRC reproduces the recorded result: 0 errors, 0 unconnected

Pinned image `kicad/kicad@sha256:18693567…` reports `kicad-cli version` 10.0.6.
`kicad-cli pcb drc --schematic-parity --format json --severity-all` gives 0 errors and 0 unconnected items. Parity
shows only `extra_footprint` ×3 (MH1–MH3). Warnings: 69 silk_overlap, 34 silk_over_copper, 14 text_height,
2 silk_edge_clearance, 3 lib_footprint_issues, 2 via_dangling, 1 track_dangling. These match
`manufacturing/pd20-status.md`. Outline 27.05 × 40.05 mm, two layers of 0.035 mm copper.

The geometry below comes from a pcbnew script run in the same image (filled-zone areas, pad-to-pad centre distances,
vias inside pads).

## Main power path is poured, single layer

J1 VBUS → D5 → Q3 → U2 → C3/Q1 → JOUT1 lands on F.Cu pours on every main pad: VBUS_IN 23.8 mm², EF_IN 15.3 mm²,
VBUS_P 56.4 mm², VBUS_OUT 57.1 mm². None of these nets has a B.Cu pour. The 0.4 mm tracks on VBUS_IN and VBUS_P are
feeds to small parts, not the load path.

## Findings

Board P current used below: about 3.2 A at the B20 limiter maximum. This assumes 51.7 W OSC let-through and 80 %
overall efficiency at 20 V. The B20 calculator does not compute this figure. The 5 A PDO is the contract ceiling.

| # | Severity | Finding | Evidence | Proposed action |
|---|---|---|---|---|
| R1 | Major | U2 TPS16630 PowerPAD (pin 21) has **one** via. The datasheet's RθJA 32.2 °C/W is a JEDEC board; SLVSET9G layout guidance puts the PAD on a GND plane, with other layers added for higher current. At 3.2 A and RON maximum 53 mΩ the loss is 0.54 W. The installed θJA is UNKNOWN. | `ep_vias U2.21 = 1`; SLVSET9G section 6.4 and layout guidelines | Add a thermal-via array under the PAD into the B.Cu GND pour, following TI's PWP example, in the r3 builder. Then rerun native DRC |
| R2 | Major at 5 A, watch at 3.2 A | Q1 DMP3036SFG-7 sits on 56 + 57 mm² of 1 oz F.Cu with **no** vias in its drain pad. Its rated current and the 55 °C/W figure need 1 in² (645 mm²) of 2 oz copper. At 20 V the clamp holds VGS near −10.4 V: 20 mΩ maximum at 25 °C, about 30 mΩ hot. That gives 0.31 W at 3.2 A, a rise of about 42 K on the 137 °C/W minimum-pad figure, and 0.75 W (about 103 K) at 5 A. | Zone areas; `ep_vias Q1.9 = 0`; DS37038 thermal table | Add drain-pad vias into a B.Cu VBUS_OUT island, or record a current ceiling below 5 A. Bench T2 adds a thermocouple on Q1 (already listed) |
| R3 | Minor | Q3 CSD18543Q3A drain pad (EF_IN) has no vias. Loss is about 0.24 W at 3.2 A (15.6 mΩ at VGS 4.5 V, hot ×1.5). | `ep_vias Q3.9 = 0` | Same treatment as R2 if R2 is laid out |
| R4 | Minor | STUSB4500 regulator capacitors sit away from their pins: C30 (VREG_2V7) 5.4 mm, C34 (VREG_1V2) 4.1 mm, pad centre to pad centre. C38 (VDD) is 1.5 mm. | Pin-distance table in the review script | Pull C30 and C34 next to U1 pins 23 and 21 when the placement is next searched |
| R5 | Observation | C3 (100 µF bulk on VBUS_P) is 10.7 mm from U2 OUT and 15.1 mm from Q1 source. SLVSET9G recommends an output Schottky close to OUT/GND for inductive loads, and Board P has none. The cable to B20 is a short header, and C3 bounds the turn-off excursion. | Pin-distance table; SLVSET9G layout list | Bench T7 (fault latch) records VBUS_P undershoot at U2 OUT on a fast trip |
| R6 | Evidence hygiene | Two owner facts describe superseded states. `fact-c461081-board-p-role` still gives the old −2.0 V divider VGS at 5 V, which phase 6 replaced with R11/R12 = 150k/4.7k. `fact-c1849461-board-p-config` still says the PCB "carries the r2 TPS26630 layout"; the r3 PCB is routed. | `.claude/skills/component-diodes-dmp3036sfg-7/facts.json`, `.claude/skills/component-tps16630pwpr/facts.json` | Refresh both conditions through the component-spec-audit workflow when evidence integration opens |
| R7 | Pass (desk) | Q1 turn-on into the B20 VIN bank stays inside the Fig. 12 SOA by about 2× at 25 °C (1.6× at 60 °C). | `manufacturing/pd20-evidence-research.md` | Bench T3 |
| R8 | Pass | Clamp and strap parts sit at their pins: D12 at U1.9 (0.05 mm), D9 at VDD 1.8 mm, D10 at VBUS_VS_DISCH 2.0 mm, D11 at VBEN 2.5 mm, R21 (RESET) 1.8 mm, R26 (ILIM) 2.0 mm, C5 (dVdT) 0.8 mm. D5 TVS is 4.0 mm from the J1 VBUS pad. | Pin-distance table | None |

## Not run

- **Layout changes for R1–R4: NOT RUN.** Each one changes the routed draft, which `scripts/pcb/board-p-r3-draft/run.sh`
  regenerates from search, router and pour stages. The changes need an owner-approved builder change, then a full
  rebuild and native DRC. This review does not edit the PCB.
- **Thermal simulation: NOT RUN.** No field solver is available. The figures above are datasheet θJA arithmetic.
- **Surge, inrush and fault waveforms: NOT RUN** (bench T3, T7 and T8).
