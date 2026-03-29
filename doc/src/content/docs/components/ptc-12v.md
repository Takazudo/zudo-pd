---
title: SMD1210P150TF/16 - +12V Rail PTC Resettable Fuse
sidebar_position: 10
---

# SMD1210P150TF/16 - +12V Rail PTC Resettable Fuse

Auto-reset overcurrent protection for +12V power rail with 1.5A hold current and fast trip response.

- 🔗 [View on JLCPCB: C7529589](https://jlcpcb.com/partdetail/C7529589)
- 📄 Datasheet: Contact manufacturer

## Overview

The SMD1210P150TF/16 is a Positive Temperature Coefficient (PTC) resettable fuse that provides automatic overcurrent protection for the +12V power rail. Unlike traditional fuses that require replacement, this PTC automatically resets after cooling, making it ideal for modular synthesizer applications where temporary overloads may occur.

## Part Information

| Parameter                    | Value                                              |
| ---------------------------- | -------------------------------------------------- |
| **JLCPCB Part Number**       | [C7529589](https://jlcpcb.com/partdetail/C7529589) |
| **Manufacturer Part Number** | SMD1210P150TF/16                                   |
| **Package**                  | SMD1210 (3.2mm x 2.5mm)                            |
| **Stock**                    | 7,525 units                                        |
| **Estimated Price**          | ~$0.15-0.20                                        |
| **Type**                     | Resettable Polymeric PTC                           |

## Electrical Specifications

### Current Ratings

| Parameter             | Symbol | Value | Unit | Conditions                             |
| --------------------- | ------ | ----- | ---- | -------------------------------------- |
| **Hold Current**      | I_hold | 1.5   | A    | Maximum safe continuous current        |
| **Trip Current**      | I_trip | 3.0   | A    | Current that will cause device to trip |
| **Maximum Current**   | I_max  | 35    | A    | Can handle during trip transition      |
| **Voltage Rating**    | V_max  | 16    | V    | Maximum voltage                        |
| **Power Dissipation** | P_D    | 0.6   | W    | @ 25°C                                 |

### Resistance Characteristics

| State                | Resistance | Notes                                        |
| -------------------- | ---------- | -------------------------------------------- |
| **Initial (cold)**   | 0.03Ω      | Minimal voltage drop during normal operation |
| **After trip (hot)** | &gt;1000Ω  | High resistance limits current to ~10mA      |
| **Post-reset**       | &lt;0.05Ω  | May increase slightly after trip cycles      |

### Dynamic Characteristics

| Parameter          | Value      | Unit | Conditions                    |
| ------------------ | ---------- | ---- | ----------------------------- |
| **Trip Time**      | 500        | ms   | @ 3A (2x hold current)        |
| **Trip Time**      | 1-5        | s    | @ 1.5-2A (sustained overload) |
| **Trip Time**      | 0.1-0.5    | s    | @ &gt;5A (moderate short)     |
| **Reset Time**     | 30-60      | s    | Time to cool and auto-reset   |
| **Operating Temp** | -40 to +85 | °C   | Full specification range      |

## How PTC Resettable Fuses Work

### Normal Operation (0-1.5A)

During normal operation below hold current:

```
Normal State (I < 1.5A):
    +12V IN ─── [PTC: 0.03Ω] ─── +12V OUT
                    │
                Low resistance
                Minimal heating
                Voltage drop: ~45mV @ 1.5A
```

The PTC remains in low-resistance state with negligible heating and voltage drop.

### Overload Detection (1.5-3A)

When current exceeds hold current:

```
Warming State (I > 1.5A):
    +12V IN ─── [PTC: heating up] ─── +12V OUT
                    │
                Polymer heating
                Resistance increasing
                Temperature rising
```

The polymer material begins to heat up due to I²R losses, causing resistance to increase.

### Trip State (I > 3A)

When current reaches trip threshold:

```
Tripped State (I > 3A):
    +12V IN ─── [PTC: >1000Ω] ─── Output (~10mA)
                    │
                High resistance
                Current limited
                Hot, but safe
```

1. **Rapid heating**: Polymer expands, resistance increases dramatically
2. **Current limiting**: High resistance (>1kΩ) limits current to ~10mA
3. **Self-heating**: Remains hot and tripped until cause is removed
4. **Protection active**: Circuit protected from overcurrent

### Auto-Reset

After fault is removed and PTC cools:

```
Reset Sequence:
    Remove fault → PTC cools (30-60s) → Resistance drops → Normal operation
                        │
                  Temperature decreases
                  Polymer contracts
                  Resistance returns to ~0.03Ω
```

The PTC automatically resets to low-resistance state without user intervention.

## Circuit Integration

### Protection Architecture

This PTC is part of a 4-layer protection system:

```
Layer 1: USB-PD Adapter
    │    └─→ Overcurrent protection (input side)
    ▼
Layer 2: LM2596S DC-DC Converter
    │    └─→ Current limiting ~3-5A
    ▼
Layer 3: LM7812 Linear Regulator
    │    ├─→ Current limiting ~1.5-2.2A
    │    └─→ Thermal shutdown @ 150°C
    ▼
Layer 4: This PTC (1.5A hold / 3A trip)
    │    └─→ Auto-reset overcurrent protection
    ▼
+12V Output to Modules
```

### Placement in Circuit

```
LM7812 Output ──┬─── PTC1 (1.5A) ───┬─── TVS1 ─── +12V OUT
                │   SMD1210P150TF   │   SMAJ15A
                │                   │      ↓
                │                   └─────GND
                │
                └─── LED2 ─── R7 (1kΩ) ─── GND
                     Green status indicator
```

**Connection:**

- Input: +12V from LM7812 regulator output
- Output: +12V rail with TVS overvoltage protection
- LED indicator: Shows when power is present

## Protection Behavior

### Scenario 1: Normal Operation (0-1.5A)

```
Current: 0-1.5A
PTC State: ✅ Low resistance (0.03Ω)
Voltage Drop: ~45mV @ 1.5A
Status: Normal operation
```

### Scenario 2: Moderate Overload (1.5-2.2A)

```
Sequence:
1. Current rises to 1.5-2.2A
2. PTC starts heating (warming phase)
3. LM7812 current limiting also active
4. Within 1-5 seconds: PTC trips
5. Current drops to ~10mA
6. After 30-60s: Auto-resets

User Experience:
- LED dims/turns off (indicates overload)
- Auto-recovery after cooling
- No manual intervention needed
```

### Scenario 3: Short Circuit (>2.2A)

```
Sequence:
1. Output shorts to GND
2. LM7812 current limiting: IMMEDIATE (limits to ~2.2A)
3. PTC heating: Current limited by regulator
4. Within 1-5 seconds: PTC trips OR regulator thermal shutdown
5. Output current: ~0A

Protection Effectiveness:
✅ LM7812 prevents >2.2A (instant)
✅ PTC provides backup (1-5s)
✅ Thermal shutdown if sustained (5-10s)
✅ Auto-recovery when fault cleared
```

## Design Considerations

### Why 1.5A Hold Current?

**Design target:** 1.5A maximum continuous current (L7812CD2T-TR rated for 1.5A)

**Analysis:**

```
Hold current:  1.5A  (chosen)
Design target: 1.5A
Margin:        PTC and regulator rated equally

Benefits:
✅ Matches L7812CD2T-TR maximum output (1.5A)
✅ Tolerates brief surges without false trips
✅ Trips at 3A provides clear fault indication
✅ Regulator current limiting provides first-line protection
```

### Interaction with LM7812

**Key insight:** The linear regulator limits current before the PTC trips:

```
Current Limiting Cascade:

LM7812:  Current limit @ ~2.2A max (immediate)
         Thermal shutdown @ 150°C (1-5s)
            ↓
PTC:     Warming @ 1.5A (seconds)
         Trip @ 3.0A (0.5-1s)
            ↓
Result:  PTC never sees >2.2A in practice!
         Both protections complement each other
```

**Protection stages:**

| Current  | LM7812 State        | PTC State             | Result                  |
| -------- | ------------------- | --------------------- | ----------------------- |
| 0-1.5A   | ✅ Normal           | ✅ Normal             | Normal operation        |
| 1.5-2.2A | ⚠️ Current limiting | ⚠️ Warming            | Both protections active |
| &gt;2.2A | 🛑 Hard limit       | 🛑 Trips (or warming) | Dual protection         |

### Voltage Drop

**Normal operation voltage drop:**

```
V_drop = I × R
V_drop = 1.2A × 0.03Ω
V_drop = 36mV

Impact on output:
Input:  12.00V (from LM7812)
Drop:   -0.036V (PTC resistance)
Output: 11.96V ✅ (within spec)
```

Negligible impact on +12V rail voltage.

### PCB Layout Recommendations

**Trace width for 1.5A:**

- Minimum: 0.5mm (1oz copper)
- Recommended: 1.0mm (better thermal dissipation)
- Ideal: 1.5mm or copper pour

**Thermal considerations:**

- Place away from heat-generating components (LM7812)
- Good thermal contact with PCB copper
- Adequate airflow around component
- Keep-out zone: 1mm around component for proper cooling

## Failure Modes

### End-of-Life Behavior

**After many trip cycles (thousands):**

- Initial resistance may increase slightly (0.03Ω → 0.05Ω)
- Hold current may decrease slightly
- Trip time may increase
- Still provides protection, just with degraded specs

**Indicators of wear:**

- Slower reset time
- Higher voltage drop during normal operation
- Earlier trip threshold

**Design margin:** Selected 1.5A hold matches regulator maximum. Degradation over time may require replacement if voltage drop exceeds spec.

### Failure Mode: Stuck Open (Very Rare)

If PTC fails permanently open:

```
Result: +12V rail dead
Backup: None on this specific rail
Detection: LED off, no +12V output
Recovery: Replace PTC
```

**Probability:** Very low (&lt;0.1% over lifetime)

### Failure Mode: Stuck Closed (Extremely Rare)

If PTC fails permanently closed (doesn't trip):

```
Result: No PTC protection
Backup 1: LM7812 current limiting (still active)
Backup 2: LM7812 thermal shutdown (still active)
Backup 3: LM2596 DC-DC current limiting (still active)
Backup 4: USB-PD adapter protection (still active)
```

**Probability:** Extremely low (&lt;0.01% over lifetime)
**Impact:** Still protected by 3 other layers

## Comparison to Alternatives

### vs Traditional Fuse (1.5A Fast-Blow)

| Feature                 | PTC (This Part)      | Traditional Fuse     |
| ----------------------- | -------------------- | -------------------- |
| **Auto-reset**          | ✅ Yes (30-60s)      | ❌ No (must replace) |
| **Response time**       | ⚠️ 0.5-5s            | ✅ &lt;100ms         |
| **User convenience**    | ✅ Excellent         | ❌ Poor              |
| **JLCPCB availability** | ✅ Yes (7,525 stock) | ❌ No (zero stock)   |
| **Cost**                | ~$0.15-0.20          | ~$0.05-0.10          |
| **Voltage drop**        | 36mV @ 1.2A          | &lt;1mV              |
| **Best for**            | Overloads            | Catastrophic shorts  |

**Verdict:** PTC is better for this application due to auto-reset and availability.

### vs Electronic Current Limiting

| Feature           | PTC (This Part)     | Active Limiting     |
| ----------------- | ------------------- | ------------------- |
| **Complexity**    | ✅ Simple (passive) | ❌ Complex (active) |
| **Response time** | ⚠️ 0.5-5s           | ✅ &lt;1µs          |
| **Cost**          | ✅ $0.15-0.20       | ❌ $1-5+            |
| **Reliability**   | ✅ High (passive)   | ⚠️ Lower (active)   |
| **Auto-reset**    | ✅ Yes              | ✅ Yes              |

**Verdict:** PTC is adequate given LM7812 provides fast current limiting.

## Testing and Validation

### Acceptance Testing

**Test 1: Normal operation**

```
Apply: 1.2A load
Measure: Voltage drop across PTC
Expected: 30-40mV
Pass if: <50mV
```

**Test 2: Overload trip**

```
Apply: 2.5A load (or short output after regulator)
Expected: PTC trips within 5 seconds
Measure: Output current drops to <20mA
Reset: Remove load, wait 60s, verify recovery
```

**Test 3: Reset functionality**

```
1. Trip PTC with overload
2. Remove overload
3. Wait 60 seconds
4. Measure resistance: Should be <0.1Ω
5. Verify normal operation resumes
```

### Long-term Monitoring

Monitor for degradation:

- Measure voltage drop periodically
- Check reset time after trip events
- Replace if V_drop >100mV @ 1.2A

## Bill of Materials

| Designator | Part             | Package | JLCPCB Part # | Qty | Unit Price | Extended |
| ---------- | ---------------- | ------- | ------------- | --- | ---------- | -------- |
| PTC1       | SMD1210P150TF/16 | SMD1210 | C7529589      | 1   | $0.15      | $0.15    |

## Related Components

- **Protected circuit**: L7812CD2T-TR (U6) - +12V Linear Regulator
- **Upstream**: LM2596S-ADJ (U2) - +13.5V DC-DC Converter
- **Parallel rails**: PTC +5V (C70119), PTC -12V (C2830246)
- **Overvoltage protection**: SMAJ15A (TVS1)

## References

- **Protection design**: `/doc/docs/learning/protection-fuse-strategy.md`
- **Circuit diagram**: [Diagram5 - +12V Linear Regulator](/docs/overview/circuit-diagrams#diagram5-135v--12v-linear-regulator-l7812-u6)
- **JLCPCB Part Page**: https://jlcpcb.com/partdetail/C7529589
