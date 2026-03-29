---
title: GND and Component Placement Strategy
sidebar_position: 3
---

# GND and Component Placement Strategy

Practical guide for 2-layer PCB layout using unified ground plane with noise control through component placement.

## Overview

**Strategy:** Single unified GND plane + Physical component separation

- **Schematic:** Use "GND" label for all ground connections
- **PCB Bottom Layer:** Solid copper pour (unified ground plane)
- **PCB Top Layer:** Strategic component placement for noise isolation
- **Key Principle:** Noise reduction through physical distance, not ground plane splitting

---

## Component Noise Classification

### High Noise Components (Keep Separate!)

**Switching DC-DC Converters:**

| Component       | Type              | Noise Source                          | Isolation Required               |
| --------------- | ----------------- | ------------------------------------- | -------------------------------- |
| **U2, U3, U4**  | LM2596S-ADJ       | High-frequency switching (150-300kHz) | 3-5cm from clean circuits        |
| **L1, L2, L3**  | 100µH Inductors   | Magnetic field radiation              | 5-10mm clearance around inductor |
| **D1, D2, D3**  | SS34 Schottky     | Fast switching transients             | Keep switching loop tight        |
| **C3, C4, C11** | 470µF Output caps | Pulsing currents                      | Close to inductor output         |

**USB-PD Input Stage:**

| Component | Type            | Noise Level | Notes                                   |
| --------- | --------------- | ----------- | --------------------------------------- |
| **U1**    | STUSB4500       | Medium      | Digital USB-PD protocol, some switching |
| **J1**    | USB-C connector | Low-Medium  | Input noise from adapter                |

### Low Noise Components (Sensitive to Noise)

**Linear Regulators (Buffer Zone):**

| Component | Type       | Function              | Placement                    |
| --------- | ---------- | --------------------- | ---------------------------- |
| **U6**    | L7812CD2T  | +12V Linear regulator | Between switching and output |
| **U7**    | L7805ABD2T | +5V Linear regulator  | Between switching and output |
| **U8**    | CJ7912     | -12V Linear regulator | Between switching and output |

**Output Stage (Cleanest Area):**

| Component    | Type                | Sensitivity | Priority                        |
| ------------ | ------------------- | ----------- | ------------------------------- |
| **J10, J11** | Eurorack connectors | HIGH        | Maximum distance from switching |
| **PTC1-3**   | Resettable fuses    | Low         | Output protection area          |
| **TVS1-3**   | TVS diodes          | Low         | Output protection area          |
| **LED2-4**   | Status indicators   | Low         | Can go anywhere                 |

---

## PCB Layout Strategy

### Left-to-Right Power Flow

```
┌──────────────────────────────────────────────────────────────┐
│                    PCB Top View (80mm × 50mm)                │
│                                                              │
│  ┌──────────┐     ┌─────────────────┐     ┌──────────────┐ │
│  │ STAGE 1  │ →→→ │    STAGE 2      │ →→→ │  STAGE 3+4   │ │
│  │ USB-PD   │     │    DC-DC        │     │  Linear+Out  │ │
│  │ Input    │     │    Switching    │     │              │ │
│  ├──────────┤     ├─────────────────┤     ├──────────────┤ │
│  │          │     │                 │     │              │ │
│  │ J1       │     │ U2  L1  D1  C3  │     │ U6  C14 C17  │ │
│  │ U1       │     │                 │     │              │ │
│  │ C1, C2   │     │ U3  L2  D2  C4  │     │ U7  C15 C18  │ │
│  │ C30      │     │                 │     │              │ │
│  │ R11-R13  │     │ U4  L3  D3  C11 │     │ U8  C16 C19  │ │
│  │          │     │                 │     │              │ │
│  │          │     │ C5-C10          │     │ PTC1-3       │ │
│  │          │     │ C31-C33         │     │ TVS1-3       │ │
│  │          │     │ R1-R6           │     │ F1-F3        │ │
│  │          │     │                 │     │ J10,J11 Out  │ │
│  └──────────┘     └─────────────────┘     └──────────────┘ │
│      ║                    ║                      ║         │
│     Vias                 Vias                   Vias       │
│      ↓                    ↓                      ↓         │
│  ═══════════════════════════════════════════════════════   │
│           UNIFIED GND PLANE (Bottom Layer)                 │
│  ═══════════════════════════════════════════════════════   │
│                                                              │
│  Noise Level:  MEDIUM  →→→  HIGH  →→→  LOW                 │
│  Distance:     0-15mm       15-50mm      50-80mm            │
└──────────────────────────────────────────────────────────────┘
```

### Physical Spacing Requirements

| Between                      | Minimum Distance | Reason                              |
| ---------------------------- | ---------------- | ----------------------------------- |
| Stage 1 → Stage 2            | 2-3cm            | Isolate USB-PD from switching noise |
| Stage 2 → Stage 3            | 2-3cm            | Isolate switching from output       |
| Switching circuits (U2-U4)   | 5-10mm           | Magnetic field interference         |
| Inductors (L1-L3)            | 10-15mm          | Strong magnetic coupling            |
| Switching → Output connector | 5cm+             | Maximum isolation for clean output  |

---

## Switching Converter Layout (Critical!)

### Minimize Current Loop Area

**Each LM2596S must have TIGHT, COMPACT layout:**

```
Target: Minimize this loop area
        ↓
    ┌───────────────────┐
    │                   │
VIN ┴ C_in              │
    │        ┌──────┐   │
    └───→ 1 │      │ 2 ┴ L ───→ VOUT
            │ U2   │   │
    ┌───→ 3 │ LM   │   │
    │        │ 2596 │   │
    │      5 │      │   │
   GND       └──────┘   │
                        │
                    ┌───┘
                    D (flyback)
                    │
                   GND

Keep ALL components within 20mm radius of IC
```

### Component Proximity Rules

**For each converter (U2, U3, U4):**

| Component                    | Max Distance from IC | Pin Connection        | Priority |
| ---------------------------- | -------------------- | --------------------- | -------- |
| Input bulk cap (C5/C7/C9)    | **5mm**              | VIN (pin 1)           | CRITICAL |
| Input decoupling (C6/C8/C10) | **3mm**              | VIN (pin 1)           | CRITICAL |
| Inductor (L1/L2/L3)          | **10mm**             | VOUT (pin 2)          | HIGH     |
| Flyback diode (D1/D2/D3)     | **5mm**              | VOUT (pin 2)          | HIGH     |
| Output cap (C3/C4/C11)       | **10mm**             | After inductor        | MEDIUM   |
| Feedback R upper (R1/R3/R5)  | **10mm**             | FB (pin 4)            | MEDIUM   |
| Feedback R lower (R2/R4/R6)  | **10mm**             | FB (pin 4)            | MEDIUM   |
| Compensation cap (C31-C33)   | **15mm**             | Parallel with R upper | LOW      |

### Ground Via Placement

**Multiple vias for low impedance:**

```
Component ground connections:

High current (4+ vias):
  ●●●●
  C5 ────→ GND plane
  ●●●●

Medium current (2-3 vias):
  ●●
  U2 pin 3 ────→ GND plane
  ●

Low current (1 via):
  ●
  R2 ────→ GND plane
```

**Via count by component:**

| Component                 | Current  | Via Count | Via Size    |
| ------------------------- | -------- | --------- | ----------- |
| Input caps (C5, C7, C9)   | 2-3A     | 4 vias    | 0.5mm drill |
| Output caps (C3, C4, C11) | 2-3A     | 4 vias    | 0.5mm drill |
| IC GND (U2-U4 pin 3)      | 2-3A     | 2-3 vias  | 0.5mm drill |
| IC GND (U2-U4 pin 5)      | Signal   | 1 via     | 0.3mm drill |
| Diode cathode (D1-D3)     | 2-3A     | 2 vias    | 0.5mm drill |
| Feedback resistors        | &lt;10mA | 1 via     | 0.3mm drill |

---

## Power Trace Width Guidelines

**1oz copper (35µm), 10°C temperature rise:**

| Net Name            | Max Current | Min Trace Width | Recommended    |
| ------------------- | ----------- | --------------- | -------------- |
| +15V (USB-PD input) | 3A          | 1.2mm           | **1.5-2.0mm**  |
| +13.5V (U2 output)  | 2A          | 0.8mm           | **1.5mm**      |
| +7.5V (U3 output)   | 2A          | 0.8mm           | **1.5mm**      |
| -13.5V (U4 output)  | 1.5A        | 0.6mm           | **1.0mm**      |
| +12V (final output) | 1.5A        | 0.6mm           | **1.0mm**      |
| +5V (final output)  | 1.2A        | 0.5mm           | **0.8mm**      |
| -12V (final output) | 1A          | 0.5mm           | **0.8mm**      |
| GND (return)        | 3A+         | Plane           | **Solid pour** |
| Signal (FB, CFG)    | &lt;10mA    | 0.2mm           | **0.3mm**      |

**Note:** Always use **thicker traces** than minimum for reliability and lower voltage drop.

---

## Via Stitching for EMI Reduction

### Via Fence Around Noisy Components

```
Add extra vias around switching ICs to provide low-impedance return path:

     ●  ●  ●  ●  ●  ●
    ●                ●
    ●   ┌────────┐   ●
    ●   │  U2    │   ●  ← Via fence (1-2mm spacing)
    ●   │LM2596S │   ●     Connects top GND to bottom GND plane
    ●   └────────┘   ●     Reduces EMI radiation
    ●                ●
     ●  ●  ●  ●  ●  ●

Spacing: 1-2mm between vias
Benefit: Creates "Faraday cage" effect
```

### Recommended Via Stitching Locations

| Area                         | Via Spacing | Purpose                    |
| ---------------------------- | ----------- | -------------------------- |
| Around U2, U3, U4            | 1-2mm       | EMI containment            |
| Under inductors L1-L3        | 2-3mm       | Magnetic field return path |
| Between switching and output | 5mm         | Ground continuity          |
| Board edges                  | 5-10mm      | Edge return currents       |
| Thermal pads (U6-U8)         | Multiple    | Heat dissipation + GND     |

---

## Layout Checklist

### Before Routing

- [ ] Components placed left-to-right (power flow direction)
- [ ] 2-3cm spacing between switching and output stages
- [ ] Each LM2596S circuit is compact (&lt;20mm radius)
- [ ] Input caps &lt;5mm from IC VIN pins
- [ ] Inductors have 10-15mm clearance around them
- [ ] Output connectors (J10, J11) at maximum distance from switching

### During Routing

- [ ] Power traces ≥1.5mm width for high current
- [ ] Switching loops minimized (tight layout)
- [ ] Feedback traces routed away from inductors
- [ ] No sensitive traces cross over switching nodes
- [ ] GND vias placed at every component GND pad

### After Routing, Before GND Pour

- [ ] All power traces routed
- [ ] All signal traces routed
- [ ] No unconnected GND pads
- [ ] Via stitching planned around noisy components

### GND Plane (Bottom Layer)

- [ ] Solid copper pour on entire bottom layer
- [ ] No splits or gaps in GND plane
- [ ] Via stitching added (1-2mm spacing around ICs)
- [ ] Thermal relief for vias (if needed for hand soldering)
- [ ] Clearance from board edge (0.5-1mm)

### Final Checks

- [ ] DRC (Design Rule Check) passes
- [ ] No airwires (all nets connected)
- [ ] GND net connected to all GND pads
- [ ] Power trace widths meet current requirements
- [ ] Component clearances adequate for assembly

---

## Common Mistakes to Avoid

### ❌ Don't Do This

**1. Large current loops:**

```
❌ BAD:
VIN ───────┐
           │ (10mm)
           C5 (input cap far from IC)
           │
           └──→ U2 VIN pin

Large loop = More EMI, more noise
```

**2. Feedback trace near inductor:**

```
❌ BAD:
         L1 (inductor)
          ↓
    FB trace crosses here  ← Picks up magnetic noise
          ↓
         R1, R2

Route feedback traces away from inductors!
```

**3. Interleaving noisy and clean:**

```
❌ BAD:
[U2 switching] [U6 linear] [U3 switching] [U7 linear]
 ← Mixed placement = noise coupling

✅ GOOD:
[U2] [U3] [U4] ─gap─ [U6] [U7] [U8]
 ← Grouped by noise level
```

**4. Output connector near switching:**

```
❌ BAD:
[J10,J11 Output] ──→ [U2 Switching] ──→ [Linear regs]
 ← Output picks up switching noise

✅ GOOD:
[U2 Switching] ──→ [Linear regs] ──→ [J10,J11 Output]
 ← Maximum distance from noise source
```

### ✅ Do This Instead

**1. Tight current loops:**

```
✅ GOOD:
VIN ─┬─ C5 (&lt;5mm from VIN pin)
     │
     └──→ U2 VIN pin

Minimal loop = Less EMI
```

**2. Route feedback away from magnetic fields:**

```
✅ GOOD:
         L1 (inductor)

         (5mm clearance)

    FB trace routed below
          ↓
         R1, R2
```

**3. Group by noise level:**

```
✅ GOOD:
┌──────────────┐  ┌──────────┐  ┌──────────────┐
│ All Switching│  │ Linears  │  │   Output     │
│ U2, U3, U4   │→→│ U6,U7,U8 │→→│ J10,J11,LEDs │
└──────────────┘  └──────────┘  └──────────────┘
```

**4. Maximum isolation for output:**

```
✅ GOOD:
[USB-PD] → [Switching] → [Linear] → [Protection] → [J10,J11]
                                                      ↑
                                          Cleanest location
```

---

## Advanced Tips

### Current Return Paths

**High-frequency currents follow path directly beneath signal trace:**

```
Top Layer (signal):
    ═════════════════════════  VIN trace

Bottom Layer (GND plane):
    ╔═════════════════════════  Return current
    ║  flows directly beneath
    ╚═════════════════════════

Keep GND plane solid (no splits) for direct return paths!
```

### Thermal Considerations

**Linear regulators (U6, U7, U8) dissipate heat:**

| Regulator | Input  | Output | Current | Power Dissipation         |
| --------- | ------ | ------ | ------- | ------------------------- |
| U6 (7812) | 13.5V  | 12V    | 1.5A    | (13.5-12)×1.5 = **2.25W** |
| U7 (7805) | 7.5V   | 5V     | 1.2A    | (7.5-5)×1.2 = **3.0W**    |
| U8 (7912) | -13.5V | -12V   | 1A      | (13.5-12)×1 = **1.5W**    |

**Thermal management:**

- Use thermal vias from IC tab to bottom GND plane (heat sink)
- 4-9 vias under thermal pad (0.5mm drill)
- GND plane acts as heat spreader
- Consider copper pour on top layer as well

### Inductor Orientation

**Orient inductors to minimize magnetic coupling:**

```
Plan View:

    L1      L2      L3
    ║       ║       ║    ← All inductors parallel
    ║       ║       ║      (fields in same direction)
    ║       ║       ║
    ↓       ↓       ↓

Alternative (if space limited):

    L1  →   ← L2    → L3    ← Alternating orientation
                              (fields partially cancel)
```

---

## Summary

### Key Principles

1. ✅ **Unified ground plane** - Solid copper pour on bottom, no splits
2. ✅ **Physical separation** - 2-3cm between noisy and clean sections
3. ✅ **Tight switching loops** - Components &lt;5mm from IC pins
4. ✅ **Left-to-right flow** - USB → Switching → Linear → Output
5. ✅ **Multiple ground vias** - 2-4 vias per high-current node
6. ✅ **Wide power traces** - 1.5-2mm for high current paths
7. ✅ **Via stitching** - 1-2mm spacing around noisy ICs

### Expected Results

With proper component placement and unified GND plane:

- ✅ Output ripple: &lt;1mVp-p (meets modular synth requirements)
- ✅ EMI emissions: Within limits (no excessive radiation)
- ✅ Thermal performance: Linear regulators stay cool with GND plane heatsinking
- ✅ Ground offset: &lt;10mV between stages (negligible for audio)

**Component placement is MORE important than ground plane splitting for noise control on 2-layer boards!**
