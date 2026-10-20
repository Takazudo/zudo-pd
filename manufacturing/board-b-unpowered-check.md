# Board B unpowered visual and continuity check (D1 plan, not authorized)

## 1. Purpose and authorization status

**Status: proposal only. Not authorized.** This is step D1 of [`as-built-and-controller.md`](as-built-and-controller.md) §2.4, written for the owner to approve or reject. Nothing here has been done and nothing is measured. Board B stays an unvalidated draft. Evidence classes are as defined in `as-built-and-controller.md`.

Purpose: confirm that the one built renewal Board B matches package state **S3** (`f25194f`, [`releases/corner-support-review/board-b/`](releases/corner-support-review/board-b/)) beyond its BOM. The open items are copper and silk identity, LED2 placement, and polarity, plus the absence of rail-to-GND shorts.

Limits, if approved:

- Handling and visual inspection only. No power, no rework, no reflow, no part removal, no cable or module attachment.
- The only meter modes allowed are continuity and resistance. **A DMM in resistance or continuity mode drives a small test voltage and current through the circuit.** That source forward-biases junctions, charges electrolytics and can faintly light an LED. The open-circuit test voltage depends on the meter and is UNAV; record it from the meter's manual. **The owner decides whether that test voltage is acceptable.** Diode-test mode and any external source are excluded.

Sources (all at HEAD; nothing under `manufacturing/releases/` has changed since `f25194f`):

| Tag | Path |
|---|---|
| BOM, CPL | `releases/corner-support-review/board-b/bom.csv`, `cpl.csv` (designator sets equal; P1/TP3–TP5 are bare copper per `excluded.csv`) |
| NET | `releases/corner-support-review/board-b/raw/board-b.net` (S3 export netlist) |
| PCB | `boards/board-b/board-b.kicad_pcb`. It differs from the package's `source/board-b.kicad_pcb` only in 3D-model path prefixes. Every CPL position and rotation equals the PCB footprint placement |
| GBR | `releases/corner-support-review/board-b/board-b-gerbers.zip` (byte-identical to `gerbers/`); S2 comparison from `git show aeeff56:` of the same zip |
| SPEC | `scripts/schgen/board_b_spec.py` |

Coordinates are in the CPL/Gerber frame in millimetres, viewed from the component (front) face. The origin is the lower-left corner of the 110 × 85 board; J6/J7 sit on the left edge, J10/J11 on the low-y edge and P1 on the high-y edge (y = 85 − KiCad y). Board B mounts front face down (`CLAUDE.md`), so view it component side up.

## 2. Identity checks (S3 vs S1/S2)

| # | Check | Expected for S3 | S1/S2 would show | Source / class |
|---|---|---|---|---|
| I1 | R26, R27, R28 fitted (0603) at (82.6, 32.7) 90°, (82.6, 36.1) 90°, (81.85, 38.8) 0° | Three resistors on pads | No pads at these positions (the S2 F_Cu, F_Mask and F_Paste have no flashes in x 80–84, y 30–40) | CPL; GBR (S3 and S2) |
| I2 | R26–R28 body marking | Record what is printed. Values: 8.2 kΩ C861589, 680 Ω C861519, 1 kΩ C110776 | — | BOM; marking UNAV |
| I3 | U6, U7 top marking | Record verbatim. LT1963AEQ#TRPBF C459702 | Same die as S1 `#PBF` (`component-renewal-ldos/SKILL.md`), so the marking is **not expected to separate S1 from S3** | BOM; marking code UNAV |
| I4 | U8 top marking | Record verbatim. LT3015EQ#PBF C666306, adjustable | Fixed LT3015EQ-12 C666307 | BOM; marking code UNAV, so use I5 |
| I5 | U8 pin 4 (ADJ) to pin 5 (OUT), resistance mode | **Not continuous.** They connect through R26 + R27 plus in-circuit parallel paths; reading UNAV, to be recorded | S1/S2 netlists put U8.4 on `Net-(U8-OUT)`, which would read as continuity | NET; SPEC diff in `f385f20` |
| I6 | LED2 silk mark at (63.0, 8.5) | Triangle apex and chamfered outline end point toward **+y**, to the pad at (63.0, 9.25) | S2 silk points toward −y, to the pad at (63.0, 7.75) | GBR F_Silkscreen, S3 vs S2 |
| I7 | LED2 body polarity vs CPL 270° | Body cathode on the pad at (63.0, 9.25). That pad is footprint pad 1 (cathode, per the `pinmap-c2289` LED0603-RD pin map) and is on GND. The anode pad at 7.75 goes through R7 to U6 OUT | CPL 90° in S1/S2 places the cathode at 7.75 | CPL; PCB; NET; `component-project-passives/pin-map.json` (PA) |

For I7, the meaning of the LED body's cathode marking is UNAV: the pin map was reviewed against the LCSC/EasyEDA library and the JLCPCB preview, not the KENTO datasheet. A relational check is to compare LED2's body mark against LED3's. Same-family marking is assumed (PA). LED3's cathode should be on its GND pad at (63.0, 4.35), which faces −y. LED2's cathode should be on its GND pad at 9.25, which faces +y. The two marks should therefore point in opposite directions.

**Desk discrepancy (schematic labels only).** The S3 schematic places `zudo-pd:KT-0603YG`, and both that symbol in `symbols/zudo-pd.kicad_sym` and the copy in `boards/board-b/board-b.kicad_sch` name pin 1 `A` and pin 2 `K`. As a result, NET lists `LED2.1(A)` on GND and `LED2.2(K)` on the R7 net.

This contradicts two sources that both make pin 1 the cathode on GND: the owner pin map, which was reviewed against the differently named symbol `YLED0603YG`, and the SPEC comment. The copper, the footprint mark and the CPL 270° all follow the pin map, so the as-built check above tests the pin map. The physical result rests on the LCSC LED0603-RD convention; the pin map was not checked against the KENTO datasheet (PA). `component-project-passives/SKILL.md` line 37 also still says `YLED0603YG` pin 1 = anode, contradicting the corrected fact. The symbol pin names and that line remain open record fixes and are not changed here.

## 3. Orientation and polarity of polarized parts

| Ref | Expected (from source) | How to check | Source / class |
|---|---|---|---|
| U2 AP63201 TSOT-23-6, rot 180 | Pin 1 (FB) at (41.80, 70.95) | Package pin-1 mark at the silk dot by that pin | CPL; PCB; `component-ap63201-power-stage/pin-map.json` (G) |
| U3, U4 LM2596S-ADJ TO-263-5, rot 0 | Leads on the +x side, pin 1 at the lowest y (28.16, 45.60 / 21.60); the tab faces −x | Lead row and tab side; pin 1 at the silk dot. The U4 tab is on −14.145 V PRE, not GND | PCB; NET; `component-lm2596s-adj-c347423/pin-map.json` (G) |
| U6, U7 LT1963A Q, rot 0 | Pin 1 SHDN at (79.72, 65.60) / (82.72, 47.60); pin 3 and the tab are GND | Lead row on +x, pin 1 at the lowest y | PCB; `component-renewal-ldos` pin map (G-U, mirror datasheet) |
| U8 LT3015 Q, rot 0 | Pin 1 SHDN at (82.72, 21.60); pin 2 GND; **the tab is IN (−14.145 V PRE)** | As U6. The tab must not touch any GND hardware | PCB; NET; `component-renewal-ldos` (G-U) |
| D2 SS34 (SMA) | Cathode pad 1 at (33.75, 47.80), on `Net-(D2-K)` (U3.2 / L2.1) | Body band toward the silk bar at y = 49.12 | PCB; GBR; `component-ss34-c8678` (G) |
| D3 SDT5A60SA | Cathode pad 1 at (35.00, 22.00), on `Net-(D3-K)` (U4.2 / L3.1) | **The S3 silk has no cathode mark** (outline with end ticks only at the pad-1 end; no band), so the body band must be on the pad continuous with U4 pin 2 | PCB; GBR; `component-renewal-input-protection` (G) |
| TVS1 / TVS2 (SMAJ15A / SMAJ6.5A) | Cathode pad 1 at (108, 65.17) on +12 V rail / (106, 45.67) on +5 V rail | Band toward the silk triangle and bar on the pad-1 end | PCB; NET; `component-smaj15a-c571368` (G); `component-sd05-c502527` (G for the band end; the C87267 pin-map record still says "unplaced candidate") |
| TVS3 SMAJ15A | **Cathode on GND** at (106, 22.97); anode on −12 V rail | Same; its band faces −y like TVS1/TVS2, but it sits on GND | SPEC (locked orientation); NET (G) |
| LED2 / LED3 / LED4 | Cathodes at (63, 9.25) GND / (63, 4.35) GND / (63, 0.95) through R9 to U8 OUT | See I6/I7 | PCB; `component-project-passives` (PA) |
| C40, C41, C42 25SVPF47M | Pin 1 = + on U6 OUT, U7 OUT and GND respectively; C42's − is on U8 OUT | Body polarity mark vs pad 1, at the chamfered silk end | NET; `component-panasonic-25svpf47m-c136280` (G) |
| C4, C5, C7, C9, C11, C12, C21–C25 (Al electrolytic) | In every case pad 1 is on the more positive net (for example C9 + on +15 V, − on −14.145 V; C11/C12/C24 + on GND). Pad 1 is the chamfered silk end | Body − stripe on the pad-2 end | NET; PCB; pin maps say "polarity not independently confirmed" (PA) |
| J5 PM254V 1×6 female | Pin 1 (+15 V) at (37.20, 66.45), pin 6 at 53.75 | Pin 1 end of the housing; mating orientation is an open bench gate | PCB; `component-xfcn-board-headers` (G) |
| J6, J7 WJ500V | Pin 1 at the lower y (34.46 / 21.46); wire entries face −x (left edge) | Entry openings face the left edge | PCB; `component-kangnex-wj500v-5-08-2p-c8465` (G-U) |
| J10, J11 DW254P | Pin 1 (−12 V) at (50.29, 13.50) / (90.39, 13.50), the +x end; "−12V / RED" silk beside it | Shroud key and pin-1 triangle vs that end. EasyEDA contact numbering is an open physical item | PCB; `component-dealon-dw254p-2x8-l0-c4749189` (G-U) |

## 4. Unpowered resistance checks (meter only, if approved)

"Not a short" means the continuity beeper stays silent and the reading is clearly different from the probes-shorted reading. Readings drift as electrolytics charge, so record both the first and the settled value. Put the meter's positive lead on the more positive net (GND for the −12 V and −14.145 V checks). Junctions such as TVS3 conduct in one polarity, so a low reading with the leads reversed is not a short. Record which lead was where. No numeric expected resistance is available; each value is UNAV and is recorded, not judged against a number. Expected net membership comes from NET.

| # | Probe A | Probe B | Expected |
|---|---|---|---|
| R1 | J6.1 (GND) | J6.2 (−12 V rail) | Not a short |
| R2 | J6.1 | J7.1 (+5 V rail) | Not a short |
| R3 | J6.1 | J7.2 (+12 V rail) | Not a short |
| R4 | J7.1 / J7.2 / J6.2, each pair | — | Not a short (rail to rail) |
| R5 | J10 and J11 pins 1–2 / 3–8 / 9–10 / 11–12 | J6.2 / J6.1 / J7.2 / J7.1 | Continuity within each group |
| R6 | J10 or J11 pins 13–14 (CV), 15–16 (GATE) | GND and each rail; CV vs GATE | Not a short. J10.13 to J11.13 and J10.15 to J11.15 are continuous (shared bus) |
| R7 | J5.1/J5.2 (+15 V INPUT) | J5.5/J5.6 (GND) | Not a short |
| R8 | TP3 (+13.44 V PRE), TP4 (+6.519 V PRE), TP5 (−14.145 V PRE) | P1.3 (GND) | Not a short |
| R9 | U6 tab, U7 tab / U8 tab | J6.1 | Continuity / **not a short** (the U8 tab is on −14.145 V PRE, continuous with TP5) |
| R10 | J5.3 / J5.4 / J5.5 | P1.1 ATT / P1.2 PDOK / P1.3 GND | Continuity; P1.4 is NC |

## 5. Label check (front and back silk vs nets)

All label text and positions below come from the PCB `gr_text` entries. The Gerber silk strokes were not rendered to text in this desk review.

| Label | Layer, position | Pin there | Net (NET) | Match |
|---|---|---|---|---|
| GND / −12V | F.SilkS (0.8, 34.46) / (0.8, 39.54) | J6.1 / J6.2 | GND / −12V rail | Yes |
| +5V / +12V | F.SilkS (0.8, 21.46) / (0.8, 26.54) | J7.1 / J7.2 | +5V rail / +12V rail | Yes |
| GND, −12V, +5V, +12V | B.SilkS (11.6, 34.5), (12.2, 39.0), (11.8, 21.2), (12.2, 26.6), `justify mirror` | J6.1, J6.2, J7.1, J7.2 | as above | Yes |
| +12 / +5 / −12 | F.SilkS (65.8, 8.5 / 5.1 / 1.7) | LED2 / LED3 / LED4 | R7 from U6 OUT / R8 from U7 OUT / R9 from U8 OUT | Yes |
| −12V / RED | F.SilkS (53.5, 14.0), (93, 14.6) | J10.1, J11.1 | −12V rail | Yes |
| TP3 13.44V / TP4 6.519V / TP5 −14.145V | F.SilkS (88, 83.0) | TP3 x 66.35, TP4 68.89, TP5 71.43 | matching PRE nets | Yes (order) |

The back labels "+12V : 1.2A", "−12V : 0.8A" and "+5V : 0.5A" restate design budgets (PA), not ratings. On the physical board, confirm that each label is legible and sits beside the pin it names.

## 6. Record sheet (fill in on the board; nothing is pre-filled)

```
Date / operator / meter model / meter test voltage (from manual):
Approval reference (issue comment id):
Board marking or serial (if any):
I1 R26 / R27 / R28 present (Y/N):          I2 markings:
I3 U6 marking:              U7 marking:              I4 U8 marking:
I5 U8.4–U8.5 reading (first / settled):
I6 LED2 silk direction (+y / −y):          I7 LED2 body cathode pad (9.25 / 7.75 / unclear):
LED3 body cathode pad (4.35 / 5.85):        LED4 body cathode pad (0.95 / 2.45):
§3 each row: OK / NOT OK / UNCLEAR + note:
§4 R1..R10: reading (first / settled), beeper Y/N:
§5 each label: legible Y/N, beside named pin Y/N:
Photos taken (file names):
Deviations, stops, open questions:
```

## 7. What a pass does and does not establish

A pass means that this one Board B shows the S3 copper/silk discriminators (I1, I5, I6), the expected placement of polarized parts, and no rail-to-GND or rail-to-rail short at meter test levels. It narrows the open identity items in §1.1 of the as-built page.

It does **not** establish:

- solder joint quality, hidden shorts under parts or regulator behaviour;
- output voltages, current budgets, thermal behaviour or transient behaviour;
- cable or key polarity (J10/J11 with a real ribbon; J5 mating);
- the HC-11 or adhesive-leg fit;
- any production-file hash.

It does not qualify, validate or release the board, and it authorizes **no energizing**. D5 still needs its own approval and a verified source board.
