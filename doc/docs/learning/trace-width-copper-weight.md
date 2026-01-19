# PCB Trace Width and Copper Weight

Understanding how trace width and copper weight affect current carrying capacity, and why USB-C connector pins are sized the way they are.

## Overview

When designing PCBs for power applications, two key parameters determine how much current a trace can safely carry:

1. **Trace width** - The physical width of the copper trace
2. **Copper weight** - The thickness of the copper layer (measured in oz/ft²)

This document explains the relationship between these parameters and current capacity, based on IPC-2221 standards.

---

## Copper Weight Basics

### What is Copper Weight?

Copper weight is measured in **ounces per square foot (oz/ft²)**:

| Copper Weight | Thickness | Common Use                      |
| ------------- | --------- | ------------------------------- |
| 0.5 oz        | 17.5 µm   | Fine-pitch, low current         |
| **1 oz**      | **35 µm** | **Standard (most PCBs)**        |
| 2 oz          | 70 µm     | High current, power electronics |
| 3 oz          | 105 µm    | Heavy power, automotive         |

### 1oz vs 2oz Comparison

```
Cross-section view:

1oz copper (35µm):
═══════════════════  ← 35µm thick
       0.7mm wide

2oz copper (70µm):
███████████████████  ← 70µm thick (2× more copper)
       0.7mm wide
```

**Key point**: 2oz copper has **twice the cross-sectional area**, so it can carry approximately **1.4× more current** at the same temperature rise (not 2×, due to thermal dynamics).

---

## IPC-2221 Current Capacity

### The Standard

IPC-2221 provides guidelines for trace current capacity based on:

- Trace width
- Copper thickness
- Acceptable temperature rise
- External vs internal layer

### Temperature Rise Explained

**Temperature rise** is how much hotter the trace gets compared to ambient:

```
Temperature
    ↑
    │            ┌─────────────── Steady state (equilibrium)
    │           /
    │          /
    │         /  ← Takes 5-15 minutes to stabilize
    │        /
    │       /
    │──────┘
    └────────────────────────────→ Time
         Current ON
```

**Important**: This is **steady-state** temperature after thermal equilibrium, not a rate of increase. Once equilibrium is reached, temperature stops rising.

### Current Capacity Table (External Layer)

**1oz Copper (35µm):**

| Trace Width | 10°C Rise | 20°C Rise | 30°C Rise | 45°C Rise |
| ----------- | --------- | --------- | --------- | --------- |
| 0.25mm      | ~0.8A     | ~1.2A     | ~1.5A     | ~1.8A     |
| 0.5mm       | ~1.5A     | ~2.2A     | ~2.7A     | ~3.3A     |
| **0.7mm**   | **~2.5A** | **~3.5A** | **~4.5A** | **~5.5A** |
| 1.0mm       | ~3.2A     | ~4.5A     | ~5.5A     | ~6.5A     |
| 2.0mm       | ~5.5A     | ~7.5A     | ~9.0A     | ~11A      |

**2oz Copper (70µm):**

| Trace Width | 10°C Rise | 20°C Rise | 30°C Rise | 45°C Rise |
| ----------- | --------- | --------- | --------- | --------- |
| 0.25mm      | ~1.2A     | ~1.7A     | ~2.1A     | ~2.6A     |
| 0.5mm       | ~2.2A     | ~3.1A     | ~3.8A     | ~4.7A     |
| **0.7mm**   | **~3.5A** | **~5.0A** | **~6.0A** | **~7.5A** |
| 1.0mm       | ~4.5A     | ~6.3A     | ~7.7A     | ~9.5A     |
| 2.0mm       | ~7.7A     | ~10.5A    | ~12.5A    | ~15A      |

---

## Why USB-C Connector Pins Are This Size

### The Connection

Looking at our USB-C connector (6-pin power-only):

```
USB Type-C 6-Pin Connector

┌──────────────────┐
│   1    2    3    │  Top Row
│  GND  VBUS  CC1  │
└──────────────────┘
┌──────────────────┐
│  CC2  VBUS  GND  │  Bottom Row
│   4    5    6    │
└──────────────────┘
```

The VBUS pins have a specific pad size (approximately **0.7mm width** traces on PCB) because:

1. **USB-PD 3A rating** requires traces that can handle 3A
2. **0.7mm @ 1oz copper** handles ~2.5-3.5A (depending on temp rise)
3. **Two VBUS pins in parallel** = 1.5A per pin = very comfortable margin

### Current Distribution

```
Pin 2 (VBUS) ──┬─→ ~1.5A
               │
               ├─→ Total: 3A to circuit
               │
Pin 5 (VBUS) ──┘─→ ~1.5A
```

This is why USB-C connectors use **multiple power pins** - to distribute current and reduce individual pin stress.

---

## This Project's Design Decision

### Our Requirements

| Rail           | Voltage | Current | Power |
| -------------- | ------- | ------- | ----- |
| Input (USB-PD) | 15V     | 3A max  | 45W   |
| +12V output    | 12V     | 1.5A    | 18W   |
| -12V output    | -12V    | 1A      | 12W   |
| +5V output     | 5V      | 1.5A    | 7.5W  |

### Trace Width Selection: 0.7mm

We chose **0.7mm traces** for power lines because:

```
USB-C VBUS pin pad ≈ 0.7mm
    ↓
Matching our power traces = 0.7mm
    ↓
At 1oz copper: handles ~2.5-3.5A
    ↓
Our max current: 3A (input only)
    ↓
Result: Adequate with ~15-20°C rise ✓
```

### Copper Weight Decision: 1oz

**We chose 1oz copper** because:

| Factor       | 1oz             | 2oz               |
| ------------ | --------------- | ----------------- |
| Cost         | Standard        | +$5-15 extra      |
| 0.7mm @ 3A   | ~15-20°C rise   | ~10°C rise        |
| Availability | Always in stock | Usually available |
| Our need     | Sufficient      | Overkill          |

**Calculation for 0.7mm trace @ 3A with 1oz copper:**

- Temperature rise: ~15-20°C above ambient
- If ambient is 25°C, trace reaches ~40-45°C
- Well below any damage threshold
- Components rated for 85°C+ operation

---

## Current Limits and Safety Margins

### What Happens at Higher Currents?

For **0.7mm trace, 1oz copper**:

| Current  | Temp Rise     | Status                    |
| -------- | ------------- | ------------------------- |
| 2.5A     | +10°C         | Very safe                 |
| 3.0A     | +15°C         | Safe ✓ (our design point) |
| 4.0A     | +25°C         | OK                        |
| 5.0A     | +40°C         | Warm but acceptable       |
| 6.0A     | +60°C         | Hot, near limit           |
| **7-8A** | **+80-100°C** | **Problem zone**          |
| 10A+     | -             | Destruction               |

### Failure Points

| Temperature    | What Happens                           |
| -------------- | -------------------------------------- |
| +45°C rise     | IPC-2221 max recommended               |
| +80-100°C rise | Solder joints weaken                   |
| ~105°C rise    | FR4 glass transition (~130°C absolute) |
| ~150°C+        | Trace delamination, board damage       |

### Our Safety Margin

```
Design point:     3A @ 0.7mm, 1oz
Trace limit:      ~5-6A before getting hot
Connector limit:  3-5A (USB-C rating)
                  ↓
Limiting factor:  USB-C connector (not trace)
Safety margin:    ~1.7-2× on traces ✓
```

---

## Via Behavior (Important!)

### Vias Are NOT Solid Copper

A common misconception is that larger vias = more copper = better thermal/electrical conductivity.

**Reality:**

```
What you might imagine:          What actually happens:

    ┌──────────┐                     ┌──────────┐
    │██████████│                     │┌────────┐│
    │██SOLID██ │                     ││  AIR   ││
    │██COPPER██│  ← NOT this         ││ (empty)││  ← THIS
    │██████████│                     │└────────┘│
    └──────────┘                     └──────────┘
                                      ↑        ↑
                                   Thin copper plating
                                   (25-35 microns)
```

**Manufacturing process:**

1. Drill hole through PCB
2. Electroplate thin copper layer on hole walls
3. Center stays **hollow** (air)

### Multiple Small Vias Beat One Large Via

For thermal connections (like IC thermal pads):

```
One 0.5mm via:              Nine 0.3mm vias:

    ┌─────┐                    ┌─┐ ┌─┐ ┌─┐
    │     │                    └─┘ └─┘ └─┘
    │     │  1× barrel         ┌─┐ ┌─┐ ┌─┐
    │     │  surface           └─┘ └─┘ └─┘
    └─────┘                    ┌─┐ ┌─┐ ┌─┐
                               └─┘ └─┘ └─┘

Copper wall area:            Copper wall area:
π × 0.5mm × 1.6mm           9 × π × 0.3mm × 1.6mm
≈ 2.5 mm²                   ≈ 13.6 mm²  ← 5× more!
```

---

## Practical Guidelines

### Trace Width Quick Reference

| Current | Min Width (1oz)   | Recommended |
| ------- | ----------------- | ----------- |
| 0.5A    | 0.2mm             | 0.3mm       |
| 1A      | 0.4mm             | 0.5mm       |
| 2A      | 0.6mm             | 0.8mm       |
| **3A**  | **0.7mm**         | **1.0mm**   |
| 5A      | 1.5mm             | 2.0mm       |
| 10A+    | Use polygon/plane | GND pour    |

### When to Use 2oz Copper

Consider 2oz copper when:

- Continuous current &gt;5A per trace
- Limited board space (can't make traces wider)
- High ambient temperature environment
- Automotive/industrial applications
- Thermal management is critical

### For This Project

**1oz copper with 0.7mm traces is the right choice:**

- Cost effective
- Sufficient for 3A with acceptable temperature rise
- Standard JLCPCB option
- Traces won't be the weak point (USB-C connector limits current first)

---

## Related Documentation

- [PCB Layout Guidelines](/docs/learning/pcb-layout-power-circuits) - Complete layout rules for power circuits
- [USB Type-C Pinout](/docs/learning/usb-type-c-pinout) - Why USB-C has multiple power pins
- [Two-Stage Architecture](/docs/learning/two-stage-dc-dc-ldo-architecture) - Our power conversion strategy

---

**Document created:** 2026-01-11
**Applies to:** zudo-pd PCB design
**Design decision:** 1oz copper, 0.7mm power traces for 3A USB-PD input
