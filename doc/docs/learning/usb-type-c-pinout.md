---
sidebar_position: 6
---

# USB Type-C Pinout and Power Delivery

Understanding USB Type-C connector pinout and how it enables USB Power Delivery (PD) negotiation.

## Full USB Type-C Pinout (24-pin)

A full USB Type-C receptacle has 24 pins arranged symmetrically to support reversible insertion:

```
USB Type-C Receptacle (24-pin)
Receptacle Front View (looking into connector)

Top Row (A-side):
┌────────────────────────────────────────────────────┐
│ A1   A2   A3   A4   A5   A6   A7   A8   A9  A10  A11  A12 │
│ GND  TX1+ TX1- VBUS CC1  D+   D-  SBU1 VBUS RX2- RX2+ GND │
└────────────────────────────────────────────────────┘

Bottom Row (B-side):
┌────────────────────────────────────────────────────┐
│ B12  B11  B10  B9   B8   B7   B6   B5   B4   B3   B2   B1  │
│ GND  RX1- RX1+ VBUS SBU2 D-   D+  CC2  VBUS TX2- TX2+ GND │
└────────────────────────────────────────────────────┘
```

### Pin Functions

| Pin(s)               | Signal         | Purpose                 | Speed           |
| -------------------- | -------------- | ----------------------- | --------------- |
| **A1, A12, B1, B12** | **GND**        | Ground reference        | -               |
| **A4, A9, B4, B9**   | **VBUS**       | Power delivery (5V-20V) | -               |
| **A5**               | **CC1**        | Configuration Channel 1 | -               |
| **B5**               | **CC2**        | Configuration Channel 2 | -               |
| **A6, A7, B6, B7**   | **D+, D-**     | USB 2.0 data            | 480 Mbps        |
| **A2, A3**           | **TX1+, TX1-** | SuperSpeed TX Lane 1    | 5-10 Gbps       |
| **A10, A11**         | **RX2-, RX2+** | SuperSpeed RX Lane 2    | 5-10 Gbps       |
| **B2, B3**           | **TX2-, TX2+** | SuperSpeed TX Lane 2    | 5-10 Gbps       |
| **B10, B11**         | **RX1-, RX1+** | SuperSpeed RX Lane 1    | 5-10 Gbps       |
| **A8**               | **SBU1**       | Sideband Use 1          | Alternate modes |
| **B8**               | **SBU2**       | Sideband Use 2          | Alternate modes |

## Simplified USB Type-C for Power-Only (6-pin)

For applications requiring **only power delivery** (no data transfer), a simplified 6-pin connector is sufficient:

```
USB Type-C 6-Pin Connector (Power-Only)

┌──────────────────┐
│   1    2    3    │  Top Row
│  GND  VBUS  CC1  │
└──────────────────┘
┌──────────────────┐
│  CC2  VBUS  GND  │  Bottom Row
│   4    5    6    │
└──────────────────┘
```

### 6-Pin Functions

| Pin      | Signal   | Purpose                                    |
| -------- | -------- | ------------------------------------------ |
| **1, 6** | **GND**  | Ground reference                           |
| **2, 5** | **VBUS** | Power delivery (5V-20V)                    |
| **3**    | **CC1**  | Configuration Channel 1 (orientation & PD) |
| **4**    | **CC2**  | Configuration Channel 2 (orientation & PD) |

**This project uses a 6-pin connector** (JLCPCB C456012) - see [J1 USB-C Connector documentation](/docs/components/usb-c-connector).

## Configuration Channel (CC) Pins

The CC pins are critical for USB Power Delivery. They serve multiple purposes:

### 1. Cable Orientation Detection

USB Type-C is reversible. When you plug in a cable:

- Only **one** CC pin is active at a time
- The active CC pin identifies cable orientation
- The other CC pin remains inactive

**Example**:

```
Orientation 1 (normal):
- CC1 active → CH224D detects cable on CC1
- CC2 inactive

Orientation 2 (flipped):
- CC2 active → CH224D detects cable on CC2
- CC1 inactive
```

### 2. Current Advertisement (Non-PD)

For standard USB Type-C (without PD negotiation), CC pins advertise available current:

| Rp (Pull-up resistor on source) | Advertised Current      |
| ------------------------------- | ----------------------- |
| 56kΩ                            | Default USB (500-900mA) |
| 22kΩ                            | 1.5A @ 5V               |
| 10kΩ                            | 3A @ 5V                 |

### 3. Power Delivery Negotiation

With USB-PD (like CH224D), CC pins carry **digital communication**:

```
Negotiation Sequence:

1. Initial Connection (0-100ms):
   ┌─────────┐                    ┌─────────┐
   │ Source  │ ─── CC line ────→  │  Sink   │
   │ (PD     │                    │ (CH224D)│
   │ Charger)│                    │         │
   └─────────┘                    └─────────┘
   VBUS = 5V (default)

2. Capability Discovery (100-200ms):
   ┌─────────┐                    ┌─────────┐
   │ Source  │ ←── CC line ────   │  Sink   │
   │         │  "What voltages    │         │
   │         │   do you have?"    │         │
   └─────────┘                    └─────────┘

   Source responds:
   - 5V @ 3A
   - 9V @ 3A
   - 12V @ 3A
   - 15V @ 3A ✅
   - 20V @ 2.25A

3. Voltage Request (200-300ms):
   ┌─────────┐                    ┌─────────┐
   │ Source  │ ←── CC line ────   │  Sink   │
   │         │  "I want 15V/3A"   │         │
   │         │                    │         │
   └─────────┘                    └─────────┘

4. Acceptance (300-500ms):
   ┌─────────┐                    ┌─────────┐
   │ Source  │ ─── CC line ────→  │  Sink   │
   │         │  "OK, switching"   │         │
   │         │                    │         │
   └─────────┘                    └─────────┘

5. Voltage Transition (500-1000ms):
   VBUS transitions: 5V → 15V

6. Power Ready (>1000ms):
   VBUS stable at 15V
   System draws up to 45W (15V × 3A)
```

## VBUS Pins and Current Distribution

### Why Multiple VBUS Pins?

USB Type-C has **4 VBUS pins** (A4, A9, B4, B9) to:

1. **Distribute current**: Each pin carries a portion of total current
2. **Reduce resistance**: Parallel pins = lower resistance
3. **Improve reliability**: Redundancy in case of poor contact

**Current distribution example (3A total)**:

```
A4 ──┬─→ ~0.75A
     │
A9 ──┤─→ ~0.75A
     │
B4 ──┤─→ ~0.75A       Total: 3A
     │
B9 ──┴─→ ~0.75A
```

### 6-Pin Connector VBUS

In 6-pin connectors, only **2 VBUS pins** are present (pins 2, 5):

- Maximum current: **3A** (sufficient for most USB-PD applications)
- Current distribution: ~1.5A per pin

**This is adequate for our 15V/3A (45W) power supply.**

## Critical: Always Connect Redundant Pins Together

### Why Connect Both VBUS Pins Together?

USB Type-C has **redundant power pins** by design. For 6-pin connectors, this means:

- **2 VBUS pins** (pins 2, 5)
- **2 GND pins** (pins 1, 6)

**You must ALWAYS connect both pins of each type together.** Never connect just one!

### ✅ Correct Connection Strategy

```
J1 (USB-C 6P Connector)

Pin 1 (GND)  ──┬─→ System GND
               │   (via wide trace or ground plane)
Pin 6 (GND)  ──┘

Pin 2 (VBUS) ──┬─→ VBUS node → CH224D pin 2
               │   (via wide trace or copper pour)
Pin 5 (VBUS) ──┘

Pin 3 (CC1)  ────→ CH224D pin 10 (separate)
Pin 4 (CC2)  ────→ CH224D pin 11 (separate)
```

### ❌ Wrong: Connecting Only One Pin

```
❌ WRONG:
Pin 1 (GND)  ──→ System GND
Pin 6 (GND)  ──→ Not connected  ❌

Pin 2 (VBUS) ──→ VBUS node
Pin 5 (VBUS) ──→ Not connected  ❌
```

### Benefits of Connecting Both Pins

| Benefit               | Single Pin              | Both Pins Connected       |
| --------------------- | ----------------------- | ------------------------- |
| **Resistance**        | R                       | **R/2** (half) ✅         |
| **Current per pin**   | 3A                      | **1.5A** (distributed) ✅ |
| **Power dissipation** | I²R                     | **I²R/4** (quarter) ✅    |
| **Voltage drop**      | High                    | **Low** ✅                |
| **Heating**           | High                    | **Low** ✅                |
| **Reliability**       | Single point of failure | **Redundancy** ✅         |
| **EMI/Noise**         | Higher                  | **Lower** ✅              |

### Why This Matters: Practical Example

**Scenario**: 15V @ 3A power delivery

#### ❌ Using Only One GND Pin:

```
Resistance: 10mΩ (typical pin + trace resistance)
Current: 3A (full current through one pin)
Voltage drop: V = I × R = 3A × 10mΩ = 30mV
Power dissipation: P = I² × R = 9W × 10mΩ = 90mW (heats up!)
```

#### ✅ Using Both GND Pins:

```
Resistance: 5mΩ (two pins in parallel)
Current per pin: 1.5A (distributed)
Voltage drop: V = I × R = 3A × 5mΩ = 15mV (half!)
Power dissipation: P = I² × R = 9W × 5mΩ = 45mW (half the heating!)
```

**Result**: Connecting both pins gives you:

- 50% less voltage drop
- 50% less heating
- Better reliability with redundancy

### PCB Layout Best Practices

```
Top Copper Layer:

┌────────────────────────────────┐
│  USB-C Connector J1            │
│                                │
│  Pin 1 (GND) ────┐             │
│                  ├──→ Via to GND plane
│  Pin 6 (GND) ────┘             │
│                                │
│  Pin 2 (VBUS) ───┐             │
│                  ├──→ Wide trace to VBUS
│  Pin 5 (VBUS) ───┘             │
└────────────────────────────────┘

Ground Plane (Internal Layer):
████████████████████████████████
█ Solid copper pour             █
█ Multiple vias from pins 1, 6  █
████████████████████████████████
```

**Key points**:

1. Use **wide traces** (≥1mm) or **copper pours** for VBUS
2. Use **multiple vias** to connect GND pins to ground plane
3. Keep traces **short and direct**
4. Use **symmetrical routing** when possible

### USB-C Specification Requirement

The **USB Type-C specification requires** all redundant power pins to be connected:

- Ensures proper current distribution
- Guarantees reliable operation in both orientations
- Meets thermal and electrical specifications
- Required for USB-IF certification

**Bottom line**: Always connect both VBUS pins together AND both GND pins together. This is not optional!

## CH224D Connection to USB-C Connector

In this project, the CH224D connects to the 6-pin USB Type-C connector:

```
J1 (USB-C 6P)          CH224D (QFN-20)

Pin 1 (GND) ──────────→ Pin 0 (GND/EPAD)
Pin 2 (VBUS) ─────────→ Pin 2 (VBUS)
Pin 3 (CC1) ──────────→ Pin 10 (CC1)
Pin 4 (CC2) ──────────→ Pin 11 (CC2)
Pin 5 (VBUS) ─────────→ Pin 2 (VBUS) (paralleled with pin 2)
Pin 6 (GND) ──────────→ Pin 0 (GND/EPAD)
```

**Key points**:

- Both VBUS pins (2, 5) connect to CH224D VBUS (pin 2)
- Both GND pins (1, 6) connect to CH224D GND (pin 0/EPAD)
- CC1 and CC2 are separate signals for orientation detection
- CH224D automatically detects which CC pin is active

## Advantages of 6-Pin Power-Only Design

| Feature                | 24-Pin Connector     | 6-Pin Connector    | Winner   |
| ---------------------- | -------------------- | ------------------ | -------- |
| **Cost**               | Higher ($0.50-1.00)  | Lower ($0.20-0.30) | ✅ 6-pin |
| **PCB Space**          | Larger footprint     | Smaller footprint  | ✅ 6-pin |
| **Complexity**         | More routing         | Simpler routing    | ✅ 6-pin |
| **Data Transfer**      | ✅ Yes (USB 2.0/3.x) | ❌ No              | 24-pin   |
| **Power Delivery**     | ✅ Yes (up to 5A)    | ✅ Yes (up to 3A)  | Both     |
| **Stock Availability** | Good                 | Very good          | ✅ 6-pin |

**For power-only USB-PD applications, 6-pin connectors are the optimal choice.**

## Common Misconceptions

### ❌ "You need all 24 pins for USB-PD"

**False.** USB-PD only requires VBUS, GND, and CC pins. The 6-pin connector is sufficient for up to 60W (20V/3A).

### ❌ "CC pins carry power"

**False.** CC pins carry only **low-current signals** for communication and detection. Power flows through VBUS pins only.

### ❌ "Both CC pins are always active"

**False.** Only **one CC pin is active** at a time, depending on cable orientation. The CH224D automatically detects which one.

### ❌ "More VBUS pins = more power"

**Partially true.** More VBUS pins allow **higher current** (24-pin supports 5A, 6-pin supports 3A), but voltage is the same. For 45W (15V/3A), the 6-pin connector is sufficient.

## Related Documentation

- [J1 USB-C Connector Component Page](/docs/components/usb-c-connector) - Full specifications and footprint
- [CH224D USB-PD Controller](/docs/components/ch224d) - PD negotiation IC
- [Diagram1: USB-PD Section](/docs/overview/circuit-diagrams#diagram1-usb-pd-power-supply-section) - Complete circuit diagram
- [Open-Drain PG Pin](/docs/learning/open-drain-pg-pin) - Understanding the Power Good indicator

## References

- [USB Type-C Cable and Connector Specification v2.1](https://www.usb.org/document-library/usb-type-cr-cable-and-connector-specification-release-21)
- [USB Power Delivery Specification v3.1](https://www.usb.org/document-library/usb-power-delivery)
- [AN4879: USB Type-C Power Delivery Using the STM32 MCU](https://www.st.com/resource/en/application_note/an4879-usb-typec-power-delivery-using-stm32-mcus-and-stm32mpu-devices-stmicroelectronics.pdf)
