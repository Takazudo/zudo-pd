# Footprint Preview

Visual reference of all PCB footprints used in this USB-PD power supply project. All footprints are sourced from LCSC/EasyEDA and converted to KiCad format.

Click on any footprint to view it in fullscreen.

## USB-PD Stage

### U1 - CH224D USB PD Controller

import FootprintSvg from '@site/src/components/FootprintSvg';
import CH224D from '@site/static/footprints-svg/QFN-20_L3.0-W3.0-P0.40-BL-EP1.7.svg';

<FootprintSvg src={CH224D} alt="CH224D QFN-20 Package" minWidth="300px" minHeight="300px" />

**Designator:** U1
**Component:** [CH224D](../components/ch224d) - USB PD Controller
**Package:** QFN-20 (3.0mm × 3.0mm, 0.40mm pitch)
**LCSC:** [C3975094](https://jlcpcb.com/partdetail/C3975094)
**Function:** Negotiates 15V from USB-C PD adapter

### J1 - USB Type-C Connector

import USBC from '@site/static/footprints-svg/TYPE-C-SMD_TYPE-C-6P.svg';

<FootprintSvg src={USBC} alt="USB Type-C 6P Connector" minWidth="300px" minHeight="200px" />

**Designator:** J1
**Component:** USB-TYPE-C-009 - 6P Type-C Female Connector
**Package:** SMD Type-C 6P Female
**LCSC:** [C2927029](https://jlcpcb.com/partdetail/C2927029)
**Function:** USB-C PD power input

---

## DC-DC Converter Stage

### U2, U3, U4 - LM2596S-ADJ Buck Converter

import LM2596S from '@site/static/footprints-svg/TO-263-5_L10.2-W8.9-P1.70-BR.svg';

<FootprintSvg src={LM2596S} alt="LM2596S TO-263-5 Package" minWidth="300px" minHeight="200px" />

**Designators:** U2, U3, U4 (3× units)
**Component:** [LM2596S-ADJ(UMW)](../components/lm2596s-adj) - Adjustable 3A Buck Converter
**Package:** TO-263-5 (10.2mm × 8.9mm)
**LCSC:** [C347423](https://jlcpcb.com/partdetail/C347423)
**Function:** DC-DC conversion (+13.5V, +7.5V, -13.5V outputs)

### L1, L2 - 100µH Power Inductor

import Inductor from '@site/static/footprints-svg/IND-SMD_L13.8-W12.8.svg';

<FootprintSvg src={Inductor} alt="100µH Power Inductor" minWidth="300px" minHeight="300px" />

**Designators:** L1, L2 (2× units)
**Component:** CYA1265-100UH - 100µH 4.5A Power Inductor
**Package:** SMD Power Inductor (13.8mm × 12.8mm)
**LCSC:** [C19268674](https://jlcpcb.com/partdetail/C19268674)
**Function:** Energy storage for LM2596S buck converters (U2, U3)

---

## Linear Regulator Stage

### U6 - L7812CD2T-TR (+12V Linear Regulator)

import LM7812 from '@site/static/footprints-svg/TO-263-2_L10.0-W9.1-P5.08-LS15.2-TL.svg';

<FootprintSvg src={LM7812} alt="L7812CD2T TO-263-2 Package" minWidth="300px" minHeight="200px" />

**Designator:** U6
**Component:** [L7812CD2T-TR](../components/l7812cv) - +12V 1.5A Linear Regulator
**Package:** TO-263-2 (10.0mm × 9.1mm)
**LCSC:** [C13456](https://jlcpcb.com/partdetail/C13456)
**Function:** Regulates +13.5V to +12V with low noise

### U7 - L7805ABD2T-TR (+5V Linear Regulator)

import LM7805 from '@site/static/footprints-svg/TO-263-2_L10.0-W9.2-P5.08-LS15.3-TL-CW.svg';

<FootprintSvg src={LM7805} alt="L7805ABD2T TO-263-2 Package" minWidth="300px" minHeight="200px" />

**Designator:** U7
**Component:** [L7805ABD2T-TR](../components/l7805abd2t) - +5V 1.5A Linear Regulator
**Package:** TO-263-2 (10.0mm × 9.2mm)
**LCSC:** [C86206](https://jlcpcb.com/partdetail/C86206)
**Function:** Regulates +7.5V to +5V with low noise

### U8 - CJ7912 (-12V Linear Regulator)

import LM7912 from '@site/static/footprints-svg/TO-252-3_L6.5-W5.8-P4.58-BL.svg';

<FootprintSvg src={LM7912} alt="CJ7912 TO-252-3 Package" minWidth="250px" minHeight="200px" />

**Designator:** U8
**Component:** [CJ7912](../components/cj7912) - -12V 1.5A Linear Regulator
**Package:** TO-252-3 (6.5mm × 5.8mm)
**LCSC:** [C94173](https://jlcpcb.com/partdetail/C94173)
**Function:** Regulates -13.5V to -12V with low noise

---

## Passive Components

### Capacitors

#### 0603 Ceramic Capacitor

import C0603 from '@site/static/footprints-svg/C0603.svg';

<FootprintSvg src={C0603} alt="0603 Capacitor" minWidth="200px" minHeight="150px" />

**Package:** 0603 (1.6mm × 0.8mm)
**Used for:**

- Ceramic capacitors (470nF for CH224D, 47nF for LM2586 compensation)
- High-frequency decoupling throughout circuit
  **Typical values:** 10µF, 470nF, 100nF, 47nF
  **Applications:** IC power supply decoupling, bypass capacitors, compensation networks

#### 0805 Ceramic Capacitor

import C0805 from '@site/static/footprints-svg/C0805.svg';

<FootprintSvg src={C0805} alt="0805 Capacitor" minWidth="200px" minHeight="150px" />

**Package:** 0805 (2.0mm × 1.25mm)
**Used for:**

- Ceramic capacitors (10µF, 100nF)
- Output filter capacitors for linear regulators
  **LCSC:** [C15850](https://jlcpcb.com/partdetail/C15850) (10µF 25V), [C49678](https://jlcpcb.com/partdetail/C49678) (100nF 50V)
  **Applications:** Bulk decoupling, output filtering

#### D6.3mm Electrolytic Capacitor

import CapD63 from '@site/static/footprints-svg/CAP-SMD_BD6.3-L6.6-W6.6-FD.svg';

<FootprintSvg src={CapD63} alt="D6.3mm SMD Electrolytic Capacitor" minWidth="250px" minHeight="250px" />

**Package:** SMD Electrolytic (Ø6.3mm, 6.6mm × 6.6mm)
**Used for:**

- Linear regulator input/output capacitors (C14-C19: 470µF 10V)
- DC-DC converter input capacitors (C5, C7: 100µF 25V)
  **LCSC:** [C335982](https://jlcpcb.com/partdetail/C335982) (470µF 10V), [C22383804](https://jlcpcb.com/partdetail/C22383804) (100µF 25V)
  **Applications:** Most common electrolytic in this design - bulk energy storage

#### D18mm Large Electrolytic Capacitor

import CapLarge from '@site/static/footprints-svg/CAP-SMD_BD18.0-L19.0-W19.0-LS20.4-FD.svg';

<FootprintSvg src={CapLarge} alt="Large SMD Electrolytic Capacitor" minWidth="300px" minHeight="300px" />

**Designator:** C1
**Package:** SMD Electrolytic (Ø18.0mm, 19.0mm × 19.0mm)
**Value:** 470µF 25V
**LCSC:** [C3351](https://jlcpcb.com/partdetail/C3351)
**Function:** Main input bulk capacitor for USB-PD 15V supply

### Resistors

#### 0603 Resistor

import R0603 from '@site/static/footprints-svg/R0603.svg';

<FootprintSvg src={R0603} alt="0603 Resistor" minWidth="200px" minHeight="150px" />

**Package:** 0603 (1.6mm × 0.8mm)
**Used for:**

- USB-C CC line resistors (R1, R2: 5.1kΩ for 15V PD negotiation)
- DC-DC feedback resistors (R3-R8: 1kΩ, 10kΩ for voltage adjustment)
- LED current limiting resistors
  **Typical values:** 1kΩ, 5.1kΩ, 10kΩ, 330Ω
  **Applications:** Voltage dividers, current limiting, pull-up/pull-down

### LEDs

#### 0805 LED

import LED0603 from '@site/static/footprints-svg/LED0603-RD.svg';

<FootprintSvg src={LED0603} alt="0805 LED" minWidth="200px" minHeight="150px" />

**Package:** 0805 (2.0mm × 1.25mm)
**Used for:** Power rail status indicators
**Colors:** Red, Green, Blue
**Applications:**

- LED1 (Green): Power good indicator
- LED2 (Red): Fault indicator
- LED3 (Blue): +5V rail indicator

---

## Protection Components

### PTC Resettable Fuses

#### PTC3 - F1206 (1.0A Hold, -12V Rail)

import PTC1206 from '@site/static/footprints-svg/F1206.svg';

<FootprintSvg src={PTC1206} alt="1206 PTC Resettable Fuse" minWidth="250px" minHeight="200px" />

**Designator:** PTC3
**Component:** [JK-nSMD100/16V](../components/ptc-12v-neg) - PTC Resettable Fuse
**Package:** 1206 (3.2mm × 1.6mm)
**Specification:** 1.0A hold / 2.0A trip
**LCSC:** [C2830246](https://jlcpcb.com/partdetail/C2830246)
**Function:** -12V rail auto-reset overcurrent protection

#### PTC1 - F1210 (1.5A Hold, +12V Rail)

import PTC1210 from '@site/static/footprints-svg/F1210.svg';

<FootprintSvg src={PTC1210} alt="1210 PTC Resettable Fuse" minWidth="250px" minHeight="200px" />

**Designator:** PTC1
**Component:** [SMD1210P150TF/16](../components/ptc-12v) - PTC Resettable Fuse
**Package:** SMD1210 (3.2mm × 2.5mm)
**Specification:** 1.5A hold / 3.0A trip
**LCSC:** [C7529589](https://jlcpcb.com/partdetail/C7529589)
**Function:** +12V rail auto-reset overcurrent protection

#### PTC2 - F1812 (1.1A Hold, +5V Rail)

import PTC1812 from '@site/static/footprints-svg/F1812.svg';

<FootprintSvg src={PTC1812} alt="1812 PTC Resettable Fuse" minWidth="250px" minHeight="200px" />

**Designator:** PTC2
**Component:** [mSMD110-33V](../components/ptc-5v) - PTC Resettable Fuse
**Package:** 1812 (4.5mm × 3.2mm)
**Specification:** 1.1A hold / 2.2A trip
**LCSC:** [C70119](https://jlcpcb.com/partdetail/C70119)
**Function:** +5V rail auto-reset overcurrent protection

### SMD Fuses

#### F1 - 2410 SMD Fuse (2A, +12V Rail)

import Fuse2410 from '@site/static/footprints-svg/FUSE-SMD_L6.1-W2.6.svg';

<FootprintSvg src={Fuse2410} alt="2410 SMD Fuse" minWidth="250px" minHeight="150px" />

**Designator:** F1
**Component:** 6125FA2A - Fast-Acting SMD Fuse
**Package:** 2410 (6.1mm × 2.6mm)
**Specification:** 2A 250V
**LCSC:** [C5183824](https://jlcpcb.com/partdetail/C5183824)
**Function:** +12V rail short circuit protection (backup to PTC1)

#### F2, F3 - SMD Fuse 1.5A (±5V/±12V Rails)

import FuseLarge from '@site/static/footprints-svg/FUSE-SMD_L10.1-W3.1.svg';

<FootprintSvg src={FuseLarge} alt="Large SMD Fuse" minWidth="300px" minHeight="150px" />

**Designators:** F2, F3
**Component:** Fast-Acting SMD Fuse
**Package:** SMD (10.1mm × 3.1mm)
**Specification:** 1.5A 250V
**LCSC:** [C95352](https://jlcpcb.com/partdetail/C95352)
**Function:** +5V and -12V rail short circuit protection (backup to PTC2, PTC3)

### Schottky Diode (SMA)

import DiodeSMA from '@site/static/footprints-svg/SMA_L4.4-W2.8-LS5.4-RD.svg';

<FootprintSvg src={DiodeSMA} alt="SMA Diode Package" minWidth="250px" minHeight="150px" />

**Designators:** D1, D2, D3 (used in DC-DC converter flyback circuits)
**Component:** SS34 - 3A 40V Schottky Barrier Diode
**Package:** SMA (4.4mm × 2.8mm)
**LCSC:** [C8678](https://jlcpcb.com/partdetail/C8678)
**Function:** Flyback diode for LM2596S buck converters

### TVS Diodes

#### TVS1, TVS3 - SMAJ15A (±12V Overvoltage Protection)

import TVSSMA from '@site/static/footprints-svg/D-FLAT_L4.3-W2.6-LS5.3-RD.svg';

<FootprintSvg src={TVSSMA} alt="SMAJ15A SMA TVS Diode" minWidth="250px" minHeight="150px" />

**Designators:** TVS1, TVS3
**Component:** [SMAJ15A](../components/smaj15a) - 15V Unidirectional TVS Diode
**Package:** SMA (4.3mm × 2.6mm)
**Specification:** 15V standoff, 400W peak power
**LCSC:** [C571368](https://jlcpcb.com/partdetail/C571368)
**Function:** Overvoltage protection for ±12V rails

#### TVS2 - PRTR5V0U2X (+5V Overvoltage Protection)

**Designator:** TVS2
**Component:** [PRTR5V0U2X](../components/prtr5v0u2x) - 5V Bidirectional TVS Diode
**Package:** SOT-143
**LCSC:** [C5199240](https://jlcpcb.com/partdetail/C5199240)
**Function:** Overvoltage protection for +5V rail
**Note:** Footprint not available - download failed from EasyEDA API

---

## Connectors

### J2 - Eurorack Power Connector (16-pin)

import HeaderEuro from '@site/static/footprints-svg/HDR-TH_16P-P2.54-H-M-R2-C8-S2.54.svg';

<FootprintSvg src={HeaderEuro} alt="16-pin 2.54mm Header (Eurorack)" minWidth="400px" minHeight="200px" />

**Designator:** J2
**Component:** 2541WR-2x08P - 2×8 Pin Header (Standard)
**Package:** Through-hole 16-pin header (2×8, 2.54mm pitch)
**LCSC:** [C5383092](https://jlcpcb.com/partdetail/C5383092)
**Stock:** 6,813 units
**Function:** Eurorack power output connector

**Note:** This is a standard pin header. For box/shrouded connectors (commonly used in Eurorack), source the mating connector separately from Tayda Electronics, Mouser, or Digikey.

### 3-pin Header

import Header3P from '@site/static/footprints-svg/HDR-TH_3P-P2.54-V-M.svg';

<FootprintSvg src={Header3P} alt="3-pin 2.54mm Header" minWidth="200px" minHeight="200px" />

**Package:** Through-hole 3-pin vertical header (2.54mm pitch)
**Function:** General purpose connection header

### 6-pin SMD Header

import Header6P from '@site/static/footprints-svg/HDR-SMD_6P-P2.00-V-M_XBK_R2.svg';

<FootprintSvg src={Header6P} alt="6-pin 2.00mm SMD Header" minWidth="250px" minHeight="200px" />

**Package:** SMD 6-pin vertical header (2.00mm pitch)
**Function:** General purpose SMD connection header

---

## Footprint Management

All footprints in this project were downloaded using [easyeda2kicad.py](https://github.com/uPesy/easyeda2kicad.py) from the LCSC/EasyEDA database.

### Download Pre-Generated Footprints

**🔗 [Download all footprints from GitHub](https://github.com/Takazudo/zudo-power-usb-pd/tree/main/footprints)**

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

- [Bill of Materials](../components/bom.md) - Complete component list with specifications
- [Overview](./overview.md) - Project technical overview
- [Quick Reference](./quick-reference.md) - Specification summary
