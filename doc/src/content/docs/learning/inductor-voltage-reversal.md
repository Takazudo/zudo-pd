---
title: Inductor Voltage Reversal and Negative Voltage Generation
---

# Inductor Voltage Reversal and Negative Voltage Generation

This document explains how inductors work in switching converters and how voltage polarity reversal enables negative voltage generation from positive input voltage.

## Overview

Understanding inductor behavior is crucial for comprehending inverting buck-boost converters like Diagram4 (+15V → -13.5V). The key concept is **voltage polarity reversal** - when the switch opens, the inductor's voltage flips to maintain current flow, creating negative voltage.

---

## Table of Contents

1. [Inductor Fundamentals](#inductor-fundamentals)
2. [Voltage Polarity Reversal Mechanism](#voltage-polarity-reversal-mechanism)
3. [How Negative Voltage is Created](#how-negative-voltage-is-created)
4. [Component Roles in the Circuit](#component-roles-in-the-circuit)
5. [Common Misconceptions](#common-misconceptions)
6. [Analogies for Understanding](#analogies-for-understanding)

---

## Inductor Fundamentals

### What is an Inductor?

An inductor stores energy in a magnetic field when current flows through it.

```
     ╔═══════╗
 ────╢ Inductor╟────
     ╚═══════╝

Current flows → Magnetic field forms → Energy stored
```

### The Fundamental Law

The relationship between voltage and current in an inductor:

```
V = L × di/dt

V     : Voltage across inductor [V]
L     : Inductance [H]
di/dt : Rate of change of current [A/s]
```

**Critical Points:**

- Voltage depends on **rate of change of current**, NOT the current itself
- When current increases (di/dt > 0): Voltage has one polarity
- When current decreases (di/dt &lt; 0): **Voltage reverses polarity**

### Lenz's Law

Inductors **resist changes in current**:

- Trying to increase current → Inductor opposes with counter-voltage
- Trying to decrease current → Inductor opposes with **reversed voltage**

This is Lenz's Law: the induced voltage always opposes the change that created it.

---

## Voltage Polarity Reversal Mechanism

### Why Does Polarity Reverse?

The inductor acts differently depending on whether it's being driven or is driving:

**Phase 1 - Being Driven (Switch ON, current increasing):**

```
        +15V (External source)
         │
    [Switching Node]
         │  ╔═══════╗
         └──╢   L3  ╟──┐
         +  ╚═══════╝  │  -  ← Voltage polarity
                       │
                      GND (0V)

• Current flows DOWN ↓
• Current is increasing (di/dt > 0)
• External source (VIN) pushes current through inductor
• Inductor resists with back-EMF (top +, bottom -)
```

**Phase 2 - Driving Itself (Switch OFF, current tries to decrease):**

```
    [Switching Node] ~-14V!
         │  ╔═══════╗
         └──╢   L3  ╟──┐
         -  ╚═══════╝  │  +  ← Polarity REVERSED!
                       │
                      GND (0V)

• Current STILL flows DOWN ↓ (same direction)
• But switch is open, so current wants to decrease (di/dt < 0)
• Inductor fights this by REVERSING voltage polarity
• Switching node drops BELOW GND to maintain current
```

### The Key Insight: Source vs Load

```
Switch ON:  External source → Inductor acts as load (absorbs energy)
            Voltage: + on top, - on bottom

Switch OFF: Inductor → Acts as source (releases energy)
            Voltage: - on top, + on bottom (REVERSED!)
```

**This is NOT special component design - it's fundamental physics that ALL inductors exhibit!**

---

## How Negative Voltage is Created

### Circuit Configuration (Diagram4: +15V → -13.5V)

```
Inverting Buck-Boost Circuit (LM2596S-ADJ, U4):

                             ┌──────────────────┐
                             │   LM2596S-ADJ    │
+15V IN ─────────────────────┤1 VIN             │
                             │      (U4)        │
                             │                  │
                             │       ON/OFF 5 ──┼──○ (Float = ON)
                             │                  │
                             │            FB 4──┼─── (Feedback)
                             │                  │
                             │           OUT 2──┼─── (Switching Node)
                             │                  │
                             │3 IC GND ─────────┼──── -13.5V OUT
                             └──────────────────┘     ⚠️ IC GND at -13.5V!

Switching Section:

                    ┌─────────────────────────┐
                    │ U4 pin 2 (OUT)          │
                    └──────┬──────────────────┘
                           │
                      Switching Node
                           │
              ┌────────────┴────────────┐
              │                         │
           [  L3  ]                  D3 Cathode
          Inductor                     │
            100µH                   Schottky
              │                       SS34
              │                      3A 40V
              │                         │
              │                      D3 Anode
              │                         │
     System GND (0V)              -13.5V OUT
                                   (= IC GND pin 3)

Output Filter Capacitor:

                  System GND (0V) ──── C11 (470µF) ──── -13.5V OUT
                                       (+ terminal)   (- terminal)
```

### Bootstrapped Ground Concept

**Most Important Point:**

IC GND pin (pin 3) is **NOT** connected to System GND (0V)!

```
Normal Buck Converter (Diagram2/3):
  IC GND pin → System GND (0V) ✅ Standard reference

Inverting Buck-Boost (Diagram4):
  IC GND pin → -13.5V OUT ⚠️ NOT at system ground!
```

This is called "bootstrapped ground" - the IC operates with its ground reference at -13.5V.

### Step-by-Step Operation

**Step 1: Energy Storage (Switch ON, ~3µs)**

```
+15V ──[Switch CLOSED]── OUT pin ≈ +15V
                           │
                         [L3]
                           │
                          GND

Operation:
1. OUT pin at +15V (connected to VIN through internal switch)
2. Current flows DOWN through L3 to GND
3. Current increases (di/dt > 0)
4. Magnetic energy accumulates in L3
5. D3 is reverse-biased (cathode +15V > anode -13.5V)
   → D3 blocks current ✅
```

**Step 2: Voltage Reversal (Switch OFF, ~3.7µs)**

```
+15V ──[Switch OPEN]─X─ OUT pin ≈ -13.8V!
                          │
                        [L3]
                          │
                         GND

Operation:
1. Switch opens
2. Current tries to decrease (di/dt < 0)
3. L3 reverses voltage polarity to maintain current
4. OUT pin drops to ~-13.8V (BELOW System GND!)
5. D3 becomes forward-biased (cathode -13.8V < anode -13.5V)
   → D3 conducts current ✅
6. Current flows through D3 to -13.5V output
7. C11 charges negatively
```

**Current Path During Switch OFF:**

```
System GND (0V) ──→ L3 (UP!) ──→ OUT pin ──→ D3 ──→ -13.5V OUT
                     ↑              (-13.8V)    ↓      ↓
                     │                      Cathode  Anode
             Inductor maintains             (-13.8V) (-13.5V)
             current by reversing                ↓
             voltage polarity               C11 (- terminal)
                                                 ↓
                                            C11 (+ terminal)
                                                 ↓
                                         System GND (0V)

Loop: GND → L3 → D3 → C11 → GND
This charges C11 more negative each cycle
```

**Step 3: Steady State (After Many Cycles)**

```
Startup sequence:
  Cycle 1:   C11 = 0V → -0.5V
  Cycle 10:  C11 = -8V → -9V
  Cycle 100: C11 = -13.3V → -13.5V ✅ Stable

Feedback loop maintains -13.5V regulation
```

### PWM Operation

The circuit operates like PWM at 150kHz:

```
OUT pin (Switching Node) voltage waveform:

  +15V ────┐     ┐     ┐     ┐
           │     │     │     │    ← Switch ON periods
           │     │     │     │
   0V ─────┤     │     │     │
           │     │     │     │
 -13.8V    └─────┘     └─────┘    ← Switch OFF periods

           ├─ON─┤├OFF┤├─ON─┤├OFF┤

      Time →→→→→→→→→→→→→→→→→→→→→

Period = 1/150kHz ≈ 6.7µs
Duty cycle ≈ 50% (varies with load)
```

The output capacitor C11 filters this switching waveform into stable DC:

```
Switching Node (OUT pin):
  +15V ─┐   ┐   ┐   ┐   ← Fast switching (150kHz)
        │   │   │   │
 -13.8V └───┘   └───┘

                │
                ↓ (through D3 and L3)

C11 filters to:
  -13.5V ─────────────── ← Steady DC (small ripple ~50mV)
```

---

## Component Roles in the Circuit

### 1. L3 (Inductor): Voltage Generator ⚡

**Role:** Creates voltage reversal to generate negative voltage

```
Switch ON:  VIN (+15V) forces current through L3
            L3 stores energy in magnetic field

Switch OFF: L3 reverses voltage to maintain current
            ← This creates the negative voltage!
            Switching node drops to -13.8V
```

**Without L3:** No voltage reversal → No negative voltage → Circuit doesn't work

### 2. D3 (Schottky Diode): One-Way Gate 🚪

**Role:** Controls current direction (does NOT generate voltage!)

```
Switch ON:  D3 blocks current (reverse-biased)
            Cathode (+15V) > Anode (-13.5V) → OFF

Switch OFF: D3 allows current (forward-biased)
            Cathode (-13.8V) < Anode (-13.5V) → ON
```

**Without D3:** No current path during switch-OFF → Voltage spikes → IC damage

**Why Schottky Diode?**

| Feature              | Regular Diode    | Schottky Diode                  |
| -------------------- | ---------------- | ------------------------------- |
| Forward voltage drop | ~0.7V            | ~0.3V ⚡ Less loss              |
| Switching speed      | Slow (~µs)       | Fast (~ns) ⚡ Better for 150kHz |
| Reverse recovery     | Slow             | Fast ⚡ Less noise              |
| **Basic function**   | ✅ One-way valve | ✅ One-way valve (same!)        |

Schottky is more efficient, but **doesn't have special negative voltage generation capability** - it's still just a one-way valve!

### 3. C11 (Electrolytic Capacitor): Voltage Storage 🔋

**Role:** Stores charge and filters switching into stable DC

```
Switching waveform (OUT pin):
  +15V ─┐   ┐   ┐   ┐   ← High-frequency switching (150kHz)
        │   │   │   │
 -13.8V └───┘   └───┘

        ↓ (via D3 and L3)

C11 filters to:
  -13.5V ─────────────── ← Stable DC (ripple ~50mV)
```

**Without C11:** Output voltage oscillates ±15V → No stable -13.5V DC

### Component Cooperation

```
        Voltage Creator      Current Director    Voltage Storage
             ↓                    ↓                    ↓
        ╔═══════╗            ┌───┴───┐           ┌────────┐
   ─────╢  L3   ╟───┬────────┤  D3   ├───────────┤   C11  ├──── GND
        ╚═══════╝   │        └───────┘           └────────┘
                    │        (one-way             (stores
        (creates    │         valve)              negative
         voltage    │                             voltage)
         reversal)  │
                    │
                   OUT pin
              (switches ±15V)
```

---

## Common Misconceptions

### Misconception 1: "The diode creates negative voltage"

❌ **Wrong:** Diode generates negative voltage
✅ **Correct:** Inductor (L3) creates voltage reversal; diode just routes current at the right time

### Misconception 2: "FB pin current makes GND go below 0V"

❌ **Wrong:** FB pin accepts too much current, pulling GND negative
✅ **Correct:** Switching action and inductor voltage reversal charge C11 negatively

### Misconception 3: "Schottky diode has special voltage inversion feature"

❌ **Wrong:** Schottky has special negative voltage generation capability
✅ **Correct:** Schottky is more efficient (lower drop, faster switching) but still just a one-way valve

### Misconception 4: "Inductor just smooths the output like a capacitor"

❌ **Wrong:** Inductor only smooths output voltage
✅ **Correct:** **Inductor CREATES the negative voltage** through voltage reversal; capacitor SMOOTHS it

### True Roles Summary

| Component  | Misconception              | Actual Role                                                |
| ---------- | -------------------------- | ---------------------------------------------------------- |
| **L3**     | Stores current             | ✅ **Creates voltage reversal** (negative voltage source!) |
| **D3**     | Generates negative voltage | ❌ Just a one-way valve (efficient timing control)         |
| **C11**    | Just filtering             | ✅ Filtering + **stores negative charge** (battery-like)   |
| **IC GND** | At 0V reference            | ❌ At -13.5V (bootstrapped ground)                         |

---

## Analogies for Understanding

### Why the "Water Height" Analogy Fails

Traditional voltage analogy:

```
Voltage = Height:
  High voltage = Mountain top
  Low voltage = Valley
  Current flows downhill ✅

But for inductors:
  Voltage suddenly reverses (+15V → -14V)
  "The mountain flips upside down!" 🤔
  This doesn't make sense in water analogy ❌
```

**The problem:** Water-height assumes voltage is a fixed reference (like gravity). Inductors **generate** voltage dynamically, so the "mountain" can flip!

### Better Analogy 1: Water Balloon 🎈

Capturing the "push back" concept:

```
Filling balloon (Switch ON):
  Water flows in → Balloon expands → Stores pressure
  (Current flows → Magnetic field builds → Stores energy)

Stop filling (Switch OFF):
  Balloon pushes water back! → Water flows out
  (Magnetic field collapses → Voltage reverses → Current continues)
```

This is good! The inductor "pushes back" to maintain current.

### Better Analogy 2: Flywheel (Best!) 🎡

The **flywheel** (spinning wheel) perfectly captures voltage reversal:

```
Pushing flywheel (Switch ON):
  You push → Flywheel spins faster → Stores rotational energy
  (Voltage applied → Current increases → Stores magnetic energy)

Let go (Switch OFF):
  Flywheel keeps spinning → Now it pushes YOU! → Force reverses
  (Switch opens → Current continues → Voltage reverses!)
```

**Why this is the best analogy:**

- ✅ Explains why "force" (voltage) reverses direction
- ✅ Shows continuous motion (current) even when you stop pushing
- ✅ The "world flip" feeling makes sense - flywheel becomes the driver
- ✅ Demonstrates "current inertia" - resistance to changes

### Inductor vs Capacitor: Duality

They're complementary opposites:

| Property               | Capacitor                          | Inductor                            |
| ---------------------- | ---------------------------------- | ----------------------------------- |
| **Stores**             | Voltage (electric field)           | Current (magnetic field)            |
| **Resists changes in** | Voltage                            | Current                             |
| **Energy formula**     | E = ½CV²                           | E = ½LI²                            |
| **V-I relationship**   | I = C × dV/dt                      | V = L × di/dt                       |
| **DC steady state**    | Acts like open circuit (blocks DC) | Acts like short circuit (passes DC) |

**Key difference:**

```
Capacitor:
  ──┤├──  BLOCKS DC current after charging

Inductor:
  ──╫╫──  PASSES DC current after stabilizing
```

They're **not** the same - they're **dual** to each other!

---

## Summary

### The Three Core Principles

1. **Inductor Voltage Reversal**
- V = L × di/dt fundamental law
- When current decreases, voltage polarity reverses
- This is basic physics of ALL inductors (not special components)

2. **Switching Creates Negative Voltage**
- Switch ON: L3 stores energy (+15V → GND)
- Switch OFF: L3 reverses voltage (OUT pin → -13.8V!)
- Repeating at 150kHz continuously generates negative voltage

3. **Bootstrapped Ground**
- IC GND pin connected to -13.5V output
- IC operates with -13.5V as its ground reference
- FB pin at -13.5V + 1.23V = -12.27V (system GND reference)
- But IC sees +1.23V (normal operation)

### Complete Operation Flow

```
PWM Switching (IC)
      ↓
Inductor Creates Negative Voltage (L3)
      ↓
Diode Controls Timing (D3)
      ↓
Capacitor Smooths Output (C11)
      ↓
Stable -13.5V DC Output ✅
      ↓
Feedback Regulates Voltage (R5/R6)
```

### Applications

This inverting buck-boost technique is widely used in:

- Modular synthesizer ±12V power supplies
- Op-amp negative supply generation
- Camera flash charging circuits
- Automotive ignition coils
- LCD panel backlight drivers

---

## Related Documentation

- [Circuit Diagrams](/docs/overview/circuit-diagrams) - Complete circuit schematics
- [Buck Converter Feedback](/docs/learning/buck-converter-feedback) - How feedback regulation works
- [LM2596S-ADJ Component](/docs/components/lm2596s-adj) - IC datasheet information

---

**Document created:** 2026-01-04
**Circuit reference:** Diagram4 Inverting Buck-Boost (+15V → -13.5V)
**IC used:** LM2596S-ADJ (U4)
