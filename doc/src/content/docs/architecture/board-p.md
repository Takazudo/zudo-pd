---
title: Board P — Reusable USB-PD Input
sidebar_position: 2
description: The independent 27 × 40 mm input module, its six-pin interface and its unverified configuration boundary.
---

Board P is a two-layer, 27 × 40 × 1.6 mm USB-PD input board. It retains a routed
prototype layout and the STUSB4500QTR controller, with project-local component
records and a generated schematic at `boards/board-p/board-p.kicad_sch`.
The source spec is `scripts/schgen/board_p_spec.py`.

## A 20 V / 5 A revision is decided; only its draft schematic exists

On 2026-10-31 at 11:11Z the user chose, on a decision card
(`cmsg_01Pv35emdXEU6gCRF3teSpo23Q1CUhqDN2ebZaArfgF1Ru`):

- D3-A: a PD revision to PDO2 20 V / 5 A with a 5 A e-marked cable;
- D5-1: no degraded mode, so a source is either accepted or refused.

The machine records are `dec-p-20v-revision`, `dec-p-20v-front-end-r2` and the Q1 proposal
`dec-p-20v-q1-5a` in
`scripts/schgen/decisions.json`. They supersede the 15 V-only target **for this revision
only**.

A second card on 2026-10-31 at 15:39Z made the STUSB4500 the common controller block for the
LED lamp and zudo-pd, kept a single lineup (this revision becomes the new zudo-pd; superseded below), replaced the
TPS26630 front end with TPS16630PWPR + LM74700-Q1 + Q3, and accepted per-unit NVM programming
(`dec-common-controller-block`, `dec-single-lineup`, `dec-p-20v-front-end-r3`,
`dec-nvm-per-unit-programming`). Phase 8 moved the inventory-bound `board_p_spec.py` to that r3
front end (`dec-p-front-end-r3-migration`); the separate r3 draft spec is retired. TPS26630RGER and
the 10 kΩ R21 remain as REJECTED candidate records. The Board P PCB still carries the r2 layout
and has not been re-synchronised.

## The 15 V zudo-pd and the 20 V / 5 A unit are separate products

On 2026-11-01 at 04:59Z the user chose separate products on a decision card
(`dec-separate-products`, which supersedes `dec-single-lineup`):

- the current zudo-pd, Board P 15 V as built with the current Board B, continues as its own product;
- the Board P r3 draft with the B20 switcher-direct Board B becomes a separate 20 V / 5 A unit
  oriented to the OSC;
- the STUSB4500 controller block stays common to both.

`board_p_spec.py` and the generated schematic keep describing the r3 draft. The 15 V product is
defined by the as-built `boards/board-p/board-p.kicad_pcb` and the `corner-support-review` package.
On 2026-11-01 the coordinator chose the RESET subset of the common block for the 15 V board
(`dec-p15-reset-subset`). The changes are:

- R21 becomes a 0 Ω strap at U1.6;
- J2.4 becomes NC;
- the I2C pull-ups move to the programming jig.

Its spec is `scripts/schgen/board_p15_spec.py`, which generates `boards/board-p15/board-p15.kicad_sch`. A first
stage of that spec matched the as-built netlist pin for pin before the change. The unvalidated draft PCB is
`boards/board-p15/board-p15-draft.kicad_pcb`. In it, RESET copper is at least 1.353 mm from VBUS-class copper on
the same layer; the as-built board has 0.222 mm.

Phase 17 added three parts to the 15 V draft, all on the top side, without moving any other part:

- R22/R23, 100 kΩ pull-downs on SCL and SDA (`dec-p15-i2c-pulldowns`);
- the r3 VDD feed, R29 1 kΩ + R30 470 Ω from VBUS_IN, with the D9 BZT52C18 clamp at U1.24
  (`dec-p15-vdd-local-clamp`). The desk margin to the 28 V VDD limit becomes +7.198 V at the 28.6 V hot estimate,
  up from −0.6 V.

The other r3 local clamps are not taken. Programming uses jig pull-ups and a full power cycle:
[Board P15 NVM Programming](/docs/architecture/board-p15-programming/). The details are in
`boards/board-p15/README.md`.

The generated schematic and `board_p_spec.py` on the development branch now carry an
unvalidated draft:

| Ref | Part | Role |
|---|---|---|
| D5 | [TVS2200DRVR C523793](/docs/components/records/c523793/) | 22 V-standoff clamp on connector VBUS_IN |
| Q3 | [CSD18543Q3A C840100](/docs/components/records/c840100/) | Reverse-blocking N-FET: source on VBUS_IN (U3 ANODE), drain on EF_IN (U3 CATHODE, U2 IN), gate on EF_GATE |
| U3 / C37 | [LM74700QDBVRQ1 C2941042](/docs/components/records/c2941042/) / 1 µF C15849 | Ideal-diode controller driving Q3; EN tied to ANODE; C37 from VCAP to ANODE |
| U2 | [TPS16630PWPR C1849461](/docs/components/records/c1849461/) | eFuse from EF_IN to the protected node VBUS_P, ahead of every other part |
| R24 / R25 | 174k / 10k, 0.1 % | OVP, 21.60–22.56 V rising (22.67 V with 25 ppm/°C over 100 °C) |
| R22 / R23 | 11.5k / 4.02k, 0.1 % | UVLO, 4.53–4.73 V rising, 4.20–4.45 V falling |
| R26 | 4.02k, 0.1 % | I(OL) 4.185–4.815 A |
| C5 | 100 nF | dVdT ramp |
| C3 | 100 µF 50 V (80–120 µF) | Single protected-node bulk; C4 is removed |
| Q1 | [DMP3036SFG-7 C461081](/docs/components/records/c461081/) (proposed) | Output P-FET switch: source on VBUS_P, drain on VBUS_OUT, gate on Q1_G; replaces AO3401A |
| R11 / R12 | 150k C22807 / 4.7k C23162 (proposed) | Q1 gate divider: R11 VBUS_P to Q1_G, R12 Q1_G to VBEN (was 100k / 150k) |
| D8, D13 | [BZT52C11-7-F C92321](/docs/components/records/bzt52c11-c92321/) (proposed) | Q1 gate clamp and its redundant twin (phase 11): cathodes on VBUS_P, anodes on Q1_G |
| C36 / Q5 / R27 | 1 µF C15849 / [BSS138-7-F C40912](/docs/components/records/c40912/) / 150k C22807 (proposed) | Q1 Miller soft start: C36 VBUS_OUT to Q1_MX, Q5 body diode Q1_MX to Q1_G, R27 VBUS_P to Q1_MX |
| R14 / R28 / D10 | 2 × 1k C21190 / [BZT52C20-7-F C260890](/docs/components/records/c260890/) (proposed) | VBUS_VS_DISCH series resistance and local 20 V clamp on U1.18 |
| R29 / R30 / D9 / C38 | 1k C21190 + 470 Ω C23179 / [BZT52C18-7-F C192739](/docs/components/records/c192739/) / 1 µF C15849 (proposed) | STUSB4500 VDD feed: VBUS_P to VDD_LOC (U1.24) with an 18 V clamp and local cap |
| R13 / D12 | 4.7k C23162 / BZT52C18-7-F (proposed) | DISCH series resistance and clamp on U1.9 |
| Q6 / R31 / R32 / D11 | BSS138-7-F C40912 / 2 × 100k C25803 / BZT52C18-7-F (proposed) | VBUS_EN_SNK cascode: source on U1.16 (VBEN_PIN), drain on VBEN (R12), gate at VDD_LOC / 2 |

- MODE is left open, which selects latch-off. SHDN, IMON, FLT and PGOOD are open.
- R21 is a 0 Ω C21189 strap from RESET to GND. The I2C pull-ups R15/R16 are removed and
  move to the programming jig.
- Phase 9 (`dec-p-stusb-local-clamp`, proposed) takes the STUSB4500 high-voltage pins off
  VBUS_P. Each pin is fed through a series resistor, at milliamps, into a guaranteed zener
  clamp. VDD, VBUS_VS_DISCH, DISCH and VBUS_EN_SNK therefore no longer follow a VBUS_P
  surge. The CC pins are unchanged.
- U3 regulates Q3 as an ideal diode and turns it off on reverse current (V(AK REV)
  −17 to −2 mV). Its charge pump stops at 13.9 V maximum above ANODE, 6.1 V inside the
  Q3 ±20 V VGS rating; GATE to ANODE is 15 V absolute maximum. Reverse blocking is
  unmeasured.
- The rising UVLO threshold is now guaranteed at or above 4.5 V. The falling threshold,
  4.20–4.45 V, still sits below 4.5 V.
- One 100 µF part keeps the 5 V → 20 V transition inrush at the 30 V/ms PD slew ceiling
  to about 3.6 A, below the 4.185 A I(OL) minimum; the earlier 2 × 100 µF drew about 7.2 A.
  The slew ceiling is a project assumption. The estimated hot-unplug VBUS_P peak at
  80 µF is 25.1 V only on TYP I(SCP) and fast-trip figures and a 30 mΩ ESR assumption;
  at ESR 0.3–0.5 Ω it is 27.7–29.6 V, and at the 4.5 µs soft-short maximum it is 27.1 V.
  The only guaranteed bound on VBUS_P is the TVS2200 clamp, 28.0–28.35 V. With the local
  clamps, the STUSB4500 pins stay at or below 20.79 V (VDD) and 23.0 V (VBUS_VS_DISCH)
  with VBUS_P at 28.35 V, over −40 to 125 °C. That leaves 7.21 V and 5.0 V to the 28 V
  limits on DS18004 VZ and TC maximum rows, so L7 is **PASS** on guaranteed zener figures.
  The margins are conditioned on VBUS_P at that 28.35 V row: inductive overshoot on VBUS_P
  is not quantified, so the row is not a guaranteed VBUS_P transient bound.
  The STUSB4500 limits still rest on mirror-source evidence. The main path is now bounded by
  the Q1 −30 V VDS, 1.65 V above the 28.35 V row, not by the STUSB4500. VDD stays at or below
  20.38 V at 105 °C, inside the 22 V operating row.
- The local clamps create new conditions:
  - At a 5 V attach, VDD is at least 4.373 V at the 210 µA idle maximum and at least 4.209 V at
    twice the 160 µA idle typical, through the 1.47 kΩ feed (phase 10). The active-communication
    IDD maximum is not in the copied datasheet, so that case stays OPEN.
  - The 2 kΩ VBUS_VS_DISCH feed needs about 0.91 s to discharge 120 µF from 21 V to 0.5 V.
    The default TDISPAR0V (9, at least 630 ms) is too short, so the NVM image must set
    TDISPAR0V ≥ 13.
  - The STUSB4500 22 V VMONUSBH overvoltage monitor no longer works behind the clamp.
    U2 OVP (21.60–22.56 V) is the only slow-overvoltage protection.
  - Q1's off-state integrity at temperature depends on the Q6 hot leakage, which is
    unsourced.

- Q1 is a proposal. AO3401A is rated −4.2 A, below the 5 A target. DMP3036SFG-7 keeps
  the −30 V VDS and raises VGS to ±25 V, which leaves 14.9 V at the hot overshoot gate
  case. Its −5.8 A (70 °C) and −7.2 A (25 °C) ratings at VGS −5 V assume 1 in² of 2 oz
  copper. At 5 A and 29 mΩ it dissipates about 0.73 W: about 40 °C rise at 55 °C/W, or
  about 99 °C on the minimum pad. Its PowerDI3333-8 land is a draft from the Diodes text
  and must be redrawn before layout.
- The proposed gate divider replaces 100k/150k, which drove −2.0 V at 5 V VBUS, inside
  the −1.0 to −2.5 V threshold range. R11 150k / R12 4.7k drives −4.61, −4.85 and
  −5.09 V at 4.75, 5.00 and 5.25 V. The guaranteed 29 mΩ row is at −5 V, which this divider
  reaches only above about 5.16 V VBUS; no divider reaches it at 5.00 V. With
  `POWER_ONLY_ABOVE_5V`, Q1 stays off at 5 V anyway.
  At 20 V the divider alone would reach −19.4 V, so D8 conducts about 2.0 mA and holds
  the gate at 10.4–11.6 V, at least 13.4 V inside the ±25 V rating. At the 25.21 V
  overshoot case, D8 carries 3.08 mA and VBEN sinks 3.15 mA in total; that VBEN rating
  is unsourced. With the divider alone, that case reaches −24.44 V (0.56 V margin), and the
  28.35 V TVS2200 row reaches −27.49 V, 2.49 V beyond the rating. Phase 11 therefore adds D13,
  a second BZT52C11-7-F in parallel with D8 (`dec-p-q1-gate-clamp-redundant`). One open clamp
  then still holds the gate; both open is a double fault. The turn-on
  gate time constant falls from 6.0 ms to 0.46 ms. This is a draft proposal
  (`dec-p-20v-q1-gate-clamp`); nothing is measured.
- Q1 soft start (`dec-p-20v-q1-soft-start`, proposed). With C35 alone the drain
  transition is limited only by Q1's own Miller charge and lasts microseconds, so closing
  at 20 V would dump C3 into the uncharged Board B bank. C36 1 µF (C15849) now runs from
  VBUS_OUT to Q1_MX, and Q5 BSS138-7-F, used only as its body diode, conducts from Q1_MX
  into Q1_G. The drain then slews at the R12 gate current (3.45–4.0 mA at 20 V) divided by
  C36 (0.4–1.1 µF assumed under DC bias): 3.1–10 V/ms, so at most 2.5 A into a 250 µF
  Board B bank, below the 4.185 A I(OL) minimum. The diode blocks the reverse path, so a
  VBUS_P rise while Q1 is off cannot pull the gate on. R27 150k recharges Q1_MX and helps
  turn-off. Q1 absorbs about 50 mJ per closure over 2.0–6.5 ms; its SOA is OPEN.
- VBUS_VS_DISCH now has R14 + R28, 2 × 1k in series. Discharge current is at most 10.6 mA,
  against the 50 mA maximum. The discharge reaches vSafe0V only if the NVM sets
  TDISPAR0V ≥ 13 (see above).
- The STUSB4500 VBUS sense sits behind the reverse-blocking eFuse and C3, so after
  detach or hard reset it may not see vSafe0V promptly. This needs a bench check (OPEN).
- `scripts/pcb/calculate-input-ovp-20v.py` reproduces these figures. The CSD18543Q3A land
  is a project-authored draft from the TI text and must be reviewed before layout.

The board-p PCB, the 5 A NVM image and every measurement are unchanged or absent.
Canonical adoption, NVM programming, ordering and energizing each need separate
permission.

The rest of this page describes the routed 15 V module and its PCB. That is the
historical, as-built-design record; the 15 V Board P was never built.

## A verified 15 V-only configuration is mandatory

The as-built Board P PCB uses D5 Littelfuse SMAJ16A, C74561, a 16 V standoff TVS. It is
now a retired candidate record and has no published component page. **Factory 20 V negotiation is unsafe for this board** and can
cause sustained TVS conduction. The input TVS sees negotiated VBUS even while the
output switch is off, so output gating does not remove this requirement.

First power and program P from a current-limited **5 V-only source**, with Board B
disconnected. Resolve the programming-jig voltage and VREG_2V7 pull-up loading
questions in `boards/board-p/README.md` before attaching the jig. Program two PDOs
with PDO2 at 15 V / 3 A, disable every 20 V request and set
`POWER_ONLY_ABOVE_5V = 1`. Read back the NVM and retain the actual image; verify the
configuration after a power cycle before using a source capable of 15 V or 20 V.
Then verify actual input VBUS and switched VBUS_OUT with B still disconnected.

No retained NVM image, programmed readback or bench result establishes that an
assembled module already has this configuration. Routed copper and the 15 V-only
label do not prove programmed state, startup or load performance.

## Input-transient screening remains conditional

The replacement TVS has a 26 V maximum clamp point at 15.4 A, a 10/1000 µs pulse
and 25 °C. Its 16 V standoff leaves only 0.25 V above the project's 15.75 V high
normal-input screening point. Confirm the actual source and temperature envelope.

Board B D3 now uses [SDT5A60SA-13, C3024223](/docs/components/records/c3024223/),
with a 60 V reverse rating. Combining the 26 V clamp point with the conditioned
14.814 V negative pre-rail magnitude gives about **40.814 V**: below U4's 45 V
absolute maximum and D3's 60 V reverse rating. This clears the previous table-point
mismatch. It does not imply that U4 regulates beyond its 40 V operating limit.

The 26 V point is not an installed or full-temperature surge ceiling. Actual
source energy, return-path inductance, ringing, hot clamp behavior and repeated
pulses remain open qualification items. Read the
[integration records](/docs/components/integration/) and
`manufacturing/power-budget.json` for the complete conditioned stress screen.

## Board-to-board interface

JOUT1 is the unkeyed PZ254V-11-06P male header, C492405. Board B J5 uses the mating
PM254V-11-06-H85 female header, C2832269. These replace the earlier JST cable
interface for the Board P / Board B arrangement.

| Pin | Net | Role |
| --- | --- | --- |
| 1 | `VBUS_OUT` | Switched positive output |
| 2 | `VBUS_OUT` | Paired positive output |
| 3 | `ATT` | Open-drain attachment status |
| 4 | `PDOK` | Open-drain power status |
| 5 | `GND` | Return |
| 6 | `GND` | Paired return |

The header is unkeyed. Pin-1 alignment, side of insertion and board orientation are
part of the stack contract; a six-pin header cannot enforce them mechanically.
Check any status-line pull-up voltage and unpowered behavior in the attached circuit.

## Mounting geometry

The mechanical source is `boards/board-p/mechanical.json`. Coordinates are in
millimeters relative to the board outline minimum (0, 0).

| Feature | X | Y | Size or role |
| --- | --- | --- | --- |
| Mounting hole 1 | 4.0 | 4.0 | Ø3.2 mm NPTH, M3 |
| Mounting hole 2 | 23.0 | 4.0 | Ø3.2 mm NPTH, M3 |
| Mounting hole 3 | 12.8 | 32.6 | Ø3.2 mm NPTH, M3 |
| JOUT1 center | 12.9 | 37.7 | Six-pin, 2.54 mm pitch |
| JOUT1 pin 1 | 6.55 | 37.7 | Numbering increments toward +X |
| USB connector center | 13.506 | 5.0 | Opening at the Y = 0 edge |

### Mounted coordinates on Board B

The table above remains Board P-local geometry. The current Board B carries J5
on F.Cu. The PD module faces B's component surface, with its own component face
down in CAD and its front plane nominally at Z=+11.1 mm relative to B's front.
The complete XY mapping is `pd_to_board_b(x,y)=(y−0.5,x+12)`. Its projection is
B x=−0.5–39.5 mm, y=12–39 mm, with USB access at B's left edge. This moves the
module away from B's independent top-left support. Board P's own PCB is unchanged.

| Feature | Board B X | Board B Y |
| --- | --- | --- |
| P mounting hole 1, H1 | 3.5 | 16.0 |
| P mounting hole 2, H2 | 3.5 | 35.0 |
| P mounting hole 3, H3 | 32.1 | 24.8 |
| J5 center | 37.2 | 24.9 |
| J5 pin 1 | 37.2 | 18.55 |
| J5 pin 6 | 37.2 | 31.25 |

J5 pins increment toward increasing Board B Y on 2.54 mm pitch. The connector is
on B's front side; the earlier bottom-side stack and its decreasing-Y pin order are
historical. Verify every mating pin and hole against this transform.
The three PD mounting holes remain Ø3.2 mm; B's four independent Ø3.0 mm corner
support holes have a separate [support contract](./board-contract.md#independent-corner-supports).

Board B is installed on legs with its front/component face down. In that installed
orientation, P is physically below B even though it appears above B in CAD.
The 11.1 mm plane spacing is a nominal CAD setting based on the mating-header
clearance and insertion screen, not a qualified spacer part. Actual standoff
selection, seated height, tolerances and retention remain unmeasured. Select leg
height and mechanical spacing from the final populated assembly; nominal model
planes alone do not establish component or cable clearance. The earlier HC-11
option's 11 mm height does not clear this front-down stack over a flat floor:
P's back substrate plane alone reaches 12.7 mm, before outward solder tails.
The selected [18 mm printed-leg prototype](./board-contract.md#independent-corner-supports)
addresses that nominal height conflict. Actual printed fit, screw passage,
adhesive retention and enclosure clearance remain physical checks.

The mating female body is nominally 8.5 mm high. Select standoffs from an actual
stack fit check; nominal header body height alone does not establish assembled
board separation, pin engagement or clearance above components.

## Regeneration

```sh
python3 scripts/schgen/gen_schematic.py scripts/schgen/board_p_spec.py
```

Run the strict component and integration checks after source changes. The PCB is a
separate routed artifact and must stay in connectivity parity with the generated
schematic. Follow the [release gates](./release-readiness.md) before an order.
