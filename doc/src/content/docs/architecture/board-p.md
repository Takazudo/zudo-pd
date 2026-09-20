---
title: Board P — Reusable USB-PD Input
sidebar_position: 2
description: The independent 27 × 40 mm input module, its six-pin interface and its unverified configuration boundary.
---

Board P is a two-layer, 27 × 40 × 1.6 mm USB-PD input board. It retains a routed
prototype layout and the STUSB4500QTR controller, with project-local component
records and a generated schematic at `boards/board-p/board-p.kicad_sch`.
The source spec is `scripts/schgen/board_p_spec.py`.

## A verified 15 V-only configuration is mandatory

Board P D5 now uses [Vishay SMAJ16A-E3/61, C968650](/docs/components/records/c968650/),
a 16 V standoff TVS. **Factory 20 V negotiation is unsafe for this board** and can
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
