# Box Header Guard for Eurorack Power Connector

3D printable shrouded/keyed box header frame that converts standard 2×8 pin headers into IDC-compatible Eurorack power connectors.

## Target Component

- **LCSC Part**: [C5383092](https://jlcpcb.com/partdetail/C5383092)
- **Part Number**: 2541WR-2x08P
- **Type**: 2×8 pin header (16-pin), 2.54mm pitch

## Files

| File | Description |
|------|-------------|
| `box-header.scad` | OpenSCAD source file |
| `box-header.stl` | 3D printable STL |
| `C5383092.pdf` | Pin header datasheet (if present) |

## Key Dimensions

| Parameter | Value | Source |
|-----------|-------|--------|
| Pin pitch | 2.54mm | Datasheet |
| Pin size | 0.64mm (square) | Datasheet SQ.0.64 |
| Row spacing | 2.54mm | Standard |
| Box height | 8.9mm | Standard IDC |
| Bottom thickness | 1.0mm | Adjusted (0.5mm too thin) |
| Pin hole diameter | 1.4mm | Adjusted (0.8mm, 1.0mm too tight) |
| Slot width | 0.6mm | Adjusted after print test |

## Design Features

- **Center divider** on bottom surface for alignment
- **1.4mm pin holes** for proper fit (0.8mm, 1.0mm were too tight)
- **Key notch** for polarized connection (prevents reverse insertion)
- **Thicker walls** (1.5mm) for print durability

## Print Settings

- Layer height: 0.2mm recommended
- No supports needed
- Print with bottom face down

## License

Original design by John Stäck 2018, licensed under [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/).

Modifications:
- Changed bottom thickness to 1.0mm (0.5mm was too thin)
- Changed pin hole diameter to 1.4mm (0.8mm, 1.0mm were too tight)
- Added center divider
- Adjusted slot width to 0.6mm

## Usage

Press-fit onto the 2×8 pin headers (J2-J5) on the PCB to create shrouded connectors compatible with standard Eurorack 16-pin ribbon cables.
