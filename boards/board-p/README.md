# Board P — reusable USB-PD core

Board P is the current routed power-input module. It supplies the downstream Board B
through the six-position XFCN header pair. Board A remains historical schematic
evidence; its gate network and connector are different and must not be treated as
Board P's as-built circuit.

`../../scripts/schgen/board_p_spec.py` is the schematic source of truth. Regenerate:

```sh
python3 scripts/schgen/gen_schematic.py scripts/schgen/board_p_spec.py
```

The PCB retains the routed module's pad/copper geometry. Shared exact parts use the
current project's canonical library names, while the PCB embeds its retained physical
footprints. Updating all PCB footprints from the shared library would change that
geometry and requires a fresh layout review. `layout-verification.json` records the
import comparison; `mechanical.json` records dimensions and mating coordinates.

## Interface and mechanical contract

| JOUT1 pin | Net | Function |
| --- | --- | --- |
| 1, 2 | VBUS_OUT | Switched nominal 15 V; paired power contacts |
| 3 | ATT | Active-low open-drain attach indication |
| 4 | PDOK | Open-drain contract indication; depends on programmed configuration |
| 5, 6 | GND | Paired return contacts |

JOUT1 is PZ254V-11-06P (C492405); Board B J5 is PM254V-11-06-H85
(C2832269). The pair is unkeyed. Verify pin-1-to-pin-1 orientation and every net
before mating. The old Board A JST XH connector has a different pitch and does not
mate directly. Both XFCN parts have a manufacturer 3 A contact rating; paired contacts
do not raise the USB-PD source's 3 A contract limit.

The board is 27 × 40 mm, two layers, 1.6 mm thick. Its mounting holes are 3.2 mm
NPTH for M3 hardware at (4, 4), (23, 4), and (12.8, 32.6) mm, measured from the
upper-left outline corner in KiCad coordinates. JOUT1 pin 1 is at (6.55, 37.7) mm;
subsequent pins advance 2.54 mm along X. The USB opening is at the y=0 edge.
The female body is 8.5 mm tall; actual board spacing and mating engagement require
a stack fit check rather than assuming that body height equals the standoff length.

## Circuit and configuration state

The intended configuration is two sink PDOs, PDO2 = 15 V / 3 A, and
`POWER_ONLY_ABOVE_5V = 1`. **No retained programmed NVM image, persistent readback,
or bench-qualified 3 A output accompanies this PCB.** The design intention does not
establish the factory or installed state. First provision with a current-limited
5 V-only source and the downstream board disconnected. Retain the received image,
40-byte programmed image, byte-for-byte readback, reset reload and full power-cycle
readback before connecting a PD source and load.

Board P's 100 kΩ/150 kΩ gate divider gives ideal steady VGS = −6 V at 15 V and
−8 V at 20 V. C35 connects gate to source; R21 is a 10 kΩ reset pull-down with
RESET available on J2.4. These are Board P facts. The retained Board A records describe
its older 56 kΩ gate resistor, ground-referenced C35, and grounded reset.

Open electrical gates remain: VREG_2V7 feeds 4.7 kΩ I2C pull-ups even though retained
controller documentation only authorizes decoupling; confirm manufacturer approval
or revise this circuit and verify programming-jig logic levels. The SMAJ20A's 32.4 V
clamp table point exceeds Q1's 30 V VDS and the controller's retained 28 V absolute
maximum; actual source/rail/gate transient waveforms and duration remain unmeasured.
NVM policy, switch inrush, steady full-load temperature, and connector temperature
must be checked with the actual downstream load. The nominal 45 W contract alone
cannot establish those results.

## Checks and manufacturing state

The renewal check passed native KiCad netlist comparison (23 nets, 91 nodes), ERC
with zero errors, and PCB DRC with zero errors and zero unconnected items. The
strict component registry and its 53 contract tests passed. The order exporter
accepted 19 fitted components in 14 BOM lines, all on the top side. R17/R18 and
D6/D7 remain intentionally DNP; J2/J3 and MH1/MH2/MH3 are bare copper/mechanical
features excluded from assembly.

Retained warnings are explicit: 29 ERC pin-type warnings; 50 PCB DRC warnings
(23 shared-library footprint mismatches, 19 small-text, 3 silk-over-copper,
2 silk-to-edge, 1 silk overlap, 1 duplicate SCL via, 1 dangling gate-track stub);
three schematic-parity warnings identify the PCB-only mounting holes. No ERC/DRC
error was disabled to obtain these results. Warnings do not establish an assembled
or bench-qualified product.

The XFCN male and female drawings were downloaded on 2026-09-20, confirmed as
PDF drawings for the specified connector families and six-position dimension
rows, and matched their retained SHA-256 values. The current HRO drawing request
returned HTTP 403, so its earlier retained manufacturer extract remains the evidence
and the current retrieval was not represented as a new successful verification.
Yageo and UNI-ROYAL primary documents were readable during the renewal audit.
