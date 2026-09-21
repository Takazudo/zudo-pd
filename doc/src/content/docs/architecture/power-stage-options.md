---
title: Renewed Power Stage
sidebar_position: 5
description: Selected regulator changes, voltage calculations, and remaining qualification limits.
---

The renewal keeps the nominal output targets **+12 V / 1.2 A, +5 V / 0.5 A,
and −12 V / 0.8 A** and changes the regulators to recover headroom. These are
whole-board targets shared by the output connectors. They remain prototype
qualification targets; the schematic and fabrication data do not establish a
continuous-load rating.

| Stage | Selected part | Nominal intermediate or output |
| --- | --- | --- |
| U2 positive buck | AP63201WU-7, C2071044 | +13.44 V |
| U3 positive buck | LM2596S-ADJ, C347423 | +6.519 V |
| U4 inverting buck-boost | LM2596S-ADJ, C347423 | −14.145 V |
| U6 positive LDO | LT1963AEQ#TRPBF, C459702 | About +11.981 V with typical adjustment current |
| U7 positive LDO | LT1963AEQ#TRPBF, C459702 | About +4.998 V with typical adjustment current |
| U8 negative LDO | LT3015EQ#PBF, C666306 | About −12.054 V from R26 8.2 kΩ + R27 680 Ω over R28 1 kΩ |

U6 uses 8.2 kΩ + 680 Ω above ADJ and 1 kΩ below it. U7 uses 3.09 kΩ + 33 Ω
above ADJ and 1 kΩ below it. These are exact YAGEO RT0603BRD parts with 0.1%
initial tolerance and 25 ppm/°C TCR. The nominal figures use
`VOUT = 1.21 × (1 + Rtop/Rbottom) + 3 µA × Rtop`.
With the conservative 1.174–1.246 V reference envelope, independent 0.1%
resistors, and 0–10 µA adjustment current, the calculation gives approximately
**11.578–12.422 V** and **4.833–5.177 V**. This is a conditional screening
calculation: the 10 µA maximum is specified at 25 °C only. It does not establish
full-temperature output accuracy. Independent resistor TCR, regulator temperature,
load regulation, wiring and PTC voltage drop must also be included.

The [LT1963A datasheet](https://www.analog.com/media/en/technical-documentation/data-sheets/1963aff.pdf)
provides 0.55 V maximum dropout at 1.5 A and 0.35 V at 0.5 A in its marked
full-temperature rows. E-grade testing and characterization conditions apply.
The [LT3015 datasheet](https://www.analog.com/media/en/technical-documentation/data-sheets/3015fb.pdf)
provides a fixed −12 V regulation interval of −11.76 to −12.24 V for input
−30 to −13 V and load 1 mA to 1.5 A, subject to grade, temperature and thermal
limits. U4's 10.5 kΩ/1 kΩ divider gives a nominal magnitude of 14.145 V;
using its retained full-temperature reference and 0.1% resistor tolerances gives
13.545–14.747 V before TCR and ripple. The integration calculation also tests
independent 25 ppm/°C drift over a 100 °C change, leaving about 0.484 V above
the 13 V input boundary before ripple and wiring losses.

C40, C41 and C42 add one Panasonic 25SVPF47M, 47 µF / 25 V polymer capacitor
at each LDO output. Its [exact manufacturer table](https://industrial.panasonic.com/cdbs/www-data/pdf/AAB8000/AAB8000C177.pdf)
gives ±20% capacitance at 20 °C and 30 mΩ maximum ESR at 100–300 kHz / 20 °C.
The initial minimum capacitance is 37.6 µF, above the regulators' 10 µF minimum.
The positive regulator permits ESR up to 3 Ω; the negative regulator requires
ESR below 0.5 Ω. The capacitor's room-temperature row does not replace a
stability and transient check across the actual temperature range. C42 positive
connects to ground and negative connects to U8 OUT.

Both LDOs use ADI Q package drawing 05-08-1461 Rev. F. The land patterns are
normalized to its recommended solder pads: 1.7018 mm lead pitch,
1.0668 × 2.286 mm lead pads, and a 10.668 × 8.89 mm thermal pad.
U6/U7 pins are **1 SHDN, 2 IN, 3 GND, 4 OUT, 5 ADJ; tab GND**.
U8 pins are **1 SHDN, 2 GND, 3 IN, 4 SENSE, 5 OUT; tab IN**.
The downloaded LT3015 symbol had reversed functional assignments for pins
1/5 and 2/4; these were corrected against the manufacturer drawing. Its tab
copper belongs to the negative intermediate rail, never to ground.

Sustained dissipation must include regulator ground current as well as
`(VIN − VOUT) × load current`. The LT1963A table includes 120 mA at 1.5 A
and 25 mA at 0.5 A under its stated input condition. The LT3015 table includes
70 mA at 1.5 A measured in dropout, with no separate 0.8 A maximum. Using that
higher-load value as a conservative screen can put the negative stage above
3 W; it is not a measurement of the finished board. The LT3015 14 °C/W figure
requires 2500 mm² of copper on **each** side in the datasheet layout. Copper
area, thermal vias, adjacent converter heat and enclosure airflow need review
and full-load measurement on the actual PCB.

Exact identities are linked at [JLCPCB C459702](https://jlcpcb.com/partdetail/AnalogDevices-LT1963AEQTRPBF/C459702)
and [JLCPCB C666306](https://jlcpcb.com/partdetail/AnalogDevices-LT3015EQPBF/C666306).
Current stock and assembly availability remain unconfirmed. Manufacturer PDF
text was independently reviewed, but direct binary retention repeatedly failed;
the evidence owner retains genuine mirror hashes and marks the missing primary
binary lock explicitly. Those facts remain **UNSOURCED** under the repository's
strict source policy. Procurement, primary source retention, startup, transient
protection, output accuracy, capacitor stability and thermal qualification must
be closed before claiming a production-ready supply.
