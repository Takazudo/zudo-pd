---
sidebar_position: 1
pagination_next: null
pagination_prev: null
---

# Parts Documentation

Detailed documentation about components and parts used in the USB-PD modular synthesizer power supply.

## Protection Components

Critical transient voltage suppression (TVS) diodes providing overvoltage and ESD protection:

### TVS Diodes

- **[SMAJ15A](./smaj15a.md)** - 15V Unidirectional TVS Diode
  - Package: SMA (DO-214AC)
  - Application: +12V and -12V rail protection (TVS1, TVS3)
  - Peak pulse power: 400W
  - JLCPCB: C571368

- **[PRTR5V0U2X](./prtr5v0u2x.md)** - 5V Bidirectional Dual-Channel TVS Diode
  - Package: SOT-143 (4-pin)
  - Application: +5V rail protection (TVS2)
  - Ultra-low capacitance: 1pF typical
  - JLCPCB: C5199240

## Planned Content

Additional component documentation coming soon:

- USB-PD Controller (CH224D)
- DC-DC Converters (LM2596S-ADJ)
- Linear Regulators (LM7812/7805/7912)
- PTC Resettable Fuses
- Inductors and Capacitors
- Footprint requirements and PCB design considerations
- Alternative parts and substitution guidelines
- Stock availability and procurement strategies
- Cost analysis and BOM optimization

---

*Documentation in progress. Last updated: 2025-12-28*
