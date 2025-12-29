---
sidebar_position: 3
---

# PRTR5V0U2X - 5V Bidirectional Dual-Channel TVS Diode

Ultra-low capacitance ESD protection for 5V power rail with dual independent protection channels.

- 🔗 [View on JLCPCB: C5199240](https://jlcpcb.com/partdetail/C5199240)
- 📄 [Download Datasheet (PDF)](/datasheets/PRTR5V0U2X-datasheet.pdf)

import FootprintSvg from '@site/src/components/FootprintSvg';
import DiodeSOD from '@site/static/footprints-svg/SOD-123FL_L2.8-W1.8-LS3.7-RD.svg';

<FootprintSvg src={DiodeSOD} alt="PRTR5V0U2X SOD-123FL Package" minWidth="200px" minHeight="150px" />

![PRTR5V0U2X Package Preview](/footprints/PRTR5V0U2X.png)

## Overview

The PRTR5V0U2X is a bidirectional, dual-channel TVS diode array designed for ultra-low capacitance ESD protection. Its extremely low capacitance (1pF typical) makes it ideal for protecting high-speed signal lines, though in this project it protects the +5V power rail.

## Part Information

| Parameter | Value |
|-----------|-------|
| **JLCPCB Part Number** | [C5199240](https://jlcpcb.com/partdetail/C5199240) (primary) |
| **Alternate Part Number** | [C41409257](https://jlcpcb.com/partdetail/C41409257) |
| **Manufacturer Part Number** | PRTR5V0U2X |
| **Package** | SOT-143 (4-pin) |
| **Stock** | Low availability (check alternates) |
| **Estimated Price** | $0.12 |
| **Direction** | Bidirectional (both positive and negative) |
| **Channels** | Dual independent channels |

## Electrical Specifications

### Voltage Characteristics

| Parameter | Symbol | Min | Typ | Max | Unit |
|-----------|--------|-----|-----|-----|------|
| **Working Voltage** | V_WM | - | 5 | - | V |
| **Reverse Standoff Voltage** | V_RWM | - | 5 | - | V |
| **Breakdown Voltage** | V_BR | 7 | 8 | 9 | V |
| **Clamping Voltage @ 1A** | V_C | - | - | 20 | V |
| **Reverse Leakage Current** | I_R | - | - | 1 | µA |

### Power and Current Ratings

| Parameter | Symbol | Value | Unit | Conditions |
|-----------|--------|-------|------|------------|
| **Peak Pulse Power (per channel)** | P_PP | 140 | W | 8/20µs waveform |
| **Peak Pulse Current** | I_PP | 7 | A | 8/20µs waveform |
| **ESD Protection (contact)** | V_ESD | ±8 | kV | IEC 61000-4-2 |
| **ESD Protection (air)** | V_ESD | ±15 | kV | IEC 61000-4-2 |

### Dynamic Characteristics

| Parameter | Symbol | Value | Unit | Conditions |
|-----------|--------|-------|------|------------|
| **Capacitance** | C_D | 1 | pF | Typical @ 0V |
| **Response Time** | t_R | &lt;1 | ns | - |
| **Operating Temperature** | T_OP | -40 to +125 | °C | - |
| **Storage Temperature** | T_STG | -55 to +150 | °C | - |

## Pin Configuration

### SOT-143 Package (4-pin)

```
Top View:
    ┌─────────┐
    │ 1     4 │
    │         │  Pin 1: GND
    │ PRTR5V  │  Pin 2: I/O_1 (Channel 1)
    │  0U2X   │  Pin 3: I/O_2 (Channel 2)
    │         │  Pin 4: VCC (5V rail)
    │ 2     3 │
    └─────────┘
```

### Pin Functions

| Pin | Name | Function |
|-----|------|----------|
| **1** | GND | Ground reference |
| **2** | I/O_1 | Channel 1 protection I/O |
| **3** | I/O_2 | Channel 2 protection I/O |
| **4** | VCC | 5V power rail connection |

## How Bidirectional TVS Works

### Normal Operation

During normal operation (voltage within ±5V):

```
Normal State (-5V < V < +5V):
    VCC (Pin 4) ─────→ +5V Rail

    I/O_1 (Pin 2) ────→ Protected Load/Signal
    I/O_2 (Pin 3) ────→ Protected Load/Signal

    GND (Pin 1) ──────→ Ground

    (Leakage current: &lt;1µA per channel)
```

### Positive Transient Protection

When a positive voltage spike occurs:

```
Positive Spike (V > +7V):
    VCC (Pin 4) ─────→ +5V Rail (protected)
         ↑
         │ TVS clamps voltage
         │ to maximum +20V
    I/O (Pin 2/3) ⚡ ─→ Spike diverted to VCC

    GND (Pin 1) ──────→ Ground
```

### Negative Transient Protection

When a negative voltage spike occurs:

```
Negative Spike (V < -0.7V):
    VCC (Pin 4) ─────→ +5V Rail

    I/O (Pin 2/3) ⚡ ─→ Negative spike
         │
         ↓ TVS conducts to GND
         │ Clamps to -1V typical
    GND (Pin 1) ──────→ Ground (spike diverted)
```

## Circuit Placement

### TVS2: +5V Rail Protection

```
Linear Regulator Output:
    U7 (L7805ABD2T-TR)
        │
        ├─→ C19 (470µF) ─→ GND
        │
        ├─→ C15 (100nF) ─→ GND
        │
        ├─→ [TVS2] PRTR5V0U2X
        │      Pin 4 (VCC) ─→ +5V rail
        │      Pin 2 (I/O_1) ─→ Can be tied to +5V or protect signal
        │      Pin 3 (I/O_2) ─→ Can be tied to +5V or protect signal
        │      Pin 1 (GND) ─→ Ground
        │
        ├─→ PTC2 (0.75A) ─→ LED3 (Blue) ─→ +5V OUTPUT
```

### Connection Options

**Option 1: Dual Protection (Recommended)**
```
    +5V ─┬─→ Pin 4 (VCC)
         │
         ├─→ Pin 2 (I/O_1) ─→ Protected Output 1
         │
         ├─→ Pin 3 (I/O_2) ─→ Protected Output 2
         │
    GND ─┴─→ Pin 1 (GND)
```

**Option 2: Parallel Channels (Higher Current Handling)**
```
    +5V ─┬─→ Pin 4 (VCC)
         │
         ├─→ Pin 2 (I/O_1) ─┐
         │                  ├─→ Protected +5V Output
         ├─→ Pin 3 (I/O_2) ─┘
         │  (Channels paralleled for redundancy)
    GND ─┴─→ Pin 1 (GND)
```

**Option 3: Rail + Signal Protection**
```
    +5V ─┬─→ Pin 4 (VCC) ──→ +5V Rail
         │
         ├─→ Pin 2 (I/O_1) ─→ Protected Signal Line 1
         │
         ├─→ Pin 3 (I/O_2) ─→ Protected Signal Line 2
         │
    GND ─┴─→ Pin 1 (GND)
```

## Bidirectional vs Unidirectional TVS

### Key Differences

| Characteristic | Bidirectional (PRTR5V0U2X) | Unidirectional (SMAJ15A) |
|----------------|---------------------------|--------------------------|
| **Protection Direction** | Both positive and negative | One direction only |
| **Typical Use** | Signal lines, AC circuits | DC power rails |
| **Capacitance** | Very low (1pF) | Higher (~500pF) |
| **Channels** | Dual (2 channels) | Single |
| **Symmetry** | Symmetric clamping | Asymmetric |
| **Package** | SOT-143 (4-pin) | SMA (2-pin) |

### Clamping Characteristics Comparison

```
Bidirectional (PRTR5V0U2X):
    Voltage
      +20V ┤     ╱───── (Positive clamp)
           │    ╱
        +5V├───┘
           │
         0V├────────────────
           │
        -1V├───┐
           │    ╲
      -2V  ┤     ╲───── (Negative clamp)
           └──────────────→ Current

Unidirectional (SMAJ15A):
    Voltage
    +24.4V ┤     ╱───── (Positive clamp)
           │    ╱
      +15V ├───┘
           │
         0V├────────────────
           │
      -1V  ├ ─────────── (Forward diode drop only)
           └──────────────→ Current
```

## Application Notes

### 1. Ultra-Low Capacitance Benefits

**Why 1pF Matters**:
```
Capacitance Impact on Signal Integrity:
    High Capacitance (~500pF):
    Signal ──╱╲──╱╲──╱╲──  → ─╱╲──  (Degraded edges, reduced bandwidth)
             Fast            Slow

    Low Capacitance (1pF):
    Signal ──╱╲──╱╲──╱╲──  → ──╱╲──╱╲──  (Clean signal preserved)
             Fast              Fast
```

**Best Applications**:
- USB data lines (D+ / D-)
- HDMI/DisplayPort signal lines
- High-speed serial communications
- RF circuits
- Precision analog signals

**In This Project**:
- The 1pF capacitance is "overkill" for DC power rail protection
- Chosen for availability and bidirectional protection capability
- Would be ideal if protecting USB communication lines

### 2. Dual Channel Usage Strategies

**Strategy A: Independent Protection**
```
Purpose: Protect two separate circuits
    +5V Rail ─→ Pin 4 (VCC)

    Circuit A ←─ Pin 2 (I/O_1) ─→ Protection for Circuit A
    Circuit B ←─ Pin 3 (I/O_2) ─→ Protection for Circuit B

    GND ─→ Pin 1 (GND)
```

**Strategy B: Parallel Protection**
```
Purpose: Double the current handling capability
    +5V Rail ─→ Pin 4 (VCC)

                Pin 2 (I/O_1) ─┐
                               ├─→ Protected Output
                Pin 3 (I/O_2) ─┘
                (Combined: 280W pulse power)
    GND ─→ Pin 1 (GND)
```

**Strategy C: Rail + Signal**
```
Purpose: Protect power and communication lines
    +5V Rail ─→ Pin 4 (VCC) ─→ Main 5V power

    Data Line ←─ Pin 2 (I/O_1) ─→ Protect USB D+ or similar
    Enable Signal ←─ Pin 3 (I/O_2) ─→ Protect control signal

    GND ─→ Pin 1 (GND)
```

### 3. ESD Protection Standards

The PRTR5V0U2X meets IEC 61000-4-2 Level 4:

```
IEC 61000-4-2 Test Levels:
    Level 1: ±2kV contact, ±4kV air
    Level 2: ±4kV contact, ±8kV air
    Level 3: ±6kV contact, ±12kV air
    Level 4: ±8kV contact, ±15kV air ← PRTR5V0U2X certified ✓
```

**Test Waveforms**:
```
ESD Contact Discharge (8kV):
    Current
      30A ┤     ╱╲
          │    ╱  ╲___
          │   ╱       ╲___
        0A├──╯            ╲___
          └────┴────┴────┴────→ Time
              30ns  60ns 150ns
              rise  I₁    I₂
```

### 4. Clamping Voltage Selection

**Why PRTR5V0U2X for 5V Rail**:

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| Working voltage | 5V | Matches 5V rail |
| Breakdown voltage | 7V min | Sufficient margin above 5V |
| Clamping voltage | 20V max | Below component damage threshold |
| Bidirectional | Yes | Protects against negative spikes too |

**Voltage Safety Analysis**:
```
Normal Operation:  5.0V  ✓ Below working voltage
Regulation Range:  4.8V - 5.2V  ✓ Safe margin
TVS Activates:     &gt;7V  ✓ Above regulation range
Maximum Clamp:     20V  ✓ Below IC damage threshold (typically &gt;25V)
```

### 5. Thermal Considerations

**Power Dissipation**:
- **Normal operation**: ~5µW (5V × 1µA leakage per channel)
- **ESD events**: Up to 140W per channel (brief pulses)
- **Repetitive pulse**: See derating curves in datasheet

**SOT-143 Package**:
- **Thermal resistance**: ~250°C/W junction-to-ambient
- **No heat sink required** for typical ESD protection
- Small package suitable for dense PCB layouts

**Temperature Rise During ESD Event**:
```
Single 8/20µs pulse @ 140W:
    Energy = 140W × (8µs + 20µs)/2 ≈ 2mJ
    ΔT ≈ 2mJ × 250°C/W ≈ 0.5°C

Negligible temperature rise, no cooling needed.
```

### 6. PCB Layout Guidelines

**Optimal Layout**:
```
Top View PCB Layout:
    ┌────────────────────────────┐
    │  +5V Rail                  │
    │    │                       │
    │    └─── Pin 4 (VCC)        │
    │                            │
    │  [TVS2]    Pin 2 ─── I/O_1 →
    │  PRTR5V    Pin 3 ─── I/O_2 →
    │                            │
    │    ┌─── Pin 1 (GND)        │
    │    │                       │
    │  Ground Plane              │
    └────────────────────────────┘
```

**Best Practices**:
1. **Place close to connector or I/O**: Minimize trace inductance
2. **Short ground connection**: Connect Pin 1 directly to ground plane via
3. **Wide traces**: Use &gt;0.5mm traces for ESD current paths
4. **Ground plane**: Solid ground plane under TVS for low inductance
5. **Kelvin connection**: Separate I/O protection from power rail if possible

**Trace Routing**:
```
✓ GOOD:
    Signal In ─→ [TVS I/O] ─→ Protected IC
                     │
                    GND (short via to ground plane)

✗ POOR:
    Signal In ─────────────────→ Protected IC
                                     │
                                   [TVS I/O]
                                     │
                                    GND
    (Long trace allows voltage spike before TVS)
```

### 7. Testing and Verification

**Functional Tests**:

1. **Leakage Current Test**:
   ```
   Setup: Apply 5V between VCC and GND, measure I/O current
   Expected: &lt;1µA per channel
   ```

2. **Breakdown Voltage Test** (requires curve tracer):
   ```
   Setup: Slowly increase voltage on I/O pin
   Expected: Breakdown at 7-9V
   ```

3. **Visual Inspection**:
   - Verify correct orientation (Pin 1 identification)
   - Check solder joints for quality
   - Ensure no damage to package

**ESD Simulator Test** (optional, requires equipment):
```
IEC 61000-4-2 Test Setup:
    ESD Gun → I/O Pin (contact discharge)
    Verify: No damage, circuit continues operation
    Test Levels: ±2kV, ±4kV, ±6kV, ±8kV
```

## Comparison with Alternatives

### TVS Array Comparison

| Part | Channels | V_WM | Capacitance | Clamp @ 1A | Application |
|------|----------|------|-------------|------------|-------------|
| **PRTR5V0U2X** | **2** | **5V** | **1pF** | **20V** | **High-speed signals, 5V rail** |
| TPD2E001 | 2 | 5.5V | 0.5pF | 15V | Ultra-low capacitance USB |
| PESD5V0L2BT | 2 | 5V | 0.8pF | 18V | Low capacitance alternative |
| SP0503BAHT | 4 | 6V | 5pF | 17V | Multi-channel protection |

### When to Use Each Type

```
Selection Guide Based on Application:
    DC Power Rail Protection:
        Low-speed: Use unidirectional (SMAJ series)
        High-speed: Use bidirectional low-capacitance (PRTR5V0U2X)

    Signal Line Protection:
        USB 2.0: PRTR5V0U2X or TPD2E001
        USB 3.0+: TPD2E001 (lower capacitance)
        HDMI: PRTR5V0U2X acceptable
        Ethernet: SP0503BAHT (4 channels)
        CAN/RS485: Use automotive-grade TVS
```

## Application in This Project

### Usage Summary

| Component | Rail | Function | Quantity |
|-----------|------|----------|----------|
| **TVS2** | +5V | Bidirectional spike protection | 1 |

### Why Bidirectional for 5V Rail?

**Design Rationale**:
1. **Negative Spike Protection**: Protects against negative transients (e.g., from inductive loads)
2. **ESD Events**: Provides protection against both positive and negative ESD
3. **Availability**: Selected part available at JLCPCB
4. **Future-Proof**: Could also protect communication lines if design expands

**Negative Transient Scenario**:
```
Inductive Load Disconnection:
    Before:  +5V ─→ [Inductor] ─→ GND

    Disconnect:
             [Inductor] generates negative spike
                  ↓
              -10V transient!
                  ↓
             [TVS2] clamps to -1V
                  ↓
              Protected circuit safe ✓
```

### Protection Chain

```
Complete +5V Protection:
    DC-DC → Linear Reg → [Fuse F2] → [PTC2] → [TVS2] → +5V Output
            ❶              ❷           ❸         ❹

❶ Linear Regulator: Clean 5V output
❷ Fuse: Short circuit protection (1.5A, permanent)
❸ PTC: Overload protection (0.75A, resettable)
❹ TVS: Transient/ESD protection (automatic, &lt;1ns)
```

## Stock Availability and Alternatives

### Primary Part

- **C5199240**: PRTR5V0U2X, SOT-143
- Stock: Low availability, check before ordering

### Recommended Alternatives

If C5199240 is out of stock:

| Part Number | Device | Package | Notes |
|-------------|--------|---------|-------|
| **C41409257** | PRTR5V0U2X | SOT-143 | Direct equivalent |
| C2837790 | PESD5V0L2BT | SOT-23 | 0.8pF, similar specs |
| C7420372 | TPD2E001 | SOT-23-6 | 0.5pF, lower capacitance |

### Fallback: Unidirectional Option

If no bidirectional parts available, can substitute:
- **SMAJ5.0A** (C571361) - 5V unidirectional TVS
- Trade-off: Only protects positive spikes
- Benefit: Higher stock availability

## Related Components

- [SMAJ15A](./smaj15a.md) - 15V Unidirectional TVS Diode
- Protection Circuit Overview - Coming soon
- ESD Protection Design Guide - Coming soon

## References

- [JLCPCB Part Detail: C5199240](https://jlcpcb.com/partdetail/C5199240)
- [JLCPCB Alternate: C41409257](https://jlcpcb.com/partdetail/C41409257)
- IEC 61000-4-2 ESD Immunity Standard
- [Nexperia PRTR5V0U2X Datasheet](https://www.nexperia.com/products/esd-protection-tvs-filtering-and-signal-conditioning/esd-protection/automotive-esd-protection/PRTR5V0U2X.html)

---

*Last updated: 2025-12-28*
