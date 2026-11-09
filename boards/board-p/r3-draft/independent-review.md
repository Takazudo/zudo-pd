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

## 2026-11-10 JST corrective implementation disposition

This follow-up preserves the November 8 findings above. It records implementation
and executed native evidence; it does not turn the desk review into physical
qualification or supplier acceptance. First corrective PCB SHA-256:
`7b44efc3fa93df28f14fcef62123642a659e4246bf2bad7011f0799d3681cef6`.
Source/tool/report hashes are in `native-drc-receipt.json` and
`layout-correction-check.json`; fresh-builder replay evidence is retained in
`native-full-builder-replay-20261110.json`.

| Finding | Current disposition |
| --- | --- |
| R1 | Four 0.50/0.20 mm thermal vias inside the actual rectangular U2 exposed pad, connected through B.Cu GND. The contacted B polygons total about 598.263 mm² and join through the common F.Cu exposed pad. Native clearance/connectivity passed. Stencil/via-process acceptance and installed thermal resistance remain open. |
| R2 | Four drain vias and 22.640 mm² of connected B.Cu VBUS_OUT copper added for Q1. The 5 A contract is unchanged. This is geometry improvement, not the datasheet's 1 in²/2 oz thermal reference or a measured current rating. |
| R3 | Three drain vias and 3.137 mm² of connected B.Cu EF_IN copper added for Q3. The modest area is reported explicitly; no installed thermal rating is inferred. |
| R4 | C30 is at (19.40, 24.25), F.Cu, 180°; C34 at (18.15, 24.75), B.Cu, 0°. Native pad distances are 2.866/1.602 mm. Planar supply paths are 3.237/2.382 mm with 0/1 via transitions; direct cap-to-return-via tracks are 0.900/0.986 mm. Ordinary via-opening separation is at least 0.203 mm. C30's 3.0 mm proximity target is an implementation constraint, not a manufacturer limit; actual paths and returns are separately bounded. |
| R5 | Unchanged. Turn-off/undershoot behavior at U2 OUT still needs the T7 physical sheet; NOT RUN. |
| R6 | The Q1 role and TPS16630 r3 configuration facts were refreshed through their component owners on November 9. The old divider and r2-layout descriptions are superseded. Native/thermal qualification is not inferred from that evidence cleanup. |
| R7 | Conditional desk SOA result remains conditional. T3 physical acceptance is NOT RUN. |
| R8 | D12 is unchanged; the native pad-center distance is 0.047 mm. The earlier 3.047 report value included a 3 mm bottom-side heuristic penalty, not physical distance. The generator now reports actual native distance. |

All four retained default routing seeds (12/14/16/20) closed their signal routes;
seed 12 was selected. Two fresh placement/spec/library builds followed by saved
validated routes and fills, plus a third replay through the owned files, yielded
byte-identical final PCB bytes. No heuristic placement search was used. Native
router geometry was compared against the completed default-routing input.

Pinned KiCad 10.0.6 on the selected Mac's Docker path reports zero errors and
zero unconnected items. The only parity exceptions are mechanical MH1–MH3.
The pre-artwork candidate had 123 warnings; two one-layer vias are functional
annular junctions, not removable dead ends. Its functional probe artwork was
then reviewed separately, including the inherited J3 VDD/RST mismatch with
actual VBUS_IN/GND contacts. The final artwork disposition follows below.

The conditioned 5 A I²R case is 1.325 W for U2, 0.750 W for Q1 and 0.585 W for
Q3, with explicitly named resistance/temperature assumptions. Installed thermal
resistance is UNKNOWN and bench thermal results are NOT RUN. Thermal via/paste
process choice, shared Q1/Q3 land/stencil adaptations and the broader PD20
interface/NVM/component gates remain separate pre-order obligations. No lower
current ceiling, component substitution or unresolved-margin acceptance is
adopted by this implementation.

## November 10 final artwork follow-up

The intermediate contact-artwork PCB was `76ff61f0487add2901168d5d684791a988fe03801012734057c20907dd8bd417`.
The parent independently reviewed its native front/back artwork images before
adoption. Front contact ordinals and indexed reverse-side role maps restore
J3.4 VBUS/J3.5 GND and meet the retained 1.0 mm/.15 mm supplier text guidance.
The exact 30-object artwork delta preserves all filled copper, pads, component
geometry and electrical contracts. Native replay is byte-identical and
idempotent; a wrong-net negative control fails. Actual final DRC/parity and
R1–R4 geometry verification passed with current source hashes.

There are 105 warnings: 2 functional one-layer annular junctions, 3 mechanical
library-availability findings, 2 specifically reviewed J2/J3 artwork-library
mismatches, 66 silk overlaps and 32 silk-over-copper findings. None involve
the corrected functional artwork. The earlier 123-warning inventory above
records the pre-artwork candidate. `layout-corrections.md` provides the current
dispositions and exact fabrication clearances. Supplier printed-legibility,
tenting and placement previews remain unobserved; no broad silk waiver, physical
thermal rating or order-readiness claim follows. R5/R7 and all named electrical,
land/stencil, via-process and physical gates remain open.

## November 10 final polarity follow-up

Current PCB SHA-256: `56cbe0ab48b3bd25b6bab4223e3826ef437e3b972474b15481c5b86b7e889348`. Independent
per-object review of the intermediate 76ff candidate identified two functional
cue conflicts. Q3/D13 reference fields now remain on Fab rather than obscuring
D5 pin1 and D8 cathode bars. D5 has a single printable corner cue tied to its
actual pin1 and checked against exact body maxima and mask openings; the tiny
duplicate is retained on comments only. The parent reviewed the native renders
and corner crop before adoption.

The owned result matches the four-object-only ignored prototype exactly. Native
DRC reports zero errors/opens and only mechanical MH1–MH3 parity exceptions.
The 95 warnings comprise 2 annular-junction vias, 3 mechanical library findings,
3 reviewed artwork/library mismatches, 57 silk overlaps and 30 silk-over-copper
findings. No corrected functional artwork has a native finding. Final geometry
verification and deterministic/idempotent native replay passed; project sidecars
remain byte-identical and incorrect J3/D5 net assignments are rejected. All
electrical, thermal, supplier-process and physical holds above remain open.
Prior 76ff evidence is preserved by the dated polarity-artwork history manifest.
