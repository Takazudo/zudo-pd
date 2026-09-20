---
title: Board Roles and Interface
sidebar_position: 2
---

## The input module owns USB-PD

The input module negotiates the required supply, controls its load switch and exposes
programming and diagnostic access. Its connector, controller, VBUS protection and
switch form one reviewed circuit. A board that can negotiate a different voltage
is not automatically suitable for the synth board.

[Board P](./board-p.md) is the reusable input-board direction. The older generated Board A remains
as a design reference; its component records are retained. Board P must have its
own configuration, harness and mechanical contract rather than inherit Board A's
connector assumptions. Its 16 V input TVS requires verified 15 V-only operation:
first programming power is 5 V only, followed by NVM readback that disables every
20 V request before higher-voltage-capable PD use.

## The synth board owns conversion and distribution

Board B uses an AP63201WU-7 synchronous buck for the +12 V pre-rail, one
LM2596S-ADJ buck for the +5 V pre-rail and another LM2596S-ADJ inverting buck-boost
for the negative pre-rail. LT1963A adjustable regulators produce the positive rails;
a fixed LT3015-12 produces the negative rail. There is no SEPIC in the circuit.

| Stage | Nominal intermediate | Final regulator |
| --- | --- | --- |
| U2 AP63201 synchronous buck | +13.44 V | U6 LT1963A, adjusted for the +12 V target |
| U3 LM2596 buck | +6.519 V | U7 LT1963A, adjusted for the +5 V target |
| U4 LM2596 inverting buck-boost | −14.145 V | U8 LT3015-12 |

These nominal values come from the selected feedback networks. The previous
L7812/L7805/CJ7912 chain is retired. The new selections address its headroom
constraints, while guaranteed reference limits, divider tolerance, component
temperature, ripple, low-line dropout and thermal performance still require the
conditioned [integration review](/docs/components/integration/).
See [the positive pre-regulator](./positive-pre-regulator.md) for its component and
capacitor assumptions.

## Historical Board A / Board B cable contract

The earlier split-board specs used JST B6B-XH-A connectors, J4 and J5 respectively.
Board B J5 now uses the female stacking header for [Board P](./board-p.md). The
following table preserves the old signal contract; it is not the current connector
selection.

| Pin | Board A net | Board B role |
| --- | --- | --- |
| 1–2 | `VBUS_OUT` | Paired +15 V input |
| 3 | `ATT` | Attachment-status signal |
| 4 | `PDOK` | PD-status signal |
| 5–6 | `GND` | Paired return |

Status lines are open-drain signals, not power rails. Their pull-up domain and
unpowered behavior require review for the actual attached module. The component
catalog and generated specs remain authoritative for exact pin identities.

## Synth connector contract

J10/J11 use the shrouded right-angle DEALON DW254P-2X8-L0 / C4749189. Pin numbering
follows the conventional synth power assignment: pins 1–2 are −12 V, pins 3–8 are
GND, pins 9–10 are +12 V, pins 11–12 are +5 V, pins 13–14 are CV and pins 15–16 are
GATE. The red stripe identifies the −12 V end. Verify the mating cable orientation
against the actual keyed body and pad 1 before powering hardware.

The connector replaces the custom printed-guard requirement. Its body, solder-tail
and mating-cable envelopes still determine the board edge and component clearances.
Mounting coordinates and board thickness belong in the PCB mechanical record.

## Screw-terminal and mounting contract

Board B retains a 110 × 85 mm outline with a plain left edge. Board P's unchanged
27 × 40 mm PCB now mates to front-side J5 with its component face toward B.
Board B is installed front-down on legs, so the PD module is physically below B;
in CAD, P's front face is down above B at nominal Z=+11.1 mm. The
`pd_to_board_b(x,y)=(y−0.5,x+12)` mapping transforms all three holes and six mating pins
together; see [Board P](./board-p.md).

J6 and J7 are top-side WJ500V-5.08-2P / C8465 two-pole blocks with wire entries
facing left. Their assignments are:

| Pin | Output net |
| --- | --- |
| J6.1 | GND |
| J6.2 | −12 V |
| J7.1 | +5 V |
| J7.2 | +12 V |

These connections share the same board-level rail budgets as J10/J11. Verify pin
numbering, wire entry and actual termination on the assembly before applying power.
Front voltage labels are retained and duplicated on B.SilkS. The back labels must
read normally from the back and identify these same four pins. Check label-to-pin
alignment from both sides before wiring the installed board.
J8/J9 are retired. The current board has a plain left edge and needs no printed
terminal guard. The [printed accessory](https://github.com/Takazudo/zudo-pd/blob/main/3dp-files/README.md)
is the adhesive leg described below.

## Independent corner supports

Four Ø3.0 mm non-plated holes were sized for HC-11 adhesive supports and remain
unchanged for the selected printed-leg prototype. Each center is 4 mm from its two
adjacent board edges. These holes are independent of Board P's three Ø3.2 mm
mounting holes and are excluded from the electrical BOM and placement files.

| Hole | Board B X (mm) | Board B Y (mm) |
| --- | --- | --- |
| H4, top right | 106 | 4 |
| H5, bottom left | 4 | 81 |
| H6, bottom right | 106 | 81 |
| H7, top left | 4 | 4 |

The current [printed adhesive-leg prototype](https://github.com/Takazudo/zudo-pd/blob/main/3dp-files/adhesive-leg/README.md)
has an 18 mm seating height, a 14 × 14 × 2 mm base and a straight Ø7 mm pole.
Its 4.5 mm blind bore copies the user's proven 27-vertex untapped M3 aperture,
with no larger lower cavity. Start with an M3 × 5 mm screw: through the 1.6 mm
PCB it inserts 3.4 mm, leaving 1.1 mm nominal clearance to the blind floor.
The former M3 × 8 mm recommendation does not apply. Existing Ø3.0 mm PCB holes
give zero nominal diametral clearance for M3; actual screw passage, printed fit,
retention and adhesive loading require physical checks. The four bases extend
3 mm beyond the board edges, requiring a 116 × 91 mm adhesive footprint.

The [retained evidence for the earlier HC-11 option](https://github.com/Takazudo/zudo-pd/blob/main/boards/board-b/supports/README.md)
specifies an 11 mm support height, interpreted from the drawing as base underside
to PCB seating shoulder. Adhesive thickness and compression are unspecified;
do not add an assumed tape allowance. Complete head, column and adhesive-base
envelopes are also unavailable. The footprint's Ø6 mm Fab circle and 6.5 mm square
courtyard are project clearance assumptions, not manufacturer dimensions.

**HC-11 alone does not clear the front-down assembly over a flat floor.** P's back
substrate plane reaches 12.7 mm from B's component plane, at least 1.7 mm past the
nominal 11 mm floor plane. The screw-terminal drawing reaches 14.2 mm, 3.2 mm past
that plane; P solder tails may extend farther. Moving P in X/Y frees the corner
but does not solve this height conflict. The selected 18 mm printed leg addresses
the nominal height issue, leaving 3.8 mm above the terminal drawing maximum.
Its separate CAD report does not qualify printing, adhesive retention, temperature
or physical fit. The leg does not change the PCB's electrical design or fabrication
files. Its CAD verification is separate from the evidence for the HC-11 option.

## Seven top-edge contacts

P1 and TP3/TP4/TP5 form a row of 1.5 × 2.5 mm bare contacts on 2.54 mm pitch,
centered 1.8 mm from the top edge. The complete row moves 20 mm right to stay
accessible beyond the PD module. The contact order from left to right is:

| Contact | Board B X (mm) | Net or nominal rail | Use |
| --- | --- | --- | --- |
| P1.1 | 56.19 | ATT | Attachment status |
| P1.2 | 58.73 | PDOK | PD status |
| P1.3 | 61.27 | GND | Shared probe return |
| P1.4 | 63.81 | NC | Remains unconnected |
| TP3.1 | 66.35 | +13.44 V PRE | Positive 12 V pre-regulator measurement |
| TP4.1 | 68.89 | +6.519 V PRE | Positive 5 V pre-regulator measurement |
| TP5.1 | 71.43 | −14.145 V PRE | Negative pre-regulator measurement |

The intermediate values are nominal design values, not measured acceptance limits.
Use P1.3 as the common measurement ground; the NC contact is not a second return.
Review jig alignment and signal-voltage limits before applying a probe fixture.
