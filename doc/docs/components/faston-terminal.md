---
sidebar_position: 15
---

# FASTON 250 PCB Power Terminal

Heavy-duty FASTON 250 series PCB tab terminal for busboard power connection, supporting thick gauge wire for low-noise power delivery to Eurorack modules.

- [View on JLCPCB: C305825](https://jlcpcb.com/partdetail/C305825)
- [TE Connectivity Product Page](https://www.te.com/usa-en/product-1217754-1.html)

import FootprintSvg from '@site/src/components/FootprintSvg';
import FASTON from '@site/docs/\_fragments/footprints/CONN-TH_1217754-1.svg';

<FootprintSvg src={FASTON} alt="FASTON 250 Terminal Footprint" minWidth="150px" minHeight="150px" />

## Overview

The FASTON 250 terminal (1217754-1) is an industrial-grade quick-connect PCB tab terminal from TE Connectivity. It provides a robust power output interface for connecting the USB-PD power supply to a Eurorack busboard using standard FASTON 250 (6.35mm / 0.250") receptacle connectors.

This design uses **4 terminals** for the three power rails plus ground return:

| Terminal | Signal | Purpose              |
| -------- | ------ | -------------------- |
| **J6**   | -12V   | Negative 12V output  |
| **J7**   | +12V   | Positive 12V output  |
| **J8**   | +5V    | Positive 5V output   |
| **J9**   | GND    | Common ground return |

## Key Specifications

| Parameter                    | Value              | Notes                               |
| ---------------------------- | ------------------ | ----------------------------------- |
| **JLCPCB Part Number**       | C305825            | This design                         |
| **Manufacturer**             | TE Connectivity    |                                     |
| **Manufacturer Part Number** | 1217754-1          | FASTON 250 Series                   |
| **Tab Width**                | 6.35mm (0.250")    | Standard FASTON 250 size            |
| **Current Rating**           | 7A continuous      | Per terminal                        |
| **Voltage Rating**           | 250V               | Far exceeds 15V requirement         |
| **Contact Material**         | Tin-plated brass   | Low resistance, corrosion-resistant |
| **Mounting Type**            | Through-hole (THT) | Wave soldering                      |
| **PCB Thickness**            | 1.57-2.36mm        | Standard PCB compatible             |
| **Assembly Fee**             | $0.03/piece        | JLCPCB special component fee        |

## Why FASTON Terminals?

### Advantages for Eurorack Power Distribution

1. **Low-Noise Power Delivery**
   - Supports thick gauge wire (18-22 AWG typical)
   - Lower resistance than thin ribbon cables
   - Reduces voltage drop under load

2. **High Current Capacity**
   - 7A per terminal far exceeds requirements
   - +12V: 1.5A max (21% of capacity)
   - Combined GND: ~4A max (57% of capacity)

3. **Industrial Reliability**
   - TE Connectivity quality
   - 10,000+ mating cycles typical
   - Secure connection won't vibrate loose

4. **Easy Busboard Connection**
   - Standard FASTON receptacles widely available
   - Quick connect/disconnect without tools
   - Same connectors used on commercial busboards

## Application in This Project

### Power Output Configuration

```
USB-PD Power Supply                    Busboard
┌─────────────────┐                   ┌─────────────────┐
│                 │   FASTON cable    │                 │
│  J6 [-12V] ─────┼───────────────────┼─→ -12V rail     │
│  J7 [+12V] ─────┼───────────────────┼─→ +12V rail     │
│  J8 [+5V]  ─────┼───────────────────┼─→ +5V rail      │
│  J9 [GND]  ─────┼───────────────────┼─→ GND plane     │
│                 │                   │                 │
└─────────────────┘                   └─────────────────┘
```

### Current Flow Analysis

| Terminal | Signal | Max Design Current | Terminal Rating | Margin |
| -------- | ------ | ------------------ | --------------- | ------ |
| J6       | -12V   | 0.8A               | 7A              | 775%   |
| J7       | +12V   | 1.2A               | 7A              | 483%   |
| J8       | +5V    | 0.5A               | 7A              | 1300%  |
| J9       | GND    | 2.5A (combined)    | 7A              | 180%   |

**Note:** GND terminal carries combined return current from all three rails. Even at maximum load, this is well within the 7A rating.

### Single GND Terminal Rationale

In Eurorack systems, all GND pins from module power connectors are tied together on the busboard. Using a single GND return terminal is appropriate because:

1. The busboard already combines all GND connections
2. Maximum combined return current (~2.5A) is well within 7A rating
3. Reduces terminal count and simplifies wiring
4. Matches common Eurorack busboard designs

## Mating Connectors

To connect to the FASTON tabs, use standard FASTON 250 receptacles:

| Type                    | Wire Size | Insulation          | Typical Source           |
| ----------------------- | --------- | ------------------- | ------------------------ |
| **Crimp receptacle**    | 18-22 AWG | Fully insulated     | Electronics distributors |
| **Quick-disconnect**    | 18-22 AWG | Partially insulated | Hardware stores          |
| **Wire-to-board cable** | Pre-made  | Various             | Custom cable assemblies  |

**Recommended:** Use fully-insulated crimp receptacles with 18 AWG wire for lowest resistance and best current capacity.

## PCB Layout Considerations

1. **Pad reinforcement**: Through-hole mounting provides mechanical strength
2. **Trace width**: Use wide traces (&gt;1mm) for power connections to FASTON pads
3. **Placement**: Position terminals at board edge for easy cable access
4. **Spacing**: Maintain adequate clearance between terminals for insulated receptacles

## Related Components

- [J1 - USB Type-C Connector](./usb-c-connector) - Power input
- [J2 - 2x8 Pin Header](../overview/bom#eurorack-power-connector-16-pin) - Direct module connection
- [Bill of Materials](../overview/bom) - Complete parts list
