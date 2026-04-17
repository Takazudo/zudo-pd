---
title: mSMD110-33V - +5V Rail PTC Resettable Fuse
sidebar_position: 11
---

# mSMD110-33V - +5V Rail PTC Resettable Fuse

Auto-reset overcurrent protection for +5V power rail with 1.1A hold current.

- 🔗 [View on JLCPCB: C70119](https://jlcpcb.com/partdetail/C70119)
- 📄 Datasheet: Contact manufacturer

## Overview

The mSMD110-33V is a PTC resettable fuse providing automatic overcurrent protection for the +5V power rail. It protects the L7805 linear regulator and downstream modules from overcurrent conditions while automatically resetting after cooling.

## Part Information

| Parameter                    | Value                                          |
| ---------------------------- | ---------------------------------------------- |
| **JLCPCB Part Number**       | [C70119](https://jlcpcb.com/partdetail/C70119) |
| **Manufacturer Part Number** | mSMD110-33V                                    |
| **Package**                  | 1812 (4.5mm x 3.2mm)                           |
| **Stock**                    | 44,459 units (excellent availability)          |
| **Estimated Price**          | ~$0.10-0.15                                    |
| **Type**                     | Resettable Polymeric PTC                       |

## Electrical Specifications

### Current Ratings

| Parameter          | Value | Unit | Conditions                      |
| ------------------ | ----- | ---- | ------------------------------- |
| **Hold Current**   | 1.1   | A    | Maximum safe continuous current |
| **Trip Current**   | ~2.2  | A    | Typical (2x hold current)       |
| **Voltage Rating** | 33    | V    | Maximum voltage                 |

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
Layer 2: LM2596S #2 (+7.5V) → Current limiting ~3-5A
Layer 3: LM7805 Linear Regulator → Current limiting ~1A, thermal shutdown
Layer 4: This PTC (1.1A hold / 2.2A trip) → Auto-reset protection
    ↓
+5V Output to Modules
```

### Circuit Placement

```
LM7805 Output ──┬─── PTC2 (1.1A) ───┬─── TVS2 ─── +5V OUT
                │   mSMD110-33V     │    SD05
                │                   │      ↕
                │                   └─────GND
                │
                └─── LED3 ─── R8 (1kΩ) ─── GND
                     Blue status indicator
```

## Protection Behavior

### Current vs Protection State

| Current  | L7805 State             | PTC State  | Result                      |
| -------- | ----------------------- | ---------- | --------------------------- |
| 0-1.0A   | ✅ Normal               | ✅ Normal  | Normal operation            |
| 1.0-1.5A | ⚠️ Current limiting     | ⚠️ Warming | Both protections activating |
| &gt;1.5A | 🛑 Hard limit (~1A max) | 🛑 Trips   | Dual protection active      |

### Design Rationale

**Why 1.1A hold for 1.5A target?**

```
Hold current:  1.1A
Design target: 1.5A (L7805ABD2T-TR max)
Note:          PTC trips before reaching regulator max

Behavior:
⚠️ PTC will trip if load exceeds 1.1A sustained
✅ Prevents false trips during power-on surge
✅ Allows brief current spikes
✅ Provides additional protection layer
✅ L7805ABD2T-TR handles 1.5A but PTC limits to 1.1A
```

**Note:** The 1.1A PTC hold current is lower than the 1.5A regulator capacity. If 1.5A sustained current is needed, consider upgrading to a 1.5A PTC. For typical modular synth applications, 1.1A is usually sufficient.

## Comparison to +12V Rail

| Feature       | +5V PTC (This) | +12V PTC |
| ------------- | -------------- | -------- |
| Hold current  | 1.1A           | 1.5A     |
| Package       | 1812           | SMD1210  |
| Regulator max | 1.5A           | 1.5A     |
| PTC limits to | 1.1A           | 1.5A     |
| Stock         | 44,459         | 7,525    |

**Note:** The +5V PTC limits current to 1.1A, which is lower than the regulator's 1.5A capacity. For typical modular synth applications using the +5V rail (digital modules, some LEDs), 1.1A is usually sufficient.

## Bill of Materials

| Designator | Part        | Package | JLCPCB Part # | Qty | Unit Price | Extended |
| ---------- | ----------- | ------- | ------------- | --- | ---------- | -------- |
| PTC2       | mSMD110-33V | 1812    | C70119        | 1   | $0.10      | $0.10    |

## Related Components

- **Protected circuit**: L7805ABD2T-TR (U7) - +5V Linear Regulator
- **Upstream**: LM2596S-ADJ #2 (U3) - +7.5V DC-DC Converter
- **Overvoltage protection**: SD05 (TVS2)
- **Parallel rails**: PTC +12V (C7529589), PTC -12V (C2830246)

## References

- **Protection design**: `/doc/docs/learning/protection-fuse-strategy.md`
- **Circuit diagram**: [Diagram6 - +5V Linear Regulator](/docs/overview/circuit-diagrams#diagram6-75v--5v-linear-regulator-l7805-u7)
- **JLCPCB Part Page**: https://jlcpcb.com/partdetail/C70119
