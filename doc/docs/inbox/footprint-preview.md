# Footprint Preview

Visual reference of all PCB footprints used in this USB-PD power supply project. All footprints are sourced from LCSC/EasyEDA and converted to KiCad format.

Click on any footprint to view it in fullscreen.

## USB-PD Stage

### CH224D - USB PD Controller

import FootprintSvg from '@site/src/components/FootprintSvg';
import CH224D from '@site/static/footprints-svg/QFN-20_L3.0-W3.0-P0.40-BL-EP1.7.svg';

<FootprintSvg src={CH224D} alt="CH224D QFN-20 Package" minWidth="300px" minHeight="300px" />

**Package:** QFN-20 (3.0mm × 3.0mm, 0.40mm pitch)
**LCSC:** C3975094
**Part:** CH224D

### USB Type-C Connector

import USBC from '@site/static/footprints-svg/TYPE-C-SMD_TYPE-C-6P.svg';

<FootprintSvg src={USBC} alt="USB Type-C 6P Connector" minWidth="300px" minHeight="200px" />

**Package:** SMD Type-C 6P Female
**LCSC:** C2927029
**Part:** USB-TYPE-C-009

---

## DC-DC Converter Stage

### LM2596S-ADJ - Buck Converter

import LM2596S from '@site/static/footprints-svg/TO-263-5_L10.2-W8.9-P1.70-BR.svg';

<FootprintSvg src={LM2596S} alt="LM2596S TO-263-5 Package" minWidth="300px" minHeight="200px" />

**Package:** TO-263-5 (10.2mm × 8.9mm)
**LCSC:** C347423
**Part:** LM2596S-ADJ(UMW)

### ICL7660M - Voltage Inverter

import ICL7660 from '@site/static/footprints-svg/SOP-8_L4.9-W3.9-P1.27-LS6.0-BL.svg';

<FootprintSvg src={ICL7660} alt="ICL7660M SOP-8 Package" minWidth="250px" minHeight="200px" />

**Package:** SOP-8 (4.9mm × 3.9mm, 1.27mm pitch)
**LCSC:** C356724
**Part:** ICL7660M/TR

---

## Linear Regulator Stage

### LM7812 - +12V Regulator

import LM7812 from '@site/static/footprints-svg/TO-220-3_L10.0-W4.5-P2.54-L.svg';

<FootprintSvg src={LM7812} alt="LM7812 TO-220-3 Package" minWidth="250px" minHeight="250px" />

**Package:** TO-220-3 (10.0mm × 4.5mm)
**LCSC:** C2914
**Part:** L7812CV-DG

### LM7805 - +5V Regulator

import LM7805 from '@site/static/footprints-svg/TO-263-2_L10.0-W9.2-P5.08-LS15.3-TL-CW.svg';

<FootprintSvg src={LM7805} alt="LM7805 TO-263-2 Package" minWidth="300px" minHeight="200px" />

**Package:** TO-263-2 (10.0mm × 9.2mm)
**LCSC:** C86206
**Part:** L7805ABD2T-TR

### LM7912 - -12V Regulator

import LM7912 from '@site/static/footprints-svg/TO-252-3_L6.5-W5.8-P4.58-BL.svg';

<FootprintSvg src={LM7912} alt="LM7912 TO-252-3 Package" minWidth="250px" minHeight="200px" />

**Package:** TO-252-3 (6.5mm × 5.8mm)
**LCSC:** C94173
**Part:** CJ7912

---

## Passive Components

### Capacitors

#### 0603 Capacitor

import C0603 from '@site/static/footprints-svg/C0603.svg';

<FootprintSvg src={C0603} alt="0603 Capacitor" minWidth="200px" minHeight="150px" />

**Package:** 0603 (1.6mm × 0.8mm)
**Used for:** Ceramic capacitors (10µF, 470nF, 100nF)

#### Small Electrolytic Capacitor

import CapSmall from '@site/static/footprints-svg/CAP-SMD_BD4.0-L4.3-W4.3-LS5.0-FD.svg';

<FootprintSvg src={CapSmall} alt="Small SMD Electrolytic Capacitor" minWidth="250px" minHeight="250px" />

**Package:** SMD Electrolytic (Ø4.0mm, 4.3mm × 4.3mm)
**LCSC:** C335982
**Value:** 470µF 10V

#### Large Electrolytic Capacitor

import CapLarge from '@site/static/footprints-svg/CAP-SMD_BD18.0-L19.0-W19.0-LS20.4-FD.svg';

<FootprintSvg src={CapLarge} alt="Large SMD Electrolytic Capacitor" minWidth="300px" minHeight="300px" />

**Package:** SMD Electrolytic (Ø18.0mm, 19.0mm × 19.0mm)
**LCSC:** C3351
**Value:** 470µF 25V

### Resistors

#### 0603 Resistor

import R0603 from '@site/static/footprints-svg/R0603.svg';

<FootprintSvg src={R0603} alt="0603 Resistor" minWidth="200px" minHeight="150px" />

**Package:** 0603 (1.6mm × 0.8mm)
**Used for:** Various resistor values (1kΩ, 5.1kΩ, 10kΩ, etc.)

### LEDs

#### 0603 LED

import LED0603 from '@site/static/footprints-svg/LED0603-RD.svg';

<FootprintSvg src={LED0603} alt="0603 LED" minWidth="200px" minHeight="150px" />

**Package:** 0603 (1.6mm × 0.8mm)
**Colors:** Red, Green, Blue

---

## Protection Components

### Schottky Diode (SMA)

import DiodeSMA from '@site/static/footprints-svg/SMA_L4.4-W2.8-LS5.4-RD.svg';

<FootprintSvg src={DiodeSMA} alt="SMA Diode Package" minWidth="250px" minHeight="150px" />

**Package:** SMA (4.4mm × 2.8mm)
**LCSC:** C8678
**Part:** SS34 (3A 40V Schottky)

### TVS Diode (SOD-123FL)

import DiodeSOD from '@site/static/footprints-svg/SOD-123FL_L2.8-W1.8-LS3.7-RD.svg';

<FootprintSvg src={DiodeSOD} alt="SOD-123FL Diode Package" minWidth="200px" minHeight="150px" />

**Package:** SOD-123FL (2.8mm × 1.8mm)
**Used for:** TVS protection diodes

---

## Connectors

### Eurorack Power Connector (16-pin)

import HeaderEuro from '@site/static/footprints-svg/HDR-TH_16P-P2.54-H-M-R2-C8-S2.54.svg';

<FootprintSvg src={HeaderEuro} alt="16-pin 2.54mm Header (Eurorack)" minWidth="400px" minHeight="200px" />

**Package:** Through-hole 16-pin header (2×8, 2.54mm pitch)
**Usage:** Eurorack modular synth power output

### 3-pin Header

import Header3P from '@site/static/footprints-svg/HDR-TH_3P-P2.54-V-M.svg';

<FootprintSvg src={Header3P} alt="3-pin 2.54mm Header" minWidth="200px" minHeight="200px" />

**Package:** Through-hole 3-pin vertical header (2.54mm pitch)

### 6-pin SMD Header

import Header6P from '@site/static/footprints-svg/HDR-SMD_6P-P2.00-V-M_XBK_R2.svg';

<FootprintSvg src={Header6P} alt="6-pin 2.00mm SMD Header" minWidth="250px" minHeight="200px" />

**Package:** SMD 6-pin vertical header (2.00mm pitch)

### DC Input Jack

import DCJack from '@site/static/footprints-svg/DC-IN-TH_DC550250-0366-2H.svg';

<FootprintSvg src={DCJack} alt="DC Input Jack" minWidth="300px" minHeight="250px" />

**Package:** Through-hole DC barrel jack

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

- [Bill of Materials](../parts/bom.md) - Complete component list with specifications
- [Overview](./overview.md) - Project technical overview
- [Quick Reference](./quick-reference.md) - Specification summary
