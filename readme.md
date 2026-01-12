# USB-PD Powered Modular Synthesizer Power Supply

A low-noise power module design that takes USB-C PD 15V input and provides ±12V/+5V power for modular synthesizers.

## Documentation

**Main documentation is in the `/doc/` Docusaurus site**

```bash
cd doc
pnpm install
pnpm start
```

Open http://localhost:3000 in your browser to view the documentation.

### Key Documents

- **[Project Overview](doc/docs/overview/overview.md)** - Design goals, architecture, features
- **[Circuit Diagrams](doc/docs/overview/circuit-diagrams.mdx)** - Complete circuit configuration
- **[Bill of Materials](doc/docs/overview/bom.md)** - JLCPCB-compatible BOM
- **[Quick Reference](doc/docs/inbox/quick-reference.md)** - Common specs, formulas, FAQ

## Project Overview

### Design Goals

A modular synthesizer power supply powered by USB-C PD chargers.

- **Input**: USB-C PD 15V 3A (max 45W)
- **Output**: +12V/1.2A, -12V/1.0A, +5V/1.2A
- **Ripple**: <1mVp-p (low noise optimized for modular synths)
- **Protection**: PTC auto-reset + fuse backup (beginner-friendly)
- **Sourcing**: All parts JLCPCB-compatible (reliable supply, low cost)

### 4-Stage Architecture

```
USB-C 15V ──┬─→ +13.5V (DC-DC) ──→ +12V (LDO) ──→ +12V OUT
            │
            ├─→ +7.5V  (DC-DC) ──→ +5V  (LDO) ──→ +5V OUT
            │
            └─→ -15V (Inverter) ──→ -13.5V (DC-DC) ──→ -12V (LDO) ──→ -12V OUT
```

**DC-DC + LDO Two-Stage Design**: Balancing efficiency and noise

- DC-DC ensures efficiency (85-90%)
- LDO removes noise (<1mVp-p)
- Overall efficiency: 75-80%

## Current Status

### Completed

- Circuit design complete (4-stage architecture)
- Main component selection complete (JLCPCB part numbers confirmed)
- Detailed documentation complete

### Next Steps

1. **Search for remaining parts** (PTC fuses × 3, 2A fuse × 1)
2. **KiCad PCB design** (4-layer board recommended)
3. **Order prototype** (JLCPCB SMT)
4. **Performance testing** (ripple, efficiency, thermal)

## Repository Structure

- `/doc/` - Docusaurus documentation site **← Main documentation**
- `/footprints/` - PCB footprint images (CH224Q, USB-C)
- `/diagram-sources/` - Python schemdraw scripts for circuit diagrams
- `/symbols/` - KiCad symbol library
- `/3dp-files/` - 3D printable files
- `/jlcpcb-templates/` - JLCPCB order templates
- `/__inbox/` - Working directory (temporary files, gitignored)

## Original Concept

The reliable Doepfer power supplies use DC-DC converters for voltage conversion, with linear regulators (LM7812/LM7912) and capacitors at the final stage to reduce switching noise.

Following this design philosophy, this project obtains 15V power from USB-PD and provides low-noise ±12V/+5V power required by modular synthesizers.

- **+12V**: 1200mA (most commonly used voltage in modular synths)
- **-12V**: 800mA (used by VCOs/VCAs)
- **+5V**: 500mA (used by digital modules)

These values are based on typical usage ratios in standard modular synthesizer systems.

## Reference Links

- [JLCPCB Parts Library](https://jlcpcb.com/parts)
- [KiCad Official Site](https://www.kicad.org/)
- [CH224Q Datasheet](https://www.wch-ic.com/products/CH224.html)

## License

This project is open source. Hardware design files can be freely used and modified.
