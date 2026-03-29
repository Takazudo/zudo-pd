---
title: PCB Layout Guidelines for Power Circuits
---

# PCB Layout Guidelines for Power Circuits

This document explains component placement rules and PCB layout best practices for power supply circuits, covering both switching converters and linear regulators.

## Overview

Proper PCB layout is critical for power supply performance, efficiency, and reliability. **Switching converters and linear regulators have different layout requirements** due to their fundamentally different operating principles.

---

## Table of Contents

1. [Why Layout Matters](#why-layout-matters)
2. [Switching Converter Layout (Critical!)](#switching-converter-layout-critical)
3. [Linear Regulator Layout (Less Critical)](#linear-regulator-layout-less-critical)
4. [Comparison: Switching vs Linear](#comparison-switching-vs-linear)
5. [Thermal Considerations](#thermal-considerations)
6. [Common Mistakes](#common-mistakes)
7. [Practical Checklist](#practical-checklist)

---

## Why Layout Matters

### The Fundamental Difference

```
Switching Converter:
  • High-frequency operation (150kHz in our design)
  • High di/dt (current changes rapidly)
  • Creates voltage spikes from parasitic inductance
  • Radiates EMI if layout is poor
  → CRITICAL layout requirements ⚡

Linear Regulator:
  • DC operation (no switching)
  • Low di/dt (current changes slowly)
  • No high-frequency switching noise
  • Main concern is stability, not EMI
  → RELAXED layout requirements ✅
```

### Parasitic Elements

All PCB traces have parasitic inductance and resistance:

```
Real PCB trace:
    ──────────  (what you draw)

    Reality:
    ───╫╫╫───▭─  (L + R parasitic)
       ↑    ↑
    Inductance  Resistance
```

**Impact on circuits:**

```
Switching Converter:
  V_spike = L_parasitic × di/dt

  Example with poor layout:
    L = 100nH (long trace)
    di/dt = 1A / 10ns (fast switching)
    V_spike = 10V! ⚡ Component damage risk

Linear Regulator:
  V_drop = R_parasitic × I_DC

  Example:
    R = 10mΩ (typical trace)
    I = 1A (DC current)
    V_drop = 10mV ✅ Negligible
```

**Conclusion:** Switching converters are **much more sensitive** to layout than linear regulators!

---

## Switching Converter Layout (Critical!)

### The "Hot Loop" Concept

The **hot loop** is the path with the highest frequency switching current. This loop MUST be minimized!

**For Buck Converter (Diagram2/3: +15V → +13.5V / +7.5V):**

```
Hot Loop Path:

    VIN capacitor ──→ U2 internal switch ──→ OUT pin
         ↑                                      ↓
         │                               Switching Node
         │                                      ↓
         │                                   [  L  ]
         │                                      ↓
         │                                    VOUT
         │                                      ↓
         └──────────── D (Diode) ←─────────────┤
                          ↑                     ↓
                          └────── GND ──────────┘

Critical components in hot loop:
  • Input capacitor (C5, C6)
  • Diode (D1, D2)
  • IC OUT pin

⚠️ Minimize the area of this loop!
```

**For Inverting Buck-Boost (Diagram4: +15V → -13.5V):**

```
Hot Loop Path:

    OUT pin (U4) ──→ D3 Cathode
         │              ↓
         │           D3 Anode
         │              ↓
         │         C11 (- terminal)
         │              ↓
         │         C11 (+ terminal)
         │              ↓
         └──────── System GND ───→ (back to U4 GND)

Critical components in hot loop:
  • D3 (Schottky diode)
  • C11 (Output capacitor)
  • OUT pin to GND path

⚠️ This is the MOST CRITICAL loop in Diagram4!
```

### Component Placement Priority - Switching Converters

**CRITICAL (must be very close, &lt;5mm):**

| Component                    | Placement Rule          | Reason                            |
| ---------------------------- | ----------------------- | --------------------------------- |
| **High-freq decoupling cap** | &lt;5mm from IC VIN pin | Filters switching noise at source |
| **Catch diode**              | &lt;5mm from IC OUT pin | Part of hot loop, high di/dt      |
| **Output capacitor**         | &lt;5mm from diode      | Completes hot loop                |

**IMPORTANT (should be close, &lt;20mm):**

| Component          | Placement Rule        | Reason                         |
| ------------------ | --------------------- | ------------------------------ |
| **Inductor**       | &lt;20mm from OUT pin | Large component, needs space   |
| **Bulk input cap** | &lt;20mm from VIN pin | Lower frequency, less critical |

**MODERATE (can be farther, &lt;50mm):**

| Component                    | Placement Rule            | Reason                       |
| ---------------------------- | ------------------------- | ---------------------------- |
| **Feedback resistors**       | &lt;50mm from FB pin      | Low current, low frequency   |
| **Enable/ON-OFF components** | &lt;50mm from control pin | Digital signal, not critical |

### Switching Converter PCB Layout Example

**Good Layout (Diagram2: +15V → +13.5V Buck):**

```
                [L1 Inductor]
                     │
                     │ ~10-20mm OK
                     │
    ┌────────────────┼────────────────┐
    │ U2 (LM2596S)   │                │
    │                │                │
    │  VIN ○─C6──────┘                │  C6 = 100nF ceramic
    │      ○ C5                       │  C5 = 100µF electrolytic
    │       <5mm!                     │  ↑ VERY close to VIN
    │                                 │
    │  OUT ○═════════○ D1             │  ← VERY SHORT (~5mm)
    │       <5mm!  Cathode            │     Part of hot loop!
    │                 │               │
    │                Anode            │
    │                 │               │
    │  GND ○──────────┼───────────────┤
    │                 │               │
    │   FB ○          │               │
    │      ○ R1/R2    │               │
    └─────────────────┼───────────────┘
                      │
                  [C3 470µF]  ← Output cap
                      │        (10-20mm from D1 OK)
                 ═════╪═════
                     GND

Layout priorities:
  1. C6 (100nF) RIGHT next to VIN pin (<5mm) ✅
  2. D1 cathode to OUT pin VERY short (<5mm) ✅
  3. Minimize hot loop area ✅
  4. Wide GND connections ✅
```

**Good Layout (Diagram4: +15V → -13.5V Inverting Buck-Boost):**

```
    [L3 Inductor]
         │
         │ ~10-20mm OK
         │
         ├─────────── System GND (0V)
         │
    ┌────┼─────────────┐
    │    │ U4          │
    │    │ (LM2596S)   │
    │    │             │
    │  VIN ○─C10───────┤  C10 = 100nF ceramic
    │      ○ C9        │  C9 = 100µF electrolytic
    │       <5mm!      │  ↑ VERY close to VIN
    │                  │
    │  OUT ○═══○ D3    │  ← CRITICAL: Very short! (<5mm)
    │      <5mm! Cathode  Hot loop component
    │             │    │
    │          Anode   │
    │             │    │
    │ ICGND ○─────┼────┤  IC GND at -13.5V
    │             │    │  (Bootstrapped)
    │             │    │
    │   FB ○      │    │
    │      ○ R5/R6│    │
    └─────────────┼────┘
                  │
              [C11 470µF]  ← CRITICAL: <5mm from D3!
                  │           Completes hot loop
             ═════╪═════
           System GND (0V)

Layout priorities:
  1. C10 (100nF) RIGHT next to VIN pin (<5mm) ✅
  2. D3 cathode to OUT pin VERY short (<5mm) ✅
  3. D3 anode to C11 VERY short (<5mm) ✅
  4. Minimize hot loop: OUT → D3 → C11 → GND ✅
```

### Trace Width for Switching Converters

| Connection      | Current         | Min Width (1oz copper) | Recommended           |
| --------------- | --------------- | ---------------------- | --------------------- |
| VIN → IC        | 2A avg, 4A peak | 1mm (40mil)            | 2mm (80mil)           |
| OUT → Diode     | 3A peak         | 1.5mm (60mil)          | 2mm (80mil)           |
| Diode → Cap     | 3A peak         | 1.5mm (60mil)          | 2mm (80mil)           |
| GND returns     | 3A avg          | 2mm (80mil)            | 3mm (120mil) or plane |
| Inductor traces | 3A avg          | 2mm (80mil)            | 2.5mm (100mil)        |
| Feedback        | &lt;1mA         | 0.25mm (10mil)         | 0.3mm (12mil)         |

**General rule:** Use **GND plane** on bottom layer for best performance!

---

## Linear Regulator Layout (Less Critical)

### Why Linear Regulators Are More Forgiving

```
Linear Regulator Operation:
  • No switching (DC pass-through)
  • Low di/dt (current changes slowly)
  • No high-frequency noise generation
  • Parasitic inductance doesn't cause spikes

Main concerns:
  1. Stability (prevent oscillation)
  2. Thermal management (heat dissipation)
  3. Low output impedance (good load regulation)
```

### Capacitor Placement for Linear Regulators

**For LM7812/LM7805/CJ7912 (Diagram5/6/7):**

```
Input Capacitors:
  • Ceramic (100-470nF): Should be close (<10-20mm)
  • Electrolytic (470µF): Can be farther (<50mm)

Output Capacitors:
  • Ceramic (100nF): Should be close (<10-20mm)
  • Electrolytic (470µF): Can be farther (<50mm)

Why close placement?
  • Prevents oscillation (stability)
  • Improves transient response
  • But NOT as critical as switching converters!
```

**Good Layout (Diagram5: +13.5V → +12V, LM7812):**

```
                    ┌──────────────┐
     +13.5V IN ─────┤1 IN      OUT 3├───── +12V OUT
                    │              │
                C14 ○  U6 (L7812)  ○ C17
               470nF│              │100nF
                    │              │
                C20 ○              ○ C21
               470µF│   GND 2      │470µF
                    └──────┬───────┘
                           │
                          GND

Component distances:
  • C14 (ceramic): 10-20mm from IN pin ✅ OK
  • C20 (electrolytic): 20-50mm from IN pin ✅ OK
  • C17 (ceramic): 10-20mm from OUT pin ✅ OK
  • C21 (electrolytic): 20-50mm from OUT pin ✅ OK

Much more relaxed than switching converters!
```

### Linear Regulator Layout Priority

**IMPORTANT (should be reasonably close):**

| Component              | Placement Rule        | Reason                    |
| ---------------------- | --------------------- | ------------------------- |
| **Input ceramic cap**  | &lt;20mm from IN pin  | Stability, HF filtering   |
| **Output ceramic cap** | &lt;20mm from OUT pin | Stability, load transient |

**MODERATE (can be farther):**

| Component               | Placement Rule        | Reason                    |
| ----------------------- | --------------------- | ------------------------- |
| **Input electrolytic**  | &lt;50mm from IN pin  | Bulk capacitance, LF only |
| **Output electrolytic** | &lt;50mm from OUT pin | Bulk capacitance, LF only |

**LOW PRIORITY:**

| Component                 | Placement Rule | Reason                |
| ------------------------- | -------------- | --------------------- |
| **Status LED + resistor** | Anywhere       | Low current indicator |
| **Enable resistors**      | &lt;50mm       | Digital signal        |

### Why Linear Regulators Are Less Sensitive

**No high di/dt:**

```
Switching converter during turn-off:
  di/dt = 3A / 10ns = 300 MA/µs ⚡
  V_spike = 100nH × 300MA/µs = 30V!

Linear regulator load step:
  di/dt = 1A / 1µs = 1 MA/µs ✅
  V_spike = 100nH × 1MA/µs = 0.1V

6 orders of magnitude difference!
```

**Frequency comparison:**

```
Switching converter:
  • Fundamental: 150kHz
  • Harmonics: up to 10MHz+
  → Very sensitive to parasitic L/C

Linear regulator:
  • Fundamental: DC (0Hz)
  • Transients: 1-100kHz
  → Much less sensitive to layout
```

---

## Comparison: Switching vs Linear

### Layout Sensitivity Comparison

| Aspect                    | Switching Converter      | Linear Regulator          |
| ------------------------- | ------------------------ | ------------------------- |
| **Critical hot loop**     | ✅ YES - must minimize   | ❌ NO - no switching loop |
| **Ceramic cap distance**  | &lt;5mm CRITICAL         | &lt;20mm OK               |
| **Diode placement**       | &lt;5mm CRITICAL         | N/A (no diode)            |
| **Electrolytic distance** | &lt;20mm important       | &lt;50mm OK               |
| **Trace inductance**      | CRITICAL (causes spikes) | Not critical              |
| **GND plane**             | Highly recommended       | Recommended               |
| **EMI concerns**          | HIGH (radiates if poor)  | LOW (DC only)             |
| **Layout difficulty**     | ⚡⚡⚡ DIFFICULT         | ✅ EASY                   |

### Visual Comparison

**Switching Converter - TIGHT layout required:**

```
    ┌─────┐
    │ IC  │
    │  ○══╪═ Diode     ← <5mm! CRITICAL
    │  ○  │            ← <5mm! CRITICAL
    └──┬──┘
       │
    [Cap]              ← <5mm! CRITICAL

Total critical area: ~1cm²
```

**Linear Regulator - RELAXED layout OK:**

```
    ┌─────┐
    │ IC  │
    │  ○────────○ Cap ← 1-2cm OK ✅
    │  ○────○ Cap     ← 2-5cm OK ✅
    └─────┘

Total area: ~10cm² (10× larger OK!)
```

---

## Thermal Considerations

### Switching Converters

```
Heat Generation:
  • Switching losses in IC
  • Diode forward drop losses
  • Inductor copper + core losses

Typical efficiency: 85-90%
Power dissipation: ~10-15% of output power

For 18W output:
  Heat dissipated ≈ 2-3W

Thermal strategy:
  ✅ Use thermal vias under IC
  ✅ Keep inductor away from heat-sensitive parts
  ✅ GND plane helps heat spreading
  ✅ Diode may need thermal relief
```

### Linear Regulators

```
Heat Generation:
  • (VIN - VOUT) × IOUT = Power dissipated as heat!

Example (LM7812, Diagram5):
  VIN = 13.5V
  VOUT = 12V
  IOUT = 1.2A

  Heat = (13.5V - 12V) × 1.2A = 1.8W ✅ Manageable

Example (LM7805, Diagram6):
  VIN = 7.5V
  VOUT = 5V
  IOUT = 0.5A

  Heat = (7.5V - 5V) × 0.5A = 1.25W ✅ Manageable

Thermal strategy:
  ✅ Use large GND plane (heat sink)
  ✅ Thermal vias under IC tab
  ✅ Keep away from heat-sensitive parts
  ✅ Minimize VIN-VOUT differential (our design does this!)
```

**Why our two-stage design is smart:**

```
Single-stage design (bad):
  LM7812 directly from 15V:
    Heat = (15V - 12V) × 1.2A = 3.6W ❌ Too hot!

Our two-stage design (good):
  Buck: 15V → 13.5V (efficient, ~90%)
  LDO: 13.5V → 12V (only 1.5V drop)
    Heat = (13.5V - 12V) × 1.2A = 1.8W ✅ Half the heat!
```

### Thermal Via Placement

```
IC with thermal pad (GND):

    ┌─────────────┐
    │ ╔═════════╗ │  ← IC package
    │ ║ Thermal ║ │
    │ ║   Pad   ║ │  ← Exposed pad on bottom
    │ ╚═════════╝ │
    └─────────────┘
         │││││      ← Thermal vias (multiple!)
         │││││         Connect to GND plane
    ═════╪═══╪══════ ← GND plane (bottom layer)
                        Acts as heatsink

Recommended:
  • 4-9 vias under thermal pad
  • Via diameter: 0.3-0.4mm
  • Space evenly
  • Connect to large copper area
```

---

## Common Mistakes

### Mistake 1: Long Hot Loop in Switching Converters ❌

```
BAD Layout:
    ┌─────┐
    │ IC  │
    │  ○──────────────────┐  ← 10cm trace to diode ❌
    └─────┘               │
                       [Diode]
                          │
                       [Cap] ── GND

Problems:
  • High parasitic inductance → voltage spikes
  • Large loop area → EMI radiation
  • Poor efficiency

GOOD Layout:
    ┌─────┐
    │ IC  │
    │  ○═╪ Diode  ← <5mm ✅
    │  ○ │        ← <5mm ✅
    └────┘
       [Cap]

Benefits:
  • Minimal parasitic inductance
  • Small loop area
  • Low EMI
```

### Mistake 2: No High-Frequency Decoupling ❌

```
BAD - Only bulk capacitor:
    ┌─────┐
    │ IC  │
    │ VIN ○─────── C (100µF only) ── GND
    └─────┘
             ↑
    Missing 100nF ceramic! ❌

GOOD - Bulk + Ceramic:
    ┌─────┐
    │ IC  │
    │ VIN ○─┬─── C1 (100nF ceramic, <5mm) ── GND
    └─────┘ │
            └─── C2 (100µF electrolytic) ── GND

Why both?
  • Ceramic (100nF): Filters HF switching noise (fast)
  • Electrolytic (100µF): Provides bulk energy (slow)
```

### Mistake 3: Thin Traces for High Current ❌

```
BAD - Thin trace:
    ───── 0.5mm trace, 3A current ❌

    • High resistance → voltage drop
    • High temperature → trace damage
    • Poor efficiency

GOOD - Wide trace:
    ══════ 2-3mm trace, 3A current ✅

    • Low resistance
    • Low temperature
    • Better efficiency

Rule of thumb (1oz copper):
  • 1A: ≥ 0.5mm (20mil)
  • 2A: ≥ 1mm (40mil)
  • 3A: ≥ 2mm (80mil)
  • >3A: Use GND plane or polygon
```

### Mistake 4: Treating LDO Like Switching Converter ❌

```
Waste of time:
  "I spent hours optimizing LDO layout to <1mm spacing!" ❌

Reality:
  • LDO doesn't need ultra-tight layout
  • 10-20mm is perfectly fine
  • Focus effort on switching stages instead!

Better use of time:
  • Optimize switching converter hot loop ✅
  • Ensure good thermal design ✅
  • Double-check feedback network ✅
```

### Mistake 5: Feedback Trace Near Switching Node ❌

```
BAD Layout:
                Switching Node (noisy!)
                      ↓
    ┌─────┐    OUT ○═╪═ Diode
    │ IC  │          │
    │  FB ○──────────┤  ← FB trace runs parallel ❌
    └─────┘          │     Picks up switching noise!

GOOD Layout:
                Switching Node
                      ↓
    ┌─────┐    OUT ○═╪═ Diode
    │ IC  │          │
    │  FB ○          │
    └──┬──┘          │
       │             │
       └─────────────┘  ← FB trace routes away ✅
                           Avoids switching node
```

---

## Practical Checklist

### For Switching Converters (LM2596S)

**Layout Review:**

- [ ] High-frequency decoupling cap (100nF ceramic) &lt;5mm from VIN pin
- [ ] Catch diode cathode &lt;5mm from OUT pin
- [ ] Catch diode anode &lt;5mm from output capacitor
- [ ] Hot loop area minimized (&lt;1cm²)
- [ ] Output capacitor has wide connection to GND
- [ ] Inductor within 20mm of OUT pin
- [ ] Feedback trace routed away from switching node
- [ ] No ground loops (use star or plane)

**Trace Widths:**

- [ ] VIN power trace ≥ 2mm (80mil)
- [ ] OUT to diode ≥ 2mm (80mil)
- [ ] Diode to capacitor ≥ 2mm (80mil)
- [ ] GND returns ≥ 3mm (120mil) or use plane
- [ ] Feedback traces ≥ 0.3mm (12mil)

**Thermal:**

- [ ] Thermal vias under IC (4-9 vias, 0.3-0.4mm diameter)
- [ ] Inductor has thermal relief or clearance
- [ ] GND plane on bottom layer for heat spreading

### For Linear Regulators (LM78xx/LM79xx)

**Layout Review:**

- [ ] Input ceramic cap &lt;20mm from IN pin (relaxed OK)
- [ ] Output ceramic cap &lt;20mm from OUT pin (relaxed OK)
- [ ] Input bulk cap &lt;50mm from IN pin
- [ ] Output bulk cap &lt;50mm from OUT pin
- [ ] GND connections short and wide

**Trace Widths:**

- [ ] IN power trace ≥ 2mm (80mil)
- [ ] OUT power trace ≥ 2mm (80mil)
- [ ] GND returns ≥ 2mm (80mil) or use plane

**Thermal:**

- [ ] Thermal vias under IC tab (4-9 vias)
- [ ] GND plane for heat spreading
- [ ] Check junction temperature calculations

---

## Summary

### Key Takeaways

**Switching Converters (Critical!):**

```
✅ Hot loop must be &lt;5mm and &lt;1cm² area
✅ High-freq decoupling &lt;5mm from IC
✅ Catch diode &lt;5mm from OUT pin
✅ Wide GND connections
✅ Use GND plane
⚡ Layout makes or breaks the design!
```

**Linear Regulators (Relaxed):**

```
✅ Ceramic caps &lt;20mm from IC (OK)
✅ Electrolytic caps &lt;50mm from IC (OK)
✅ Focus on thermal design
✅ GND plane helpful but not critical
😊 Layout is much more forgiving!
```

### Design Philosophy

```
Our Two-Stage Architecture:

Stage 1 (Switching):
  • High efficiency (90%)
  • Sensitive to layout ⚡
  → Spend TIME on layout!

Stage 2 (Linear):
  • Low noise
  • Relaxed layout ✅
  → Quick and easy!

Best of both worlds! ✨
```

---

## Related Documentation

- [Inductor Voltage Reversal](/docs/learning/inductor-voltage-reversal) - How switching converters work
- [Buck Converter Feedback](/docs/learning/buck-converter-feedback) - Feedback network design
- [Two-Stage DC-DC + LDO Architecture](/docs/learning/two-stage-dc-dc-ldo-architecture) - Why we use this approach
- [Linear Regulator Capacitors](/docs/learning/linear-regulator-capacitors) - Capacitor selection for LDOs

---

**Document created:** 2026-01-04
**Applies to:** All power circuits in zudo-pd project
**Reference circuits:** Diagram2, 3, 4 (switching), Diagram5, 6, 7 (linear)
