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
LED lamp and zudo-pd, kept a single lineup (this revision becomes the new zudo-pd), replaced the
TPS26630 front end with TPS16630PWPR + LM74700-Q1 + Q3, and accepted per-unit NVM programming
(`dec-common-controller-block`, `dec-single-lineup`, `dec-p-20v-front-end-r3`,
`dec-nvm-per-unit-programming`). The r3 front end is drawn in a separate unbound draft,
`scripts/schgen/board_p_r3_spec.py`. The table below still describes the inventory-bound r2
draft, whose TPS26630 evidence feeds hash-locked integration runs.

The generated schematic and `board_p_spec.py` on the development branch now carry an
unvalidated draft:

| Ref | Part | Role |
|---|---|---|
| D5 | [TVS2200DRVR C523793](/docs/components/records/c523793/) | 22 V-standoff clamp on connector VBUS_IN |
| Q3 | [CSD18543Q3A C840100](/docs/components/records/c840100/) | Reverse-blocking N-FET: source on VBUS_IN (U2 IN_SYS), drain on U2 IN, gate on B_GATE |
| Q4 | [BSS138-7-F C40912](/docs/components/records/c40912/) | B_GATE fast pulldown, gate driven by U2 DRV |
| U2 | [TPS26630RGER C1850276](/docs/components/records/c1850276/) | eFuse to the protected node VBUS_P, ahead of every other part |
| R24 / R25 | 174k / 10k, 0.1 % | OVP, 21.60–22.56 V rising (22.67 V with 25 ppm/°C over 100 °C) |
| R22 / R23 | 11.5k / 4.02k, 0.1 % | UVLO, 4.53–4.73 V rising, 4.20–4.45 V falling |
| R26 | 4.02k, 0.1 % | I(OL) 4.185–4.815 A |
| C5 | 100 nF | dVdT ramp |
| C3 | 100 µF 50 V (80–120 µF) | Single protected-node bulk; C4 is removed |
| Q1 | [DMP3036SFG-7 C461081](/docs/components/records/c461081/) (proposed) | Output P-FET switch: source on VBUS_P, drain on VBUS_OUT, gate on Q1_G; replaces AO3401A |
| R11 / R12 | 150k C22807 / 4.7k C23162 (proposed) | Q1 gate divider: R11 VBUS_P to Q1_G, R12 Q1_G to VBEN (was 100k / 150k) |
| D8 | [BZT52C11-7-F C92321](/docs/components/records/bzt52c11-c92321/) (proposed) | Q1 gate clamp: cathode on VBUS_P, anode on Q1_G |
| C36 / Q5 / R27 | 1 µF C15849 / [BSS138-7-F C40912](/docs/components/records/c40912/) / 150k C22807 (proposed) | Q1 Miller soft start: C36 VBUS_OUT to Q1_MX, Q5 body diode Q1_MX to Q1_G, R27 VBUS_P to Q1_MX |
| R14 / R28 | 2 × 470 Ω C23179 | VBUS_VS_DISCH series resistance (R28 proposed) |

- MODE is left open, which selects latch-off.
- PGTH is tied to GND.
- The STUSB4500 VDD and VBUS sense, and Q1, now sit on VBUS_P, so the TVS-clamped
  connector node no longer reaches the STUSB4500 28 V VDD absolute maximum.
- Q3 and Q4 follow the TPS2663 datasheet section 8.3.5 back-to-back topology, so U2 is
  specified to block reverse current and reverse polarity. Q4 meets the stated pulldown
  rule: at least 15 V VDS, 20 V VGS rating, Ciss ≤ 50 pF and VGTH ≤ 3 V.
- The rising UVLO threshold is now guaranteed at or above 4.5 V. The falling threshold,
  4.20–4.45 V, still sits below 4.5 V.
- One 100 µF part keeps the 5 V → 20 V transition inrush at the 30 V/ms PD slew ceiling
  to about 3.6 A, below the 4.185 A I(OL) minimum; the earlier 2 × 100 µF drew about 7.2 A.
  The slew ceiling is a project assumption. The estimated hot-unplug VBUS_P peak at
  80 µF is 25.1 V only on TYP I(SCP) and fast-trip figures and a 30 mΩ ESR assumption;
  at ESR 0.3–0.5 Ω it is 27.7–29.6 V, and at the 4.5 µs soft-short maximum it is 27.1 V.
  The only guaranteed bound is the TVS2200 clamp, 28.0–28.35 V, so gate L7 stays
  **BLOCKING**.
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
  is unsourced. If D8 fails open, that case reaches −24.44 V, a 0.56 V margin. The turn-on
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
- VBUS_VS_DISCH now has R14 + R28, 2 × 470 Ω in series: 26.7 mA at 25.1 V against the
  50 mA maximum (was 53 mA). The STUSB4500 discharge time constant doubles against its
  800 ms default; whether VBUS_P still reaches vSafe0V in time is OPEN.
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
