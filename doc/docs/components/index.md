---
sidebar_position: 1
pagination_next: null
pagination_prev: null
---

# Components Documentation

Detailed documentation for all electronic components used in the USB-PD modular synthesizer power supply.

## Protection Components

Critical transient voltage suppression (TVS) diodes providing overvoltage and ESD protection:

### TVS Diodes

- **[SMAJ15A](./smaj15a.md)** - 15V Unidirectional TVS Diode
  - Package: SMA (DO-214AC)
  - Application: +12V and -12V rail protection (TVS1, TVS3)
  - Peak pulse power: 400W
  - JLCPCB: C571368

- **[SD05](./sd05.md)** - 5V Unidirectional TVS Diode
  - Package: SOD-323 (2-pin)
  - Application: +5V rail protection (TVS2)
  - Optimized for DC power rails
  - JLCPCB: C502527

## Connectors

Power input and output connectors:

### Input Connector

- **[USB Type-C Connector](./usb-c-connector.md)** - J1 USB-C Receptacle
  - Package: SMD 6-pin power-only
  - Application: USB-PD 15V power input
  - JLCPCB: C2927029

### Output Connectors

- **[FASTON 250 Terminal](./faston-terminal.md)** - J3-J6 Power Terminals
  - Package: Through-hole (6.35mm tab)
  - Application: Busboard power output (+12V, -12V, +5V, GND)
  - Current rating: 7A per terminal
  - JLCPCB: C305825

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

_Documentation in progress. Last updated: 2025-12-28_
