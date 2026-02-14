# KiCad Footprints

This directory contains KiCad footprint files (.kicad_mod) for components used in this USB-PD power supply project. All footprints were downloaded from LCSC/EasyEDA using the [easyeda2kicad.py](https://github.com/uPesy/easyeda2kicad.py) tool.

## Key Component Footprints

### USB-PD Stage
- **QFN-20_L3.0-W3.0-P0.40-BL-EP1.7.kicad_mod** - CH224D USB PD Controller (C3975094)
- **TYPE-C-SMD_TYPE-C-6P.kicad_mod** - USB Type-C 6P Female Connector (C456012)

### DC-DC Converter Stage
- **TO-263-5_L10.2-W8.9-P1.70-BR.kicad_mod** - LM2596S-ADJ Buck Converter (C347423)
- **SOP-8_L4.9-W3.9-P1.27-LS6.0-BL.kicad_mod** - ICL7660M Voltage Inverter (C356724)

### Linear Regulator Stage
- **TO-220-3_L10.0-W4.5-P2.54-L.kicad_mod** - LM7812CV +12V Regulator (C2914)
- **TO-263-2_L10.0-W9.2-P5.08-LS15.3-TL-CW.kicad_mod** - L7805ABD2T +5V Regulator (C86206)
- **TO-252-3_L6.5-W5.8-P4.58-BL.kicad_mod** - CJ7912 -12V Regulator (C94173)

### Passive Components
- **C0603.kicad_mod** - 0603 Capacitor
- **R0603.kicad_mod** - 0603 Resistor
- **CAP-SMD_BD4.0-L4.3-W4.3-LS5.0-FD.kicad_mod** - SMD Electrolytic Capacitor (small)
- **CAP-SMD_BD18.0-L19.0-W19.0-LS20.4-FD.kicad_mod** - SMD Electrolytic Capacitor (large)

### Protection & Indicators
- **SMA_L4.4-W2.8-LS5.4-RD.kicad_mod** - SMA Diode Package (TVS, Schottky)
- **SOD-123FL_L2.8-W1.8-LS3.7-RD.kicad_mod** - SOD-123FL Diode Package
- **LED0603-RD.kicad_mod** - 0603 LED (Red)
- **LED0603-R-RD_WHITE.kicad_mod** - 0603 LED (White)

### Connectors
- **HDR-TH_16P-P2.54-H-M-R2-C8-S2.54.kicad_mod** - 16-pin 2.54mm Through-hole Header (Eurorack Power)
- **HDR-TH_3P-P2.54-V-M.kicad_mod** - 3-pin 2.54mm Through-hole Header
- **HDR-SMD_6P-P2.00-V-M_XBK_R2.kicad_mod** - 6-pin 2.00mm SMD Header
- **HDR-SMD_8P-P2.54-V-M-LS4.8_R2.kicad_mod** - 8-pin 2.54mm SMD Header
- **DC-IN-TH_DC550250-0366-2H.kicad_mod** - DC Input Jack (Through-hole)

## Usage

### In KiCad
1. Add this directory to your KiCad footprint library list
2. Select footprints when assigning components in your schematic

### Downloading Additional Footprints

To download footprints for other components:

```bash
easyeda2kicad --lcsc_id <LCSC_ID> --footprint
```

The footprints will be saved to `~/Documents/Kicad/easyeda2kicad/easyeda2kicad.pretty/` and can be copied to this directory.

Example:
```bash
# Download CH224D footprint
easyeda2kicad --lcsc_id C3975094 --footprint

# Copy to project
cp ~/Documents/Kicad/easyeda2kicad/easyeda2kicad.pretty/*.kicad_mod ./
```

## Notes

- All LCSC part numbers are referenced in `/doc/docs/inbox/parts-list.md`
- Footprints include pads, silkscreen, and courtyard layers
- Some footprints may include 3D model references (if available from EasyEDA)
