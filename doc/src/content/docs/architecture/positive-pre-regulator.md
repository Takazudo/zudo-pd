---
title: Positive Pre-Regulator
sidebar_position: 4
description: The selected AP63201 13.44 V stage, exact component choices and qualification conditions.
---

U2 is an [AP63201WU-7](/docs/components/records/ap63201wu-7/) synchronous buck.
It supplies U6's positive linear stage from the switched input rail. The part is
the adjustable, 500 kHz forced-PWM member of its family; AP63203 and AP63205 are
fixed-output parts and are not substitutes for this circuit.

## Exact component choices

| Reference | Selection | Purpose |
| --- | --- | --- |
| U2 | AP63201WU-7 / C2071044 | Synchronous conversion |
| L1 | ASPI-0630LR-100M-T15 / C1334133, 10 µH | Shielded buck inductor |
| R1 | RT0603BRE07158KL / C861679, 158 kΩ, 0.1% | Upper feedback arm |
| R2 | RT0603BRD0710KL / C95204, 10 kΩ, 0.1% | Lower feedback arm |
| C3/C14/C20/C36/C37 | GRM32ER71H106KA12L / C77102, 10 µF, 50 V | Five parallel output ceramics |
| C39/C46 | Same 10 µF / 50 V ceramic | Local input bank, in addition to bulk C5 and bypass C6 |
| C38 | CC0805KRX7R9BB104 / C1711, 100 nF | BST-to-SW bootstrap capacitor |

The old external diode D1 and 22 nF feedforward capacitor C31 are removed. The
AP63201 has internal compensation. Its datasheet allows an optional 10–220 pF
feedforward capacitor; this design starts without that optional part and requires
load-transient validation.

## Divider range is conditional

The nominal setting is `0.8 × (1 + 158 / 10) = 13.44 V`. The AP63201's 0.792–0.808 V
feedback limits apply over its recommended input and −40 to +85 °C range.
With both resistors at −40 to +85 °C, their 0.1% initial tolerances and 50/25 ppm/°C
TCRs give approximately **13.220–13.662 V** before ripple and dropout.

A 50 mV negative ripple allowance gives a 13.170 V conditional floor. This is
setpoint arithmetic, not a measured output guarantee. In particular, the datasheet
only gives typical high-side on-resistance and describes near-100% duty behavior;
it does not provide a guaranteed hot dropout bound for the final input path.

## Effective capacitance remains an explicit assumption

The output bank is 50 µF nominal. A retained manufacturer-authored Murata curve
shows approximately 15% capacitance loss at 15 V. The conservative project model
uses a 20% bias allowance, 10% initial tolerance, 15% temperature change and 10%
aging allowance: `50 × 0.8 × 0.9 × 0.85 × 0.9 = 27.54 µF`.

The curve and bias/aging allowances are not guaranteed limits. The bank must be
checked at operating voltage and temperature; startup and load-step waveforms
must confirm the actual closed-loop behavior. The same assumptions put the two
input ceramics at 11.016 µF, supplementing the retained bulk capacitor.

## Layout and bench gates

Keep the VIN bypass loop, SW–inductor path and BST capacitor compact. Route feedback
from the output bank away from SW, and return the divider to quiet local ground.
The inductor's 5.5 A saturation and 4 A temperature-rise figures are typical values
with their own test conditions. Check winding temperature, switch temperature,
low-line regulation and full-load transients on the built board.

The inductor footprint follows the manufacturer's Rev C land pattern. Its visible
3D model is an illustrative 7.5 × 6.85 × 3.0 mm maximum-body envelope; exact
manufacturer CAD remains unavailable. The documented footprint dimensions remain
the mechanical source.
See the [component catalog](/docs/components/catalog/) and
[integration rules](/docs/components/integration/) for source provenance and blockers.
