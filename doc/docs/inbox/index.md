---
sidebar_position: 1
pagination_next: null
pagination_prev: null
---

# INBOX

Documentation for USB-PD powered modular synthesizer power supply.

## Current Content

### Project Management

- **[📍 Project Status and Plan](current-status.md)** - Where are we now? What's next?

### Design Documentation

- **[Project Overview](overview.md)** - Design goals, architecture, features
- **[Circuit Diagrams](/docs/inbox/circuit-diagrams)** - Complete circuit configuration (Stages 1-4)
- **[Bill of Materials](../components/bom.md)** - JLCPCB-compatible BOM
- **[📋 Quick Reference](quick-reference.md)** - Common specs, formulas, FAQ

## Project Features

### 4-Stage Design

1. **USB-PD Power Supply** (CH224D)
2. **DC-DC Converters** (LM2596S × 3 + ICL7660)
3. **Linear Regulators** (LM7812/7805/7912)
4. **Protection Circuit** (PTC + Fuse + TVS)

### Performance

- **Output**: +12V/1.2A, -12V/1A, +5V/1.2A
- **Ripple**: &lt;1mVp-p
- **Efficiency**: 75-80%
- **Protection**: 2-stage (PTC auto-reset + fuse backup)

## Planned Content

- PCB design guidelines
- Manufacturing procedures
- Testing procedures
- Assembly guide
