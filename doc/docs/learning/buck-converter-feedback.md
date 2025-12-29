---
sidebar_position: 3
---

# How Buck Converters Work: Feedback Control Explained

Understanding how the LM2596S-ADJ controls output voltage through feedback - it's like an op-amp, but with switching!

## The Question

When looking at the LM2596S-ADJ circuit, a natural question arises:

> "This is a DC-DC converter, right? We input 15V, but how does it output 13.5V? Does it continuously monitor the FB (feedback) pin and control the voltage? Is this similar to an op-amp?"

**Short answer**: Yes! It's exactly like an op-amp comparator, but instead of adjusting output voltage continuously, it adjusts the **duty cycle** of an internal switch.

## What is a Buck Converter?

A **buck converter** (step-down converter) is a DC-DC switching regulator that converts a higher input voltage to a lower output voltage with high efficiency.

### Buck Converter vs Linear Regulator

**Linear Regulator** (like LM7812):
```
15V ──┬──[Transistor]──┬──→ 12V
      │   (Variable    │
      │   Resistance)  │
     Heat!            Load

Power loss = (15V - 12V) × Current
           = 3V × 1A = 3W of heat! 🔥
Efficiency ≈ 80%
```

**Buck Converter** (like LM2596S-ADJ):
```
15V ──┬──[Switch ON/OFF]──[Inductor]──┬──→ 13.5V
      │   150kHz PWM               │
      │                            │
     GND                         Load

Power loss ≈ 10-15% = 0.2W of heat ❄️
Efficiency ≈ 85-90%
```

**Key difference**: Linear regulators waste excess voltage as heat. Buck converters use high-frequency switching to efficiently "chop" the voltage down.

## The Feedback Control Loop (Like an Op-Amp!)

### Internal Block Diagram

```
                LM2596S-ADJ Internal Circuit
        ┌──────────────────────────────────────┐
        │                                      │
15V ────┤ VIN                                  │
        │   │                                  │
        │   ├──→ [Power Switch] ──→ VOUT ──────┤──→ To Inductor
        │          (MOSFET)              4     │
        │            ↑                          │
        │            │                          │
        │   ┌────────┴─────────┐               │
        │   │   PWM Control    │               │
        │   │   Logic          │               │
        │   └────────┬─────────┘               │
        │            │                          │
        │   ┌────────┴─────────┐               │
        │   │   Error          │               │
        │   │   Amplifier      │               │
        │   │   (like op-amp)  │               │
        │   └───┬──────────┬───┘               │
        │       │          │                    │
        │    [1.23V]      FB ───────────────────┤──→ To voltage divider
        │  (Internal      2                     │
        │  Reference)                           │
        └──────────────────────────────────────┘
```

### The Comparison: Op-Amp Analogy

Your intuition is **100% correct**! The LM2596S-ADJ uses an error amplifier that works just like an op-amp:

| Op-Amp Circuit | LM2596S-ADJ Buck Converter |
|----------------|----------------------------|
| **Non-inverting input (+)** | **Internal 1.23V reference** |
| **Inverting input (-)** | **FB pin (pin 2)** |
| **Error amplifier** | **Compares FB to 1.23V** |
| **Output adjustment** | **Changes PWM duty cycle** |
| **Goal** | **Make inputs equal** |
| V(+) = V(-) | **FB = 1.23V** |

```
Op-Amp Voltage Regulator:
         ┌──────┐
    ┌────┤+     │
    │    │  Op- ├──── Vout (continuous voltage)
    │ ┌──┤-  Amp│
    │ │  └──────┘
    │ │     ↑
[Vref]  [Feedback from voltage divider]

LM2596S-ADJ:
         ┌──────┐
 [1.23V]─┤+     │
         │ Error├──→ PWM ──→ Switch (150kHz)
    ┌────┤-  Amp│
    │    └──────┘
    │       ↑
[Feedback from voltage divider via FB pin]
```

## How Feedback Sets the Output Voltage

### The Magic Formula

The LM2596S-ADJ has an **internal 1.23V reference**. The chip tries to keep the FB pin at exactly 1.23V.

**Circuit**:
```
                        R1 (10kΩ)
+13.5V output ──────┬────────────┬──── FB pin (pin 2)
                    │            │
                    │         R2 (1kΩ)
                    │            │
                    │           GND
                    │
              [Voltage divider makes FB = 1.23V]
```

**Voltage divider equation**:
```
V_FB = V_OUT × (R2 / (R1 + R2))

The chip forces: V_FB = 1.23V

Therefore:
1.23V = V_OUT × (R2 / (R1 + R2))

Solving for V_OUT:
V_OUT = 1.23V × (R1 + R2) / R2
      = 1.23V × (1 + R1/R2)
```

**Example (our +13.5V circuit)**:
```
V_OUT = 1.23V × (1 + 10kΩ/1kΩ)
      = 1.23V × (1 + 10)
      = 1.23V × 11
      = 13.53V ✓
```

### Want Different Output Voltage?

Just change the resistor ratio!

| Target Voltage | R1 | R2 | Calculation |
|----------------|----|----|-------------|
| 3.3V | 1.7kΩ | 1kΩ | 1.23V × (1 + 1.7) = 3.32V |
| 5V | 3.1kΩ | 1kΩ | 1.23V × (1 + 3.1) = 5.04V |
| 7.5V | 5.1kΩ | 1kΩ | 1.23V × (1 + 5.1) = 7.50V |
| 12V | 8.7kΩ | 1kΩ | 1.23V × (1 + 8.7) = 11.94V |
| **13.5V** | **10kΩ** | **1kΩ** | **1.23V × 11 = 13.53V** |

## The Control Process: How It Maintains Voltage

Let's see what happens when the output voltage changes:

### Scenario 1: Output Voltage Drops (Load increases)

```
Step 1: Heavy load pulls voltage down
+13.5V → drops to 13.2V

Step 2: Voltage divider responds
FB pin = 13.2V × (1kΩ/11kΩ) = 1.20V
FB is now LESS than 1.23V reference!

Step 3: Error amplifier detects difference
Error = 1.23V - 1.20V = +0.03V (positive error)
"Need more output voltage!"

Step 4: PWM controller increases duty cycle
Was: 90% duty cycle
Now: 92% duty cycle
(Switch stays ON longer)

Step 5: More energy delivered to output
Inductor current increases
Output voltage rises back to 13.5V

Step 6: System stabilizes
FB pin returns to 1.23V
Error = 0
Duty cycle adjusts to maintain balance ✓
```

### Scenario 2: Output Voltage Rises (Load decreases)

```
Step 1: Light load allows voltage to rise
+13.5V → rises to 13.8V

Step 2: Voltage divider responds
FB pin = 13.8V × (1kΩ/11kΩ) = 1.25V
FB is now MORE than 1.23V reference!

Step 3: Error amplifier detects difference
Error = 1.23V - 1.25V = -0.02V (negative error)
"Need less output voltage!"

Step 4: PWM controller decreases duty cycle
Was: 90% duty cycle
Now: 88% duty cycle
(Switch stays OFF longer)

Step 5: Less energy delivered to output
Inductor current decreases
Output voltage drops back to 13.5V

Step 6: System stabilizes
FB pin returns to 1.23V
Error = 0
Duty cycle adjusts to maintain balance ✓
```

## How Switching Creates Lower Voltage: Duty Cycle

### What is Duty Cycle?

Duty cycle is the percentage of time the internal switch is ON during each cycle.

```
One switching period (1/150kHz = 6.67µs):

Switch ON for 6µs, OFF for 0.67µs
Duty Cycle (D) = ON time / Total time
              = 6µs / 6.67µs
              = 90%

Output Voltage = Input Voltage × Duty Cycle
              = 15V × 0.9
              = 13.5V ✓
```

### Visualizing the Switching

```
Time axis (microseconds) →
0    1    2    3    4    5    6    6.67

Switch state:
ON ████████████████████████████  OFF ██
    (6µs = 90% duty cycle)        (0.67µs)

Voltage at VOUT pin (before inductor smoothing):
15V ┐  ┌─────────────────────┐     ┌─
    │  │                     │     │
 0V └──┘                     └─────┘

After inductor smoothing:
15V ┐
    │ ───────────────────────────────
13.5V  (Average = 15V × 0.9 = 13.5V)
    │
 0V ┘
```

The **inductor** acts like a flywheel, smoothing the chopped voltage into steady DC!

## The Complete Buck Converter Circuit

```
                    LM2596S-ADJ (U2)
                    ┌─────────────────┐
+15V ───────────────┤5 VIN            │
                    │                 │
             ┌──────┤3 ON             │
             │      │                 │
             │      │            VOUT ├4───┬─→ L1 (100µH) ──┬─→ +13.5V
             │      │                 │    │                │
             │      │              FB ├2───┼────────────────┤
             │      │                 │    │                │
             │      │             GND ├1─┐ │                │
             │      └─────────────────┘  │ │                │
             │                          GND│                │
         ┌───┴───┐                         │                │
         │  C5   │ 100µF                   │                │
         │ Input │                         │                │
         └───┬───┘                         │                │
            GND                            │                │
                                           │                │
                               D1 (SS34)   │                │
                              Schottky ────┘                │
                              (Flyback)                     │
                                  │                         │
                                 GND                        │
                                                            │
                        Feedback Divider:                  │
                        R1 (10kΩ)                          │
                    ┌────────────┬───────────────────────┘
                    │            │
                    │         R2 (1kΩ)
                    │            │
                    │           GND
                    │
            Sets: V_FB = V_OUT × (R2/(R1+R2))
                      = 13.5V × (1k/11k)
                      = 1.23V ✓
```

### Component Roles

| Component | Function |
|-----------|----------|
| **L1 (100µH)** | Stores energy when switch is ON, releases when OFF (smooths output) |
| **D1 (Schottky)** | Provides current path when switch is OFF (flywheel effect) |
| **C5 (input cap)** | Stabilizes input voltage, handles transient currents |
| **C3 (output cap)** | Filters ripple, provides stable output voltage |
| **R1, R2** | Voltage divider - sets output voltage by creating 1.23V at FB pin |

## Why Buck Converters Are Better Than Linear Regulators

### Power Loss Comparison

**Our circuit: 15V → 13.5V at 1.3A**

**Linear Regulator (LM7812 equivalent)**:
```
Power in  = 15V × 1.3A = 19.5W
Power out = 13.5V × 1.3A = 17.6W
Power loss = 19.5W - 17.6W = 1.9W 🔥

Efficiency = 17.6W / 19.5W = 90%
(Still wastes 1.9W as heat)

Heat sink required: Large (to dissipate 1.9W)
```

**Buck Converter (LM2596S-ADJ)**:
```
Power in  = 15V × 1.3A = 19.5W
Power out = 13.5V × 1.3A = 17.6W

Internal loss ≈ 10% = 1.95W (efficiency loss)
Power loss ≈ 0.2W ❄️

Efficiency = 90% (typical for buck converters)

Heat sink required: Minimal or none
```

**Result**: Buck converter runs much cooler and wastes less energy!

### Why We Use Both in This Project

```
Power Supply Architecture:

Stage 1: USB-PD (15V) → DC-DC Buck → 13.5V
         (High efficiency, large voltage drop)

Stage 2: DC-DC (13.5V) → Linear Regulator → 12V
         (Ultra-low noise, small voltage drop)

Best of both worlds:
✓ Efficient voltage reduction (buck converter)
✓ Ultra-clean output (linear regulator)
✓ Low overall heat generation
✓ Less than 1mVp-p ripple (perfect for audio circuits)
```

## Key Takeaways

1. **Buck converters are switching regulators** that use PWM to efficiently reduce voltage
2. **Feedback control works like an op-amp** comparing FB pin to internal 1.23V reference
3. **Voltage divider sets output voltage** by creating 1.23V at FB pin
4. **Duty cycle determines output**: V_OUT = V_IN × Duty Cycle
5. **Much more efficient than linear regulators** for large voltage drops
6. **The chip constantly adjusts** duty cycle to maintain FB = 1.23V

## Common Mistakes to Avoid

❌ **Wrong**: "The LM2596S-ADJ outputs 15V and we use resistors to drop it to 13.5V"
- This would waste power like a linear regulator!

✅ **Correct**: "The LM2596S-ADJ uses PWM switching to create 13.5V directly. The resistors just tell it what voltage to target (by creating 1.23V at FB)."

❌ **Wrong**: "R1 and R2 pass current from the output"
- The feedback resistors carry almost no current (less than 1mA)!

✅ **Correct**: "R1 and R2 form a voltage divider that samples the output voltage and reports it to the FB pin."

## See Also

- [LM2596S-ADJ Documentation](/do../components/lm2596s-adj) - Full component specifications
- [Circuit Diagrams](/docs/inbox/circuit-diagrams) - See buck converters in context
- [Open-Drain Outputs](/docs/learning/open-drain-pg-pin) - Another control mechanism explained
