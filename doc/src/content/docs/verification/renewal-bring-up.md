---
title: PD15 Renewal Prototype Bring-Up
sidebar_position: 3
description: Staged qualification for P15 plus revision-identified PD15 Board B.
---

This procedure applies only to PD15, **P15 + Board B**, with the AP63201 / LT1963A / LT3015 design. The
+12 V / 1.2 A, −12 V / 0.8 A and +5 V / 0.5 A figures are whole-board targets,
shared by the output sockets and screw terminals. Use dummy loads until polarity, regulation and
startup are established. Record the exact PCB revision, populated BOM, PD source,
cable, ambient temperature and instrument setup with every result.

## 1. Inspect the unpowered assembly

Compare the populated board with its release BOM and placement drawing. Verify
U2's six-pin orientation, both LDO pin maps and all polarized capacitors. U6/U7
tabs are ground; U8's tab and U4's tab belong to the negative intermediate rail.
C42's positive terminal connects to ground and its negative terminal to U8 OUT.
U4 and U8 tabs must connect to each other and to the negative intermediate rail,
and must be isolated from ground. U6/U7 tabs must connect to ground.

Check for shorts between input, ground and each rail. Account for capacitors
charging during resistance measurements. Confirm P-to-B pin 1 alignment against
the [module contract](../architecture/p15-shared-input.md#accepted-interface), including the front-side J5
orientation and face-to-face stack. The unkeyed stacking connector needs a mechanical orientation check.
Confirm both synth connectors' pad 1 and cable red stripe identify −12 V; do not
reuse an older cable assignment without a continuity test.

Confirm the two top-side screw-terminal blocks face left and match the current
pin map: J6.1=GND, J6.2=−12 V, J7.1=+5 V and J7.2=+12 V. Check wire termination
against the exact component evidence and inspect for loose strands or unintended
contact with adjacent conductors. The old Fastons, printed guard and T-notches are
not part of this revision.
Check the four voltage labels from both sides: the front labels stay present, and
back labels must read normally from the back while naming the same electrical
pins. Inspect leg height, terminal-tail clearance and probe access with Board B's
front/component face down, as it will be installed. Four independent Ø3.0 mm
corner holes are separate from the three Ø3.2 mm PD mounting holes. Use the selected
18 mm printed-leg prototype rather than assuming the earlier 11 mm HC-11 option
clears the assembly. Check the M3 × 5 mm screw passes freely through the finished
PCB hole and engages the 4.5 mm blind printed bore without bottoming out. Verify
printed fit, screw retention, adhesive loading and the 116 × 91 mm base footprint
in the actual enclosure before installation. See the
[support contract](../architecture/board-contract.md#independent-corner-supports).

## 2. Qualify Board P separately

Here “Board P” means **P15 r1**, not PD20 r3. Complete every [P15-NVM-1–7 test](../architecture/board-p15-programming.md).
Both Board L and Board B stay disconnected: current-limited 5 V-only provisioning, factory dump, write/readback,
full power-cycle with external jig pull-up sequencing and configuration verification, then NVM-6 using a
current-limited PD test source also offering 20 V. RESET is grounded and cannot be pulsed. Only an accepted
P15 may proceed to the downstream boards. File regeneration is not programming or readback.

Before Board B power, identify the unit/population against S3 and complete
[D1 inspection](https://github.com/Takazudo/zudo-pd/blob/main/manufacturing/board-b-unpowered-check.md).
Do not assume current development substitutions describe received Board B. Physical tests below remain unperformed.

## 3. Inspect Board B under controlled power

With P disconnected, use the verified B input pins and a current-limited bench
supply for initial checks. Prevent simultaneous backfeeding through a second
source. Start without external loads and monitor input current and all intermediate
rails while increasing toward the intended 15 V input. The target intermediates
are +13.44 V, +6.519 V and −14.145 V. Stop on wrong polarity, an unexpected current
rise or a rail outside its reviewed component limits.

Use the [seven-contact edge row](../architecture/board-contract.md#seven-top-edge-contacts)
for repeatable access: TP3 measures the +13.44 V pre-rail, TP4 the +6.519 V pre-rail
and TP5 the −14.145 V pre-rail. P1.3 is the shared ground; leave P1.4 NC. Confirm
fixture alignment and probe voltage ranges before attaching it. The entire row
has moved 20 mm right; old probe-fixture coordinates do not match this revision.

Measure each final rail both before and after its PTC. The nominal outputs are
about +11.98 V, +5.00 V and −12 V; component tolerances and wiring losses make
these nominal values different from acceptance limits. Use the current
[integration records](/docs/components/integration/) and the repository's
`manufacturing/power-budget.json` for the conditioned voltage bands. Record both
DC values and waveforms instead of assigning a pass from a nominal value alone.

## 4. Load, low-line and thermal qualification

Increase one rail's dummy load in small steps, then repeat with all rails loaded
together. Measure connector voltage, intermediate minimum voltage, input current,
converter and LDO temperatures, and PTC voltage drop at every step. Test the stated
operating ambient and enclosure conditions. The three LDOs can dissipate several
watts in the conservative corner screens; copper area and vias alone do not
establish a continuous-load rating.

Measure output ripple with a short probe ground at the output capacitor and at
the connector. Record bandwidth limit, coupling and probe setup. Apply load steps
and capture overshoot, undershoot and settling on both intermediate and final rails.
The AP63201's biased ceramic bank and near-100% duty behavior require actual
low-line and transient measurements. Retain waveforms at the 14.0 V B-input
screening point as well as nominal input; 14.0 V is a project test assumption,
not a guaranteed input contract at the connector.

## 5. Test the complete PD chain

Reconnect P only after the separate boards have passed their staged checks.
Capture attach and restart waveforms under no load and progressively larger loads,
including simultaneous rated targets. The inverting converter's startup demand
may trip a 3 A PD source even when steady-state calculations fit. Check source
retries, PD renegotiation, input droop and rail sequencing with the actual intended
source and cable. Repeat load and temperature measurements with the two boards in
their final mechanical arrangement: B front-down on its legs, P in the front-side
stack, and the final screw terminals, wiring and enclosure. A test with different airflow or connections does not qualify the
intended assembled configuration.

The new SMAJ16A TVS and 60 V D3 clear the previous conditioned table-point mismatch.
Their 26 V / 25 °C pulse screen does not establish hot or installed surge protection.
Measure actual overshoot, return-path effects and pulse energy as separate
qualification gates; ordinary startup and DC load tests do not cover them.

Record measured operating limits and every failure. Only measured, repeatable
results can promote the design targets into a continuous-load specification.
