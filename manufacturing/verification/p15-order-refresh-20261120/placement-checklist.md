# P15 r1 placement checklist (JLC placement preview)

Source: fixed package `manufacturing/releases/corner-support-review/board-p15/` (manifest `git_base` `3b9821b`).
`bom.csv` `23d6e290…`, `cpl.csv` `a9116d1b…`. Pad nets and positions are read from
`boards/board-p15/board-p15-draft.kicad_pcb` (`97acc5f4…`, equal to the package's fabrication source lock). Prepared
2026-11-20 (UTC) as desk evidence. JLC places parts with its own library footprints, so this checklist does not prove
the placed orientation. The JLC preview is the check that counts.

Coordinates: KiCad board mm, with the origin at the top-left and Y increasing downward. The CPL uses the same X and
negates Y (`Mid Y = −y`), with a common drill/place origin at (0, 0). In a top view of the board, J1 (USB-C) sits on
the top edge (y≈0) and JOUT1 on the bottom edge (y≈38). All parts are on the top side. There are no bottom placements.

## BOM lines (14 lines, 23 placements per board)

| LCSC | Part (BOM comment) | Designators | Per board | For 2 boards |
| --- | --- | --- | ---: | ---: |
| C21189 | 0603WAF0000T5E (0 Ω) | R19, R20, R21 | 3 | 6 |
| C21190 | 0603WAF1001T5E (1 kΩ) | R29 | 1 | 2 |
| C25803 | 0603WAF1003T5E (100 kΩ) | R11, R22, R23 | 3 | 6 |
| C22807 | 0603WAF1503T5E (150 kΩ) | R12 | 1 | 2 |
| C23179 | 0603WAF4700T5E (470 Ω) | R13, R14, R30 | 3 | 6 |
| C347476 | AO3401A | Q1 | 1 | 2 |
| C192739 | BZT52C18-7-F | D9 | 1 | 2 |
| C14663 | CC0603KRX7R9BB104 | C2, C35 | 2 | 4 |
| C15849 | CL10A105KB8NNNC | C30, C34, C38 | 3 | 6 |
| C13585 | CL31A106KBHNNNE (ceramic, non-polar) | C1 | 1 | 2 |
| C492405 | PZ254V-11-06P (through-hole) | JOUT1 | 1 | 2 |
| C74561 | SMAJ16A | D5 | 1 | 2 |
| C2678061 | STUSB4500QTR | U1 | 1 | 2 |
| C283540 | TYPE-C-31-M-17 | J1 | 1 | 2 |

These parts are not placed and must not appear in the JLC BOM: D6, D7 (C85382) and R17, R18 (C23186) are
intentional DNP. J2 and J3 are bare copper pads with no physical part. The source is `excluded.csv`.

## Oriented parts: CPL row, pad nets and what the preview must show

| Ref | Part | CPL (X, Y, side, rot) | Pad 1 / key pads (KiCad abs mm, net) | Preview must show |
| --- | --- | --- | --- | --- |
| **D5** | SMAJ16A C74561, SMA | 22.250, −10.080, Top, 0 | pad 1 (20.450, 10.080) **VBUS_IN** = cathode; pad 2 (24.050, 10.080) GND | **Cathode stripe on the left pad (smaller X, VBUS_IN)** |
| **D9** | BZT52C18-7-F C192739, SOD-123 | 18.900, −24.950, Top, 0 | pad 1 (17.325, 24.950) **VDD_LOC** = cathode; pad 2 (20.475, 24.950) GND | **Cathode band on the left pad (smaller X, VDD_LOC)** |
| U1 | STUSB4500QTR C2678061, QFN-24 4×4 + EP | 11.728, −23.288, Top, 180 | pad 1 (12.978, 21.288) CC1DB; silk pin-1 dot at (13.728, 21.288); EP pad 25 GND | Pin-1 mark at the **upper-right** corner (toward J1, larger X). Pads 1–6 run along the J1-side edge from right to left |
| Q1 | AO3401A C347476, SOT-23 | 18.586, −13.636, Top, 90 | pad 1 G (19.536, 12.486) Q1_G; pad 2 S (17.636, 12.486) VBUS_IN; pad 3 D (18.586, 14.786) VBUS_OUT | Two-lead side toward J1 (gate on the right, source on the left); the single drain lead faces away from J1 |
| J1 | TYPE-C-31-M-17 C283540 | 13.506, −5.000, Top, 180 | signal row at y = 7.050 (pad 1 GND x = 16.256 … pad 6 GND x = 10.756; VBUS_IN on pads 2/5, CC1 pad 3, CC2 pad 4); 4 shell tabs GND | Receptacle opening faces the **board edge (y≈0)**, flush with the outline; signal pins point into the board |
| JOUT1 | PZ254V-11-06P C492405, 1×6 vertical header, THT | 12.900, −37.700, Top, 0 | pin 1 (6.550, 37.700) VBUS_OUT; 2 VBUS_OUT; 3 ATT; 4 PDOK; 5 GND; 6 GND (pin 6 at x = 19.250) | Header on the **top side**, pins along X; pin 1 at the **left** (smaller X). Through-hole assembly is needed |

The local cross-check in `manufacturing/readiness/p15-first-placement-orientation.json` found D5 and D9 cathode, pad 1
and net in agreement (PASS). The 2026-11-20 re-read of the PCB agrees: D5 has its F.Fab cathode bar at local
x = −1.75 (pad 1 side). D9 has its F.SilkS double cathode bar at local x = −0.97/−0.83 and a pin-1 dot at
(−1.85, 0.9). Both footprints are at 0°, so pad 1 is at the smaller absolute X.

All resistors (R11–R14, R19–R23, R29, R30) and the ceramic capacitors (C1, C2, C30, C34, C35, C38) are non-polar.
Check only their position and that they are not swapped.

## If the preview disagrees

- D5 or D9 reversed: **stop**. Rotate that part by 180° in JLC's placement tool, so the stripe or band sits on the
  VBUS_IN or VDD_LOC pad. Do not edit the frozen package files.
- U1 pin 1, the Q1 lead pattern, the J1 mouth direction or the JOUT1 side or pin 1 is wrong: correct it in JLC's tool
  and save a screenshot. If it cannot be corrected, do not place the order.
- Record the D5 and D9 preview screenshots as order evidence (see `doc/src/content/docs/project/current-state.md`, next
  action 1).
