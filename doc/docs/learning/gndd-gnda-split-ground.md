---
sidebar_position: 4
---

# GNDD/GNDA Split Ground Design

Educational reference on split ground plane techniques for mixed-signal designs. **Note: This project uses unified ground approach - this document is for learning purposes only.**

## Overview

**Split ground strategy** separates noisy "digital" ground (GNDD) from clean "analog" ground (GNDA) to minimize noise coupling in mixed-signal circuits.

**Key Concept:**

- GNDD: Ground for noisy circuits (switching regulators, digital logic, high-frequency circuits)
- GNDA: Ground for sensitive circuits (linear regulators, op-amps, ADCs, audio circuits)
- Single-point connection: GNDD and GNDA connect at ONE location only

---

## When Split Ground Makes Sense

### ✅ Good Candidates for Split Ground

**4+ Layer PCBs:**

- More routing flexibility (can route around ground splits)
- Dedicated ground layers (Layer 2 and Layer 3)
- Can implement proper star grounding without routing conflicts

**Mixed-Signal Designs:**

- Precision ADCs/DACs with digital microcontroller
- Audio circuits with digital signal processing
- RF circuits with digital control logic
- Instrumentation with digital displays

**High-Performance Requirements:**

- Need &lt;100µVp-p noise on analog ground
- Precision voltage references (&lt;1ppm drift)
- High-resolution ADCs (16-24 bit)
- Low-jitter clock circuits

### ❌ Poor Candidates for Split Ground

**2-Layer PCBs:**

- Limited routing options (hard to avoid crossing ground split)
- Signal traces crossing split create large return current loops
- Often makes noise WORSE instead of better

**Power Supplies (Like This Project):**

- Primary goal is power delivery, not signal integrity
- Component placement provides adequate isolation
- Linear regulators already act as noise filters
- Unified ground gives better return paths

**Simple Designs:**

- No precision analog circuits
- No high-resolution ADCs
- Moderate noise requirements (&gt;1mV acceptable)

---

## GNDD vs GNDA Terminology

### What "Digital" and "Analog" Really Mean

**Common misconception:**

```
❌ WRONG:
"Digital ground = for digital circuits (microcontrollers, logic)"
"Analog ground = for analog circuits (op-amps, regulators)"
```

**More accurate:**

```
✅ CORRECT:
"GNDD = Noisy ground (creates switching/high-frequency noise)"
"GNDA = Clean ground (noise-sensitive, needs quiet reference)"
```

### Noise Source Classification

**GNDD (Noisy Ground) Used For:**

| Circuit Type              | Why It's Noisy           | Examples                             |
| ------------------------- | ------------------------ | ------------------------------------ |
| **Switching regulators**  | Fast ON/OFF transitions  | LM2596S, buck/boost converters       |
| **Digital logic**         | State changes (0→1, 1→0) | Microcontrollers, FPGAs, 74HC series |
| **High-speed interfaces** | Fast signal edges        | USB, SPI, I2C, UART                  |
| **PWM circuits**          | Repetitive switching     | Motor drivers, LED dimmers           |
| **Clock circuits**        | Sharp edges, harmonics   | Crystal oscillators, PLLs            |

**GNDA (Clean Ground) Used For:**

| Circuit Type           | Why It's Sensitive              | Examples                             |
| ---------------------- | ------------------------------- | ------------------------------------ |
| **Precision ADCs**     | Noise affects LSB accuracy      | 16-24 bit ADCs                       |
| **Voltage references** | Need stable ground              | LM4040, REF3040                      |
| **Op-amp circuits**    | Amplify ground noise            | Audio preamps, instrumentation amps  |
| **Linear regulators**  | Output ripple from ground noise | LM78xx, LM317 (post-switching stage) |
| **Audio circuits**     | Audible noise/hum               | Headphone amps, DACs                 |

### Special Case: Switching Regulators

**Switching regulators are analog circuits that behave digitally:**

```
Technically:      Categorized as:       Ground Used:
═══════════      ════════════════      ════════════

Analog power     "Digital/Noisy"       GNDD
regulation       (due to switching)    (noisy behavior)

Linear power     "Analog/Clean"        GNDA
regulation       (no switching)        (clean output)
```

**Why switching regulators use GNDD:**

- Create high-frequency switching noise (like digital circuits)
- Fast current pulses in ground return path
- Magnetic field radiation from inductors
- **Grouped by noise behavior, not circuit type**

---

## Split Ground Implementation

### Schematic Organization

**Example: Mixed-signal design with microcontroller + precision ADC**

```
Noisy Section:                    Clean Section:
═════════════                    ══════════════

MCU ──→ GNDD                     GNDA ←── ADC
USB ──→ GNDD                     GNDA ←── VREF
LED PWM ──→ GNDD                 GNDA ←── Op-Amp
Buck Reg ──→ GNDD                GNDA ←── Linear Reg

         │                            │
         └──────────[R=0Ω]───────────┘
                      ↑
              Single-point connection
              (at power input)
```

### PCB Implementation Options

#### Option 1: Star Ground (Recommended)

**All grounds connect at single point:**

```
PCB Layout:

  GNDD Section              GNDA Section
  ════════════              ════════════
        │                        │
        └───────→ ⭐ ←───────────┘
             Single point
          (power input jack)

Traces radiate from star point like spokes:
    GNDD trace 1 ─┐
    GNDD trace 2 ─┤
    GNDD trace 3 ─┼─→ ⭐ ←─┬─ GNDA trace 1
                  │         ├─ GNDA trace 2
                  │         └─ GNDA trace 3
    Power GND  ───┘

Benefits: Clear current paths, no ground loops
```

#### Option 2: Split Plane with Bridge (4-Layer Only)

**Separate copper pours connected at one location:**

```
4-Layer PCB:

Layer 1 (Top): Components + signals
Layer 2 (GND):
┌────────────────────┬───────────────────┐
│   GNDD Plane       │   GNDA Plane      │
│   ════════════     │   ═══════════     │
│                    ╳                   │
│   Digital/Noisy    │   Analog/Clean    │
│   components       │   components      │
│   connect here     │   connect here    │
└────────────────────┴───────────────────┘
         ↑                    ↑
     Via from            Via from
   GNDD components     GNDA components

Layer 3 (PWR): Power planes
Layer 4 (Bottom): Additional routing

Connection: Narrow trace or 0Ω resistor at power input
```

#### Option 3: Separate Ground Pours on Same Layer (NOT Recommended)

**Problems with this approach:**

```
❌ Creates slot antenna:
┌─────────────────────────────────────┐
│  GNDD Pour        ╳     GNDA Pour   │
│                  Gap                │
│              (radiates EMI)         │
└─────────────────────────────────────┘

❌ Disrupts return currents:
Signal crosses gap → Return current detours
                  → Large loop area
                  → Worse EMI than unified plane

❌ Routing nightmare:
Can't route ANY traces across the gap
Very difficult on 2-layer PCB
```

---

## Split Ground Design Rules

### Critical Rules (Must Follow)

**1. Single-point connection only**

```
✅ CORRECT:
GNDD ────────⭐──────── GNDA
         One point

❌ WRONG:
GNDD ─┬──⭐──┬─ GNDA
      │      │
      └──⭐──┘    ← Multiple connections = ground loop
```

**2. No signal traces cross the split**

```
❌ WRONG:
GNDD plane  │  GNDA plane
            │
  Signal────┼────→ Destination
            ╳
     No return path!

✅ CORRECT:
Route signal within same ground domain
or use differential signaling across split
```

**3. Keep split length minimal**

```
❌ WRONG: Long split (slot antenna)
┌─────────────────────────────────────┐
│ GNDD          ╳╳╳╳╳╳╳      GNDA     │
│              50mm gap               │
└─────────────────────────────────────┘
        Radiates EMI like antenna

✅ CORRECT: Short split near connection point
┌─────────────────────────────────────┐
│ GNDD     ╳╳  GNDA                   │
│         5mm                         │
└─────────────────────────────────────┘
        Minimal radiation
```

**4. Connection at power input (star point)**

```
Power Input
     │
     ├──→ GNDD (noisy circuits)
     │
     ⭐  ← Single connection point
     │
     └──→ GNDA (clean circuits)

Rationale: All return currents flow to power source
```

### Measurement and Testing

**Use 0Ω resistor for split ground connection:**

```
Schematic:
GNDD ──[R1 = 0Ω]── GNDA

Benefits:
1. Measure voltage drop across R1
   → Should be near 0V
   → Non-zero = ground offset/loop

2. Remove R1 to test isolation
   → Measure noise on each domain separately
   → Verify noise coupling is reduced

3. Replace R1 with alternatives:
   → Ferrite bead (blocks HF noise)
   → Small resistor (limits ground loops)
   → Larger resistance (debugging only)
```

---

## Example: Mixed-Signal ADC System

### System Architecture

**Application: Precision temperature measurement with digital display**

```
Analog Section:          Digital Section:
═══════════════         ════════════════

Thermocouple            MCU (STM32)
    ↓                       ↓
Instrumentation Amp     USB Interface
    ↓                       ↓
Precision ADC           OLED Display
 (24-bit)                   ↓
    ↓                    PWM Backlight
Linear Regulator            ↓
 (+3.3V analog)        Buck Converter
    ↓                    (+3.3V digital)
   GNDA                      ↓
    │                      GNDD
    └──────→ ⭐ ←───────────┘
         Single point
       (power input)
```

### Ground Routing Strategy

**4-layer PCB implementation:**

```
Layer 1 (Top): Components

  [Analog Section]         [Digital Section]
  Thermocouple input       MCU + USB + Display
        ↓                         ↓
     Via to                    Via to
     GNDA                      GNDD

Layer 2 (GNDA Plane):
┌──────────────────────────────────────┐
│  GNDA Copper Pour                    │
│  ═══════════════════                 │
│                      ╳               │
│  Analog components   │               │
│  connect here        │               │
│                      ↓               │
│              Connection trace        │
└──────────────────────────────────────┘

Layer 3 (GNDD Plane):
┌──────────────────────────────────────┐
│              Connection trace        │
│                      ↑               │
│                      │               │
│                      ╳               │
│              GNDD Copper Pour        │
│              ════════════════════    │
│              Digital components      │
│              connect here            │
└──────────────────────────────────────┘

Layer 4 (Bottom): Additional routing

Connection: Narrow trace between planes at power input
           (or 0Ω resistor on top layer)
```

**Why this works:**

- Analog signals never cross GNDD plane
- Digital signals never cross GNDA plane
- Each domain has continuous return path
- Single-point connection prevents ground loops

---

## Common Split Ground Mistakes

### Mistake 1: Multiple Connection Points

```
❌ WRONG:

GNDD ─┬──Connection 1──┬─ GNDA
      │                │
      └──Connection 2──┘

Creates ground loop:
  Current flow 1 →
      ↓         ↑
  Current flow 2 ←

Different currents = voltage difference = noise
```

**Fix:** Use only ONE connection point at power input.

### Mistake 2: Signals Crossing Split

```
❌ WRONG:

GNDD side    │    GNDA side
             │
ADC_DATA ────┼───→ MCU
             ╳
        No return!

Return current must detour around split:
        Long loop = antenna = EMI
```

**Fix:**

- Isolate signal with optocoupler/isolator
- Use differential signaling (return path built-in)
- Route signal within same ground domain

### Mistake 3: Long Ground Splits

```
❌ WRONG:

┌────────────────────────────────────────┐
│ GNDD    ╳╳╳╳╳╳╳╳╳╳╳╳╳╳╳╳╳╳    GNDA    │
│        100mm slot gap                 │
└────────────────────────────────────────┘

100mm slot = excellent antenna for EMI radiation!
```

**Fix:** Minimize split length to &lt;10mm, keep near connection point.

### Mistake 4: Split on 2-Layer Board

```
❌ WRONG:

2-layer PCB with split ground:
  Top layer: Components + routing (very congested)
  Bottom: Split ground planes

Problem: MUST route many signals
         Signals inevitably cross split
         Creates ground loops everywhere
         Worse than unified ground!
```

**Fix:** Use unified ground on 2-layer boards, rely on component placement.

---

## Unified vs Split Ground Comparison

### Decision Matrix

| Criteria                 | Unified Ground          | Split Ground                    |
| ------------------------ | ----------------------- | ------------------------------- |
| **PCB Layers**           | 2-layer ✅              | 4+ layer ✅, 2-layer ❌         |
| **Routing Complexity**   | Easy ✅                 | Difficult ⚠️                    |
| **Cost**                 | Low ✅                  | Higher (more layers)            |
| **EMI**                  | Low ✅ (if layout good) | Can be high ❌ (if split wrong) |
| **Noise Isolation**      | Good (via placement) ✅ | Excellent (if done right) ✅✅  |
| **Return Current Paths** | Direct ✅               | Can be disrupted ❌             |
| **Design Time**          | Fast ✅                 | Slow (careful planning)         |
| **Risk of Errors**       | Low ✅                  | High ⚠️                         |

### Performance Comparison

**2-Layer Power Supply (This Project):**

| Approach                            | Output Ripple | EMI       | Complexity | Result             |
| ----------------------------------- | ------------- | --------- | ---------- | ------------------ |
| **Unified ground + good placement** | &lt;1mV       | Low       | Simple     | ✅ **Recommended** |
| **Split ground**                    | &lt;0.5mV?    | High risk | Complex    | ❌ Not worth it    |

**4-Layer Mixed-Signal ADC:**

| Approach           | ADC Noise | EMI | Complexity | Result                |
| ------------------ | --------- | --- | ---------- | --------------------- |
| **Unified ground** | ~10µV     | Low | Simple     | ⚠️ May not meet specs |
| **Split ground**   | &lt;1µV   | Low | Moderate   | ✅ **Recommended**    |

---

## When to Use Each Approach

### Use Unified Ground When:

✅ **2-layer PCB** - Limited routing options make split impractical
✅ **Power supplies** - Component placement provides adequate isolation
✅ **Moderate noise requirements** - &gt;1mV acceptable
✅ **Simple designs** - No precision analog, no high-res ADC
✅ **Cost-sensitive** - Minimize layer count
✅ **Fast development** - Less design time needed

### Use Split Ground When:

✅ **4+ layer PCB** - Sufficient routing flexibility
✅ **Precision analog** - High-resolution ADCs (≥16 bit), voltage references
✅ **Strict noise requirements** - &lt;100µV needed
✅ **Mixed-signal design** - Digital controller + analog sensors
✅ **Audio applications** - Professional audio (&lt;-100dB THD+N)
✅ **RF circuits** - Low phase noise oscillators, receivers

---

## Summary

### Key Takeaways

**Split ground is NOT a magic solution:**

- ❌ Does NOT automatically reduce noise
- ❌ Can make noise WORSE if done incorrectly
- ❌ Not suitable for 2-layer boards in most cases
- ✅ Requires careful design and understanding

**When split ground works:**

- ✅ 4+ layer PCBs with routing flexibility
- ✅ True mixed-signal designs (ADC + digital)
- ✅ Very strict noise requirements
- ✅ Designer understands return current physics

**Better alternatives for 2-layer boards:**

- ✅ Unified ground plane (solid copper pour)
- ✅ Strategic component placement (physical separation)
- ✅ Good layout practices (tight loops, wide traces)
- ✅ Linear regulators for noise filtering

### For This USB-PD Power Supply Project

**Decision: Unified Ground ✅**

**Rationale:**

1. 2-layer PCB (split impractical)
2. Power supply application (not mixed-signal)
3. Moderate noise requirements (&lt;1mV acceptable for modular synth)
4. Linear regulators provide natural noise filtering
5. Component placement alone achieves adequate isolation

**Implementation:**

- Bottom layer: Solid GND copper pour (no splits)
- Component placement: Physical separation between switching and output
- Result: Clean output, low EMI, simple design ✅

**This document is for learning - we use unified ground in this project!**
