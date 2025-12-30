---
sidebar_position: 0
---

# J1 - USB Type-C Receptacle Connector

24-pin USB Type-C receptacle connector for USB Power Delivery (PD) input and power negotiation.

- 🔗 [View on JLCPCB: C3151751](https://jlcpcb.com/partdetail/C3151751)
- 📘 [USB Type-C Specification](https://www.usb.org/usb-charger-pd)

## Overview

The USB Type-C receptacle connector (J1) serves as the power input interface for this modular synthesizer power supply. It receives power from USB-C PD chargers and provides the necessary connections for the CH224D USB-PD controller to negotiate 15V/3A power delivery.

USB Type-C features a reversible connector design, allowing insertion in either orientation. The connector uses CC (Configuration Channel) pins to detect orientation and negotiate power delivery profiles with compatible chargers.

## Key Specifications

| Parameter | Value | Notes |
|-----------|-------|-------|
| **JLCPCB Part Number** | C3151751 | Recommended part |
| **Manufacturer Part Number** | TYPE-C 24P-GTJB 040 | |
| **Package** | SMD (Surface Mount) | 24-pin receptacle |
| **Stock Availability** | 20,147 units | Good availability |
| **Pin Count** | 24 pins | Full USB Type-C pinout |
| **Current Rating** | 5A maximum | With appropriate cable |
| **Voltage Rating** | 20V maximum | USB PD 3.0 compatible |
| **Mounting Type** | SMD (mid-mount or through-hole posts) | |
| **Durability** | 10,000+ mating cycles | Typical |

## Pin Configuration

USB Type-C receptacles have 24 pins arranged symmetrically to support reversible insertion:

```
USB Type-C Receptacle (24-pin)
Receptacle Front View (looking into the connector)

    Top Row (A1-A12):
    ┌────────────────────────────────────────┐
    │ A1  A2  A3  A4  A5  A6  A7  A8  A9 A10 A11 A12 │
    │ GND TX1+ TX1- VBUS CC1 D+  D-  SBU1 VBUS RX2- RX2+ GND │
    └────────────────────────────────────────┘

    Bottom Row (B12-B1):
    ┌────────────────────────────────────────┐
    │ B12 B11 B10 B9  B8  B7  B6  B5  B4  B3  B2  B1  │
    │ GND RX1- RX1+ VBUS SBU2 D-  D+  CC2 VBUS TX2- TX2+ GND │
    └────────────────────────────────────────┘
```

### Pin Descriptions

| Pin | Signal | Function | Used in This Design |
|-----|--------|----------|---------------------|
| A1, A12 | GND | Ground | ✅ Connected to system GND |
| B1, B12 | GND | Ground | ✅ Connected to system GND |
| A4, A9 | VBUS | Power (+5V default, up to 20V with PD) | ✅ Power input to CH224D |
| B4, B9 | VBUS | Power (+5V default, up to 20V with PD) | ✅ Power input to CH224D |
| A5 | CC1 | Configuration Channel 1 | ✅ Connected to CH224D pin 10 |
| B5 | CC2 | Configuration Channel 2 | ✅ Connected to CH224D pin 11 |
| A6, A7 | D+, D- | USB 2.0 Data (positive/negative) | ❌ Not used (power-only) |
| B6, B7 | D+, D- | USB 2.0 Data (positive/negative) | ❌ Not used (power-only) |
| A2, A3 | TX1+, TX1- | USB 3.x SuperSpeed TX (Lane 1) | ❌ Not used (power-only) |
| A10, A11 | RX2-, RX2+ | USB 3.x SuperSpeed RX (Lane 2) | ❌ Not used (power-only) |
| B2, B3 | TX2+, TX2- | USB 3.x SuperSpeed TX (Lane 2) | ❌ Not used (power-only) |
| B10, B11 | RX1+, RX1- | USB 3.x SuperSpeed RX (Lane 1) | ❌ Not used (power-only) |
| A8 | SBU1 | Sideband Use 1 | ❌ Not used |
| B8 | SBU2 | Sideband Use 2 | ❌ Not used |

## Application in This Project

In this power supply design, the USB Type-C connector is used exclusively for **power delivery** - not data transfer. Only the following pins are utilized:

### Active Connections

1. **VBUS Pins (A4, A9, B4, B9)**:
   - Receive power from USB-C PD charger
   - Initially at 5V (USB default)
   - Negotiates up to 15V/3A via CH224D
   - All four VBUS pins connected together for 5A current capacity

2. **CC Pins (A5, B5)**:
   - CC1 (A5) → CH224D pin 10
   - CC2 (B5) → CH224D pin 11
   - Used for orientation detection and PD negotiation
   - CH224D uses CC pins to communicate with PD source

3. **Ground Pins (A1, A12, B1, B12)**:
   - All four GND pins connected to system ground
   - Provides solid ground reference for power and signal integrity

### Unused Pins

- **Data pins (D+, D-)**: Not connected - power-only mode
- **SuperSpeed pins (TX/RX)**: Not connected - no USB 3.x data
- **SBU pins**: Not connected - no alternate modes

## Circuit Connections

See [Diagram1: USB-PD Power Supply Section](/docs/inbox/circuit-diagrams#diagram1-usb-pd-power-supply-section) for complete wiring.

```
J1 (USB-C Connector) Connections:

Power Input:
┌─────────────────────────────┐
│                             │
│  B9, A9   VBUS  ────────────┼──────── To CH224D pin 2 (VBUS)
│                             │         and input capacitors C1, C2
│  B4       VBUS  ────────────┤
│  A4       VBUS  ────────────┤
│                             │

Configuration Channels:
│  A5       CC1   ────────────┼──────── To CH224D pin 10 (CC1)
│  B5       CC2   ────────────┼──────── To CH224D pin 11 (CC2)
│                             │

Ground:
│  B12, A12 GND   ────────────┼──────── To system GND
│  B1,  A1  GND   ────────────┤         and CH224D pin 0 (EPAD)
│                             │
└─────────────────────────────┘
```

## USB Power Delivery Operation

### Default Power (No PD Negotiation)

When connected to a standard USB power source:
- **Voltage**: 5V
- **Current**: Up to 0.9A (4.5W) - USB 2.0 spec
- **Current**: Up to 3A (15W) - with USB Type-C current advertisement

### With USB-PD Negotiation (CH224D)

When connected to a USB-PD charger:
1. **Initial State** (0-100ms):
   - Connector establishes physical connection
   - VBUS provides 5V default power

2. **Orientation Detection** (100-200ms):
   - CH224D detects cable orientation via CC1/CC2 pull-down
   - Identifies which CC pin is active

3. **PD Negotiation** (200-500ms):
   - CH224D requests 15V/3A power profile via CC line
   - PD source responds with available power profiles
   - Negotiation completes

4. **Voltage Transition** (500-1000ms):
   - VBUS transitions from 5V → 15V
   - CH224D monitors voltage stability

5. **Power Ready** (>1000ms):
   - VBUS stable at 15V
   - System can draw up to 45W (15V × 3A)
   - PG pin goes LOW (power good indicator)

## Design Considerations

### PCB Layout

1. **Keep CC traces short**: Route CC1/CC2 traces directly to CH224D with minimal length
2. **Match CC trace lengths**: CC1 and CC2 should have similar lengths for symmetry
3. **VBUS current capacity**: Use wide traces or copper pours for all 4 VBUS pins
4. **GND plane**: Solid ground connection for all 4 GND pins
5. **ESD protection**: Consider adding ESD protection diodes on CC lines (optional but recommended)

### Mechanical Mounting

- Ensure connector is securely mounted with through-hole posts or mid-mount design
- PCB cutout should match connector footprint exactly
- Consider mechanical stress from cable insertion/removal (10,000+ cycles)

### Thermal Considerations

- VBUS pins carry up to 3A current
- Connector should have adequate copper area for heat dissipation
- At 15V/3A (45W), minimal heating expected with proper PCB design

## Alternative Parts

If C3151751 is unavailable, consider these alternatives with good stock:

| Part Number | Stock | Notes |
|-------------|-------|-------|
| C5156605 | 16,606 | TYPE-C 24P QT 143 |
| C2681555 | 16,188 | TYPE-C 24P QT |
| C456013 | 13,352 | TYPE-C 24P QCHT |

**Important**: Verify pinout compatibility when substituting parts. Most 24-pin USB Type-C receptacles follow the standard pinout, but always check the datasheet.

## Troubleshooting

| Symptom | Possible Cause | Solution |
|---------|---------------|----------|
| No power from USB-C | Poor VBUS connection | Check solder joints on A4, A9, B4, B9 pins |
| PD negotiation fails | CC pins not connected | Verify CC1 (A5) and CC2 (B5) connections to CH224D |
| Intermittent power | Loose connector | Check mechanical mounting and solder joints |
| Only 5V available | PD source not compatible | Use USB-PD 2.0/3.0 compatible charger (15V profile required) |

## References

- [USB Type-C Cable and Connector Specification](https://www.usb.org/document-library/usb-type-cr-cable-and-connector-specification-release-21)
- [USB Power Delivery Specification 3.1](https://www.usb.org/document-library/usb-power-delivery)
- [CH224D USB-PD Controller](/docs/components/ch224d) - Companion IC for PD negotiation
- [Diagram1: USB-PD Section](/docs/inbox/circuit-diagrams#diagram1-usb-pd-power-supply-section) - Circuit diagram
