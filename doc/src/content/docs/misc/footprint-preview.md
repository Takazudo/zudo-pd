---
title: Footprint Preview
---

# Footprint Preview

Visual reference of all PCB footprints used in this USB-PD power supply project. All footprints are sourced from LCSC/EasyEDA and converted to KiCad format.

Click on any footprint to view it in fullscreen.

## USB-PD Stage

### U1 - CH224D USB PD Controller

import FootprintSvg from '../../../components/footprint-svg.astro';

<FootprintSvg src="/pj/zudo-pd/footprint-svg/QFN-20_L3.0-W3.0-P0.40-BL-EP1.7.svg" alt="CH224D QFN-20 Package" minWidth="300px" minHeight="300px" />

**Designator:** U1
**Component:** [CH224D](../components/ch224d) - USB PD Controller
**Package:** QFN-20 (3.0mm × 3.0mm, 0.40mm pitch)
**LCSC:** [C3975094](https://jlcpcb.com/partdetail/C3975094)
**Function:** Negotiates 15V from USB-C PD adapter

### J1 - USB Type-C Connector

<FootprintSvg src="/pj/zudo-pd/footprint-svg/TYPE-C-SMD_TYPE-C-6P.svg" alt="USB Type-C 6P Connector" minWidth="300px" minHeight="200px" />

**Designator:** J1
**Component:** USB-TYPE-C-009 - 6P Type-C Female Connector
**Package:** SMD Type-C 6P Female
**LCSC:** [C456012](https://jlcpcb.com/partdetail/C456012)
**Function:** USB-C PD power input

---

## DC-DC Converter Stage

### U2, U3, U4 - LM2596S-ADJ Buck Converter

<FootprintSvg src="/pj/zudo-pd/footprint-svg/TO-263-5_L10.2-W8.9-P1.70-BR.svg" alt="LM2596S TO-263-5 Package" minWidth="300px" minHeight="200px" />

**Designators:** U2, U3, U4 (3× units)
**Component:** [LM2596S-ADJ(UMW)](../components/lm2596s-adj) - Adjustable 3A Buck Converter
**Package:** TO-263-5 (10.2mm × 8.9mm)
**LCSC:** [C347423](https://jlcpcb.com/partdetail/C347423)
**Function:** DC-DC conversion (+13.5V, +7.5V, -13.5V outputs)

### L1, L2, L3 - 100µH Power Inductor

<FootprintSvg src="/pj/zudo-pd/footprint-svg/IND-SMD_L13.8-W12.8.svg" alt="100µH Power Inductor" minWidth="300px" minHeight="300px" />

**Designators:** L1, L2, L3 (3× units)
**Component:** CYA1265-100UH - 100µH 4.5A Power Inductor
**Package:** SMD Power Inductor (13.8mm × 12.8mm)
**LCSC:** [C19268674](https://jlcpcb.com/partdetail/C19268674)
**Function:** Energy storage for LM2596S buck converters (U2, U3, U4)

---

## Linear Regulator Stage

### U6 - L7812CD2T-TR (+12V Linear Regulator)

<FootprintSvg src="/pj/zudo-pd/footprint-svg/TO-263-2_L10.0-W9.1-P5.08-LS15.2-TL.svg" alt="L7812CD2T TO-263-2 Package" minWidth="300px" minHeight="200px" />

**Designator:** U6
**Component:** [L7812CD2T-TR](../components/l7812cv) - +12V 1.5A Linear Regulator
**Package:** TO-263-2 (10.0mm × 9.1mm)
**LCSC:** [C13456](https://jlcpcb.com/partdetail/C13456)
**Function:** Regulates +13.5V to +12V with low noise

### U7 - L7805ABD2T-TR (+5V Linear Regulator)

<FootprintSvg src="/pj/zudo-pd/footprint-svg/TO-263-2_L10.0-W9.2-P5.08-LS15.3-TL-CW.svg" alt="L7805ABD2T TO-263-2 Package" minWidth="300px" minHeight="200px" />

**Designator:** U7
**Component:** [L7805ABD2T-TR](../components/l7805abd2t) - +5V 1.5A Linear Regulator
**Package:** TO-263-2 (10.0mm × 9.2mm)
**LCSC:** [C86206](https://jlcpcb.com/partdetail/C86206)
**Function:** Regulates +7.5V to +5V with low noise

### U8 - CJ7912 (-12V Linear Regulator)

<FootprintSvg src="/pj/zudo-pd/footprint-svg/TO-252-3_L6.5-W5.8-P4.58-BL.svg" alt="CJ7912 TO-252-3 Package" minWidth="250px" minHeight="200px" />

**Designator:** U8
**Component:** [CJ7912](../components/cj7912) - -12V 1.5A Linear Regulator
**Package:** TO-252-3 (6.5mm × 5.8mm)
**LCSC:** [C94173](https://jlcpcb.com/partdetail/C94173)
**Function:** Regulates -13.5V to -12V with low noise

---

## Passive Components

### Capacitors

#### 0603 Ceramic Capacitor

<FootprintSvg src="/pj/zudo-pd/footprint-svg/C0603.svg" alt="0603 Capacitor" minWidth="200px" minHeight="150px" />

**Package:** 0603 (1.6mm × 0.8mm)
**Used for:**

- Ceramic capacitors (470nF for CH224D, 47nF for LM2586 compensation)
- High-frequency decoupling throughout circuit
  **Typical values:** 10µF, 470nF, 100nF, 47nF
  **Applications:** IC power supply decoupling, bypass capacitors, compensation networks

#### 0805 Ceramic Capacitor

<FootprintSvg src="/pj/zudo-pd/footprint-svg/C0805.svg" alt="0805 Capacitor" minWidth="200px" minHeight="150px" />

**Package:** 0805 (2.0mm × 1.25mm)
**Used for:**

- Ceramic capacitors (10µF, 100nF)
- Output filter capacitors for linear regulators
  **LCSC:** [C15850](https://jlcpcb.com/partdetail/C15850) (10µF 25V), [C49678](https://jlcpcb.com/partdetail/C49678) (100nF 50V)
  **Applications:** Bulk decoupling, output filtering

#### D6.3mm Electrolytic Capacitor

<FootprintSvg src="/pj/zudo-pd/footprint-svg/CAP-SMD_BD6.3-L6.6-W6.6-FD.svg" alt="D6.3mm SMD Electrolytic Capacitor" minWidth="250px" minHeight="250px" />

**Package:** SMD Electrolytic (Ø6.3mm, 6.6mm × 6.6mm)
**Used for:**

- DC-DC converter output filter (C4, C22, C23: 470µF 16V)
- DC-DC converter input capacitors (C5, C7, C9: 100µF 25V)

**LCSC:** [C46550400](https://jlcpcb.com/partdetail/C46550400) (470µF 16V), [C22383804](https://jlcpcb.com/partdetail/C22383804) (100µF 25V)
**Applications:** Bulk energy storage for DC-DC converters

#### D10mm Electrolytic Capacitor

<FootprintSvg src="/pj/zudo-pd/footprint-svg/CAP-SMD_BD10.0-L10.3-W10.3-LS11.0-FD.svg" alt="D10mm SMD Electrolytic Capacitor" minWidth="300px" minHeight="300px" />

**Package:** SMD Electrolytic (Ø10.0mm, 10.3mm × 10.3mm)
**Used for:**

- DC-DC input capacitors (C3, C11: 470µF 25V)
- Linear regulator output capacitors (C14, C20, C21, C24, C25: 470µF 16V)

**LCSC:** [C2983319](https://jlcpcb.com/partdetail/C2983319) (470µF 25V), [C22387780](https://jlcpcb.com/partdetail/C22387780) (470µF 16V)
**Applications:** Bulk energy storage for input and output filtering

#### 1206 Ceramic Capacitor

<FootprintSvg src="/pj/zudo-pd/footprint-svg/C1206.svg" alt="1206 Capacitor" minWidth="200px" minHeight="150px" />

**Designator:** C1
**Package:** 1206 (3.2mm × 1.6mm)
**Value:** 10µF 25V
**LCSC:** [C7432781](https://jlcpcb.com/partdetail/C7432781)
**Function:** USB-PD input decoupling capacitor

### Resistors

#### 0603 Resistor

<FootprintSvg src="/pj/zudo-pd/footprint-svg/R0603.svg" alt="0603 Resistor" minWidth="200px" minHeight="150px" />

**Package:** 0603 (1.6mm × 0.8mm)
**Used for:**

- USB-C CC line resistors (R3, R12, R13: 5.1kΩ for 15V PD negotiation)
- DC-DC feedback resistors (R1-R6: 1kΩ, 10kΩ for voltage adjustment)
- Compensation resistor (R11: 56kΩ)

**LCSC:** [C23186](https://jlcpcb.com/partdetail/C23186) (5.1kΩ), [C25804](https://jlcpcb.com/partdetail/C25804) (10kΩ), [C21190](https://jlcpcb.com/partdetail/C21190) (1kΩ)
**Applications:** Voltage dividers, current limiting, pull-up/pull-down

#### 0805 Resistor

<FootprintSvg src="/pj/zudo-pd/footprint-svg/R0805.svg" alt="0805 Resistor" minWidth="200px" minHeight="150px" />

**Package:** 0805 (2.0mm × 1.25mm)
**Used for:**

- LED current limiting resistors (R7, R8, R9: 1kΩ)

**LCSC:** [C25623](https://jlcpcb.com/partdetail/C25623)
**Applications:** Higher power dissipation resistors for LED current limiting

### LEDs

#### 0603 LED

<FootprintSvg src="/pj/zudo-pd/footprint-svg/LED0603-RD.svg" alt="0603 LED" minWidth="200px" minHeight="150px" />

**Package:** 0603 (1.6mm × 0.8mm)
**Used for:** Power rail status indicators
**Colors:** Green, Blue, Red
**Applications:**

- LED2 (Green): +12V rail indicator - [C19171392](https://jlcpcb.com/partdetail/C19171392)
- LED3 (Blue): +5V rail indicator - [C5382145](https://jlcpcb.com/partdetail/C5382145)
- LED4 (Red): -12V rail indicator - [C2286](https://jlcpcb.com/partdetail/C2286)

---

## Protection Components

### PTC Resettable Fuses

#### PTC3 - F1206 (1.5A Hold, -12V Rail)

<FootprintSvg src="/pj/zudo-pd/footprint-svg/F1206.svg" alt="1206 PTC Resettable Fuse" minWidth="250px" minHeight="200px" />

**Designator:** PTC3
**Component:** BSMD1206-150-16V - PTC Resettable Fuse
**Package:** 1206 (3.2mm × 1.6mm)
**Specification:** 1.5A hold / 3.0A trip
**LCSC:** [C883133](https://jlcpcb.com/partdetail/C883133)
**Function:** -12V rail auto-reset overcurrent protection

#### PTC1 - F1210 (2.0A Hold, +12V Rail)

<FootprintSvg src="/pj/zudo-pd/footprint-svg/F1210.svg" alt="1210 PTC Resettable Fuse" minWidth="250px" minHeight="200px" />

**Designator:** PTC1
**Component:** SMD1210P200TF - PTC Resettable Fuse
**Package:** SMD1210 (3.2mm × 2.5mm)
**Specification:** 2.0A hold / 4.0A trip
**LCSC:** [C20808](https://jlcpcb.com/partdetail/C20808)
**Function:** +12V rail auto-reset overcurrent protection

#### PTC2 - F1812 (1.1A Hold, +5V Rail)

<FootprintSvg src="/pj/zudo-pd/footprint-svg/F1812.svg" alt="1812 PTC Resettable Fuse" minWidth="250px" minHeight="200px" />

**Designator:** PTC2
**Component:** [mSMD110-33V](../components/ptc-5v) - PTC Resettable Fuse
**Package:** 1812 (4.5mm × 3.2mm)
**Specification:** 1.1A hold / 2.2A trip
**LCSC:** [C70119](https://jlcpcb.com/partdetail/C70119)
**Function:** +5V rail auto-reset overcurrent protection

### Schottky Diode (SMA)

<FootprintSvg src="/pj/zudo-pd/footprint-svg/SMA_L4.3-W2.6-LS5.2-RD.svg" alt="SMA Diode Package" minWidth="250px" minHeight="150px" />

**Designators:** D1, D2, D3 (used in DC-DC converter flyback circuits)
**Component:** SS34 - 3A 40V Schottky Barrier Diode
**Package:** SMA (4.3mm × 2.6mm)
**LCSC:** [C8678](https://jlcpcb.com/partdetail/C8678)
**Function:** Flyback diode for LM2596S buck converters

### TVS Diodes

#### TVS1, TVS3 - SMAJ15A (±12V Overvoltage Protection)

<FootprintSvg src="/pj/zudo-pd/footprint-svg/D-FLAT_L4.3-W2.6-LS5.3-RD.svg" alt="SMAJ15A SMA TVS Diode" minWidth="250px" minHeight="150px" />

**Designators:** TVS1, TVS3
**Component:** [SMAJ15A](../components/smaj15a) - 15V Unidirectional TVS Diode
**Package:** SMA (4.3mm × 2.6mm)
**Specification:** 15V standoff, 400W peak power
**LCSC:** [C571368](https://jlcpcb.com/partdetail/C571368)
**Function:** Overvoltage protection for ±12V rails

#### TVS2 - SD05 (+5V Overvoltage Protection)

<FootprintSvg src="/pj/zudo-pd/footprint-svg/SOD-323_L1.8-W1.3-LS2.5-FD.svg" alt="SD05 SOD-323 TVS Diode" minWidth="200px" minHeight="150px" />

**Designator:** TVS2
**Component:** [SD05](../components/sd05) - 5V Unidirectional TVS Diode
**Package:** SOD-323 (1.8mm × 1.3mm)
**LCSC:** [C502527](https://jlcpcb.com/partdetail/C502527)
**Function:** Overvoltage protection for +5V DC power rail

---

## Connectors

### J10-J11 - Eurorack Power Connector (16-pin)

<FootprintSvg src="/pj/zudo-pd/footprint-svg/HDR-TH_16P-P2.54-H-M-R2-C8-S2.54.svg" alt="16-pin 2.54mm Header (Eurorack)" minWidth="400px" minHeight="200px" />

**Designators:** J10, J11 (2× units)
**Component:** 2541WR-2x08P - 2×8 Pin Header (Standard)
**Package:** Through-hole 16-pin header (2×8, 2.54mm pitch)
**LCSC:** [C5383092](https://jlcpcb.com/partdetail/C5383092)
**Function:** Eurorack power output connectors

**Note:** Standard pin headers. For box/shrouded connectors (commonly used in Eurorack), source the mating connector separately from Tayda Electronics, Mouser, or Digikey.

### J6-J9 - FASTON 250 Power Terminals

<FootprintSvg src="/pj/zudo-pd/footprint-svg/CONN-TH_1217754-1.svg" alt="FASTON 250 PCB Terminal" minWidth="150px" minHeight="150px" />

**Designators:** J6, J7, J8, J9 (4× units)
**Component:** 1217754-1 - FASTON 250 PCB Tab Terminal
**Package:** Through-hole (6.35mm tab width)
**LCSC:** [C305825](https://jlcpcb.com/partdetail/C305825)
**Current Rating:** 7A continuous
**Function:** Busboard power output (+12V, -12V, +5V, GND)

**Note:** Industrial-grade quick-connect terminals for heavy-duty power distribution to Eurorack busboards. Requires matching FASTON 250 receptacles on busboard side.

---

## Footprint Management

All footprints in this project were downloaded using [easyeda2kicad.py](https://github.com/uPesy/easyeda2kicad.py) from the LCSC/EasyEDA database.

### Download Pre-Generated Footprints

**🔗 [Download all footprints from GitHub](https://github.com/Takazudo/zudo-pd/tree/main/footprints)**

The `/footprints/kicad/` directory contains all `.kicad_mod` files ready for use.

### Adding New Footprints

```bash
# Download footprint by LCSC ID
easyeda2kicad --lcsc_id <LCSC_ID> --footprint

# Copy to project
cp ~/Documents/Kicad/easyeda2kicad/easyeda2kicad.pretty/*.kicad_mod ./footprints/kicad/
```

### Generating Preview Images

```bash
# 1. Export to SVG using KiCad CLI
kicad-cli fp export svg footprints/kicad/zudo-power.pretty -o footprints/images --black-and-white

# 2. Remove REF** placeholder text
python3 footprints/scripts/clean-svg-refs.py footprints/images/

# 3. Copy to documentation
cp footprints/images/*.svg doc/docs/_fragments/footprints/
```

## See Also

- [Bill of Materials](../overview/bom.md) - Complete component list with specifications
- [Overview](../overview/overview.md) - Project technical overview
- [Quick Reference](../inbox/quick-reference.md) - Specification summary
