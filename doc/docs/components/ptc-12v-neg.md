---
sidebar_position: 12
---

# JK-nSMD100/16V - -12V Rail PTC Resettable Fuse

Auto-reset overcurrent protection for -12V power rail with 1.0A hold current.

- 🔗 [View on JLCPCB: C2830246](https://jlcpcb.com/partdetail/C2830246)
- 📄 Datasheet: Contact manufacturer

## Overview

The JK-nSMD100/16V is a PTC resettable fuse providing automatic overcurrent protection for the -12V power rail. It protects the CJ7912 negative linear regulator and downstream modules from overcurrent conditions while automatically resetting after cooling.

## Part Information

| Parameter                    | Value                                              |
| ---------------------------- | -------------------------------------------------- |
| **JLCPCB Part Number**       | [C2830246](https://jlcpcb.com/partdetail/C2830246) |
| **Manufacturer Part Number** | JK-nSMD100/16V                                     |
| **Package**                  | 1206 (3.2mm x 1.6mm)                               |
| **Stock**                    | 99,339 units (excellent availability)              |
| **Estimated Price**          | ~$0.10-0.15                                        |
| **Type**                     | Resettable Polymeric PTC                           |

## Electrical Specifications

### Current Ratings

| Parameter          | Value | Unit | Conditions                      |
| ------------------ | ----- | ---- | ------------------------------- |
| **Hold Current**   | 1.0   | A    | Maximum safe continuous current |
| **Trip Current**   | ~2.0  | A    | Typical (2x hold current)       |
| **Voltage Rating** | 16    | V    | Maximum voltage                 |

### Key Characteristics

| Parameter               | Value      | Unit      |
| ----------------------- | ---------- | --------- |
| **Initial Resistance**  | &lt;0.05Ω  | (typical) |
| **Trip Time @ 2x Hold** | 1-5        | s         |
| **Reset Time**          | 30-60      | s         |
| **Operating Temp**      | -40 to +85 | °C        |

## Circuit Integration

### Protection Architecture

```
Layer 1: USB-PD Adapter → Overcurrent protection
Layer 2: ICL7660M (-15V inverter) + LM2596S #3 → Current limiting
Layer 3: LM7912 Linear Regulator → Current limiting ~1A, thermal shutdown
Layer 4: This PTC (1.0A hold / 2.0A trip) → Auto-reset protection
    ↓
-12V Output to Modules
```

### Circuit Placement

```
LM7912 Output ──┬─── PTC3 (1.0A) ───┬─── TVS3 ─── -12V OUT
                │  JK-nSMD100/16V   │   SMAJ15A
                │                   │   (reversed)
                │                   │      ↑
                │                   └─────GND
                │
         GND ─── LED4 ─── R9 (1kΩ) ─┘
              Red status (reversed polarity)
```

**Note:** LED polarity is reversed for negative rail: anode to GND, cathode to -12V.

## Protection Behavior

### Current vs Protection State

| Current  | LM7912 State            | PTC State  | Result                      |
| -------- | ----------------------- | ---------- | --------------------------- |
| 0-1.0A   | ✅ Normal               | ✅ Normal  | Normal operation            |
| 1.0-1.5A | ⚠️ Current limiting     | ⚠️ Warming | Both protections activating |
| &gt;1.5A | 🛑 Hard limit (~1A max) | 🛑 Trips   | Dual protection active      |

### Design Rationale

**Why 1.0A hold for 1.0A target?**

```
Hold current:  1.0A
Design target: 1.0A (CJ7912 max)
Note:          PTC and regulator rated equally

Benefits:
✅ Matches CJ7912 regulator maximum (1A)
✅ Provides margin for transients
✅ Typical modular synth -12V usage: 0.6-0.8A
✅ Prevents false trips during normal operation
```

## Negative Voltage Considerations

### PTC Polarity

**Important:** PTCs are non-polarized devices and work equally well with positive or negative voltages:

```
Positive rail:  +12V ─── [PTC] ─── Output
Negative rail:  -12V ─── [PTC] ─── Output

PTC behavior is identical in both cases!
The PTC responds to current magnitude, not polarity.
```

### Protection on Negative Rails

**Current measurement:**

- Current flows from GND to -12V rail (conventional direction)
- PTC measures absolute current magnitude
- Trip behavior is identical to positive rails

**Example:**

```
Module draws 1.5A from -12V rail:

Current path: GND → Module → -12V → PTC → LM7912
PTC sees: 1.5A (absolute value)
Result: PTC warms up and may trip (same as +12V rail)
```

## Comparison to Other Rails

| Feature       | -12V PTC (This) | +12V PTC | +5V PTC |
| ------------- | --------------- | -------- | ------- |
| Hold current  | 1.0A            | 1.5A     | 1.1A    |
| Package       | 1206            | SMD1210  | 1812    |
| Regulator max | 1.0A (CJ7912)   | 1.5A     | 1.5A    |
| PTC limits to | 1.0A            | 1.5A     | 1.1A    |
| Stock         | 99,339          | 7,525    | 44,459  |

**Note:** -12V rail uses CJ7912 which has 1A max output (vs 1.5A for positive rails). This is adequate for typical modular synth applications where -12V draws less current than +12V.

## Typical Modular Synth -12V Usage

**Why -12V draws less current:**

- Analog synth modules use +12V for:
  - Op-amp power (primary)
  - Audio signal processing
  - CV generation
  - LED indicators
- Modules use -12V only for:
  - Op-amp negative rail
  - Bipolar signals

**Typical current split:**

```
+12V: 60-70% of total current
-12V: 30-40% of total current
+5V:  10-20% of total current (digital modules)
```

**Example modular system (10 modules):**

```
+12V: 1.0-1.2A
-12V: 0.6-0.8A  ← This rail
+5V:  0.2-0.4A
```

This is why the -12V PTC has lower current rating (1.0A) compared to +12V (1.5A).

## Bill of Materials

| Designator | Part           | Package | JLCPCB Part # | Qty | Unit Price | Extended |
| ---------- | -------------- | ------- | ------------- | --- | ---------- | -------- |
| PTC3       | JK-nSMD100/16V | 1206    | C2830246      | 1   | $0.10      | $0.10    |

## Related Components

- **Protected circuit**: CJ7912 (U8) - -12V Linear Regulator
- **Upstream**: LM2596S-ADJ (U4) - -13.5V DC-DC Converter (Inverting Buck-Boost)
- **Overvoltage protection**: SMAJ15A (TVS3, reversed polarity)
- **Parallel rails**: PTC +12V (C7529589), PTC +5V (C70119)

## References

- **Protection design**: `/doc/docs/learning/protection-fuse-strategy.md`
- **Circuit diagram**: [Diagram7 - -12V Linear Regulator](/docs/overview/circuit-diagrams#diagram7--135v---12v-linear-regulator-cj7912-u8)
- **JLCPCB Part Page**: https://jlcpcb.com/partdetail/C2830246
