---
sidebar_position: 7
---

# P-Channel MOSFET Load Switch: Gate Control Explained

Understanding how the AO3401A P-channel MOSFET works as a load switch to control power flow in the USB-PD circuit.

## The Question

When upgrading from CH224D to STUSB4500, we added a MOSFET load switch (Q1). The natural question is:

> "What does Q1 do here? How does the gate voltage control power flow? And why do we need this?"

**Short answer**: Q1 acts like a voltage-controlled switch that blocks power during USB-PD negotiation and only allows power through after 15V is stable.

## Why We Need a Load Switch

### The CH224D Problem (v1.0 Design)

Our original design with CH224D had a critical flaw:

```
USB-C (5V) ──→ CH224D ──→ DC-DC Converters ──→ Output
                              ↓
                         Draws current immediately!
                              ↓
                    5V collapses during negotiation
                              ↓
                    PD negotiation fails! ❌
```

**What happened**: When USB-C first connects, it provides 5V. The DC-DC converters started drawing current immediately, which collapsed the 5V before the CH224D could negotiate 15V. Result: ~33% charger compatibility.

### The STUSB4500 Solution (v1.1 Design)

With STUSB4500 + Q1 load switch:

```
USB-C (5V) ──→ STUSB4500 ──→ Q1 (OFF) ──✕──→ DC-DC Converters
                  │
                  │ Negotiates 15V while Q1 blocks power
                  ↓
USB-C (15V) ──→ STUSB4500 ──→ Q1 (ON) ──→ DC-DC Converters ✓
```

**Result**: Power is blocked until 15V is stable. Expected ~95%+ charger compatibility.

## What is a P-Channel MOSFET?

A MOSFET is a voltage-controlled switch with three terminals:

```
        Source (S) ← Power input (high voltage side)
           │
       ════╪════   ← Gate (G) controls this "valve"
           │
        Drain (D)  → Power output
```

### P-Channel vs N-Channel

| Type          | Source Voltage   | Gate to Turn ON    | Common Use       |
| ------------- | ---------------- | ------------------ | ---------------- |
| **P-Channel** | High (e.g., 15V) | Lower than Source  | High-side switch |
| N-Channel     | Low (e.g., GND)  | Higher than Source | Low-side switch  |

For high-side switching (controlling positive voltage), P-channel is the natural choice.

## How Vgs Controls the MOSFET

**Vgs** = Voltage from **G**ate to **S**ource = V(Gate) - V(Source)

For P-channel MOSFET (AO3401A):

| Vgs       | Meaning                    | MOSFET State               |
| --------- | -------------------------- | -------------------------- |
| 0V        | Gate = Source              | **OFF** (no current flows) |
| -1.5V     | Gate slightly below Source | Starting to turn ON        |
| -4V       | Gate well below Source     | **Fully ON**               |
| -12V      | Gate much below Source     | Fully ON (near max rating) |
| &lt; -12V | Beyond limit               | ⚠️ Damage risk             |

### The Key Insight

**P-channel is "backwards" from intuition:**

- Gate HIGH (= Source) → OFF
- Gate LOW (&lt; Source) → ON

Think of it like an upside-down water valve:

```
    Source (15V) = Water tank at top
         │
    ═════╪═════  ← Gate = valve control
         │
      Drain      → Output (water flows down when valve opens)

- Gate at same level as Source: Valve CLOSED
- Gate pulled DOWN below Source: Valve OPENS
```

## The Load Switch Circuit

### Circuit Diagram

```
                    VBUS_EN_SNK (pin 16) ← Open-drain from STUSB4500
                          │
                         R12 (33kΩ)
                          │
VBUS_IN (15V) ─── R11 (100kΩ) ───┼─── Gate (pin 1)
                          │           │
                         C35          Q1 (AO3401A)
                        100nF       ┌─┴─┐
                          │   Source│   │Drain
                         GND  (pin 2)   (pin 3)
                                │         │
                             VBUS_IN   VBUS_OUT
```

### Component Roles

| Component | Value   | Function                                                        |
| --------- | ------- | --------------------------------------------------------------- |
| **R11**   | 100kΩ   | Pull-up: keeps Gate at VBUS_IN when VBUS_EN_SNK floats          |
| **R12**   | 33kΩ    | Gate voltage divider: sets Gate voltage when VBUS_EN_SNK is LOW |
| **C35**   | 100nF   | Soft-start: slows gate voltage change to reduce inrush current  |
| **Q1**    | AO3401A | P-channel MOSFET: the actual power switch                       |

## How VBUS_EN_SNK Controls Q1

The STUSB4500's VBUS_EN_SNK pin is an **open-drain output**:

- **During negotiation**: VBUS_EN_SNK **floats** (high-impedance)
- **After successful negotiation**: VBUS_EN_SNK **pulls to GND**

### State 1: During Negotiation (Q1 OFF)

```
VBUS_EN_SNK = floating (open-drain not pulling)

VBUS_IN (15V) ─── R11 (100kΩ) ───┬─── Gate
                                 │
                                R12 (33kΩ)
                                 │
                            (floating) ← No current path through R12

Gate ≈ VBUS_IN (pulled up by R11)
Gate = 15V, Source = 15V
Vgs = 15V - 15V = 0V → Q1 is OFF ✓

Power blocked! DC-DC cannot drain the 5V during negotiation.
```

### State 2: After Negotiation (Q1 ON)

```
VBUS_EN_SNK = GND (open-drain pulling LOW)

VBUS_IN (15V) ─── R11 (100kΩ) ───┬─── Gate (3.7V)
                                 │
                                R12 (33kΩ)
                                 │
                                GND ← Current flows to GND

Voltage divider: Gate = 15V × R12/(R11+R12)
                      = 15V × 33kΩ/133kΩ
                      = 15V × 0.248
                      = 3.7V

Gate = 3.7V, Source = 15V
Vgs = 3.7V - 15V = -11.3V → Q1 is fully ON ✓

Power flows! VBUS_OUT ≈ VBUS_IN (minus tiny Rds(on) drop)
```

## Understanding the Voltage Divider

When VBUS_EN_SNK pulls to GND, R11 and R12 form a voltage divider:

```
15V (Top of hill)
 │
 ▼ R11 drops 11.3V (steep slope, 100kΩ)
 │
3.7V ──── Gate node (plateau)
 │
 ▼ R12 drops 3.7V (gentle slope, 33kΩ)
 │
0V (Ground level)
```

### The Math

```
Voltage across R11 = 15V × R11/(R11+R12) = 15V × 100/133 = 11.3V
Voltage across R12 = 15V × R12/(R11+R12) = 15V × 33/133 = 3.7V

Check: 11.3V + 3.7V = 15V ✓

Gate voltage = Voltage across R12 = 3.7V
(because R12's bottom is at GND)
```

### The Ratio

- R12 : R11 = 33 : 100 ≈ **1 : 3**
- Gate gets about **25%** of VBUS_IN

## Why These Resistor Values?

| Requirement                              | How It's Met                             |
| ---------------------------------------- | ---------------------------------------- |
| **Vgs must be &lt; -1.5V to turn ON**    | 3.7V - 15V = -11.3V ✓ (plenty of margin) |
| **Vgs must stay &gt; -12V (max rating)** | -11.3V is within spec ✓                  |
| **Low power consumption**                | 133kΩ total → only 0.11mA flows to GND   |
| **Fast switching**                       | R × C35 time constant is reasonable      |

### Adapting for Higher Voltages

If you wanted to use 20V PD instead of 15V:

```
Current design at 15V:  Vgs = 3.7V - 15V = -11.3V ✓ Within spec
If VBUS were 20V:       Vgs = 5.0V - 20V = -15.0V ❌ Exceeds -12V limit!
```

**Solution**: Increase R12 to raise the gate voltage:

```
Need: |Vgs| < 12V
Gate must be > (VBUS - 12V) = 20V - 12V = 8V

20V × R12/(100kΩ + R12) > 8V
R12 > 67kΩ → Use 68kΩ or 100kΩ
```

## Once ON, It's a Low-Resistance Switch

When Q1 is fully ON:

- **Rds(on)** for AO3401A ≈ 40mΩ (very low resistance)
- Voltage drop = I × Rds(on) = 1A × 0.04Ω = **0.04V**
- VBUS_OUT ≈ 14.96V when VBUS_IN = 15V (essentially the same)

The MOSFET acts like a nearly ideal switch with minimal power loss.

## Circuit Behavior Timeline

When you plug in a USB-C PD charger:

```
Time 0ms:
├─ USB-C connected, VBUS = 5V
├─ VBUS_EN_SNK = floating (STUSB4500 not ready)
├─ Q1 Gate = 5V (pulled up by R11)
├─ Vgs = 0V → Q1 OFF
└─ Status: "Negotiating, power blocked"

Time 0-500ms:
├─ STUSB4500 negotiates 15V via CC pins
├─ VBUS transitions 5V → 15V
├─ VBUS_EN_SNK still floating
├─ Q1 Gate follows VBUS_IN up to 15V
├─ Vgs ≈ 0V → Q1 still OFF
└─ Status: "Still negotiating..."

Time ~500ms:
├─ 15V confirmed stable
├─ VBUS_EN_SNK pulls to GND ✓
├─ Q1 Gate drops to 3.7V (voltage divider)
├─ Vgs = -11.3V → Q1 turns ON
├─ Power flows to DC-DC converters
└─ Status: "Power Good - 15V flowing to output"
```

## Key Takeaways

1. **P-channel MOSFETs turn ON when Gate is LOWER than Source** (Vgs negative)
2. **Vgs = V(Gate) - V(Source)** is the controlling voltage difference
3. **R11 keeps Q1 OFF by default** (pulls Gate to VBUS_IN)
4. **R12 turns Q1 ON** when VBUS_EN_SNK pulls to GND (creates voltage divider)
5. **The voltage divider ratio** determines Gate voltage: Gate = VBUS × R12/(R11+R12)
6. **Open-drain control** allows the low-voltage IC to control high-voltage power
7. **Load switch prevents negotiation failure** by blocking power during 5V→15V transition

## Common Mistakes to Avoid

❌ **Wrong**: "The gate needs current to turn the MOSFET on"

- MOSFET gates are capacitive; they're controlled by **voltage**, not current
- The resistors set the gate **voltage level**, not provide operating current

✅ **Correct**: "The gate voltage relative to source (Vgs) controls ON/OFF"

---

❌ **Wrong**: "Negative Vgs means the gate has negative voltage"

- All voltages are positive relative to GND (Gate = 3.7V, Source = 15V)
- Vgs is negative because Gate is **lower than** Source (3.7V - 15V = -11.3V)

✅ **Correct**: "Vgs is the voltage **difference** between Gate and Source"

---

❌ **Wrong**: "Higher gate voltage = more power through"

- For P-channel, it's the **opposite**!
- Higher gate voltage (closer to Source) = MORE OFF
- Lower gate voltage (further from Source) = MORE ON

✅ **Correct**: "For P-channel, pulling Gate DOWN turns it ON"

## See Also

- [AO3401A Documentation](../components/ao3401a) - Full MOSFET specifications
- [STUSB4500 Documentation](../components/stusb4500) - USB-PD controller with VBUS_EN_SNK
- [Open-Drain Outputs](./open-drain-pg-pin) - How open-drain control signals work
- [Circuit Diagrams](../overview/circuit-diagrams) - See the load switch in context
