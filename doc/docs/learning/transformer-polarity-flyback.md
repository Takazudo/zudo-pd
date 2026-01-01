---
sidebar_position: 4
---

# Transformer Polarity & Phasing: Why Direction Matters in Flyback Converters

Understanding transformer dot notation and why connecting a flyback transformer backwards will reverse your output voltage polarity!

## The Question

When designing the LM2586 flyback converter circuit for voltage inversion (+15V → -15V), a critical question came up:

> "About this transformer, is the direction important? Is it common knowledge of transformers?"

**Short answer**: Yes! Transformer polarity is **absolutely critical** for flyback converters. Connect it backwards and you'll get positive voltage instead of negative. This is fundamental knowledge for all switching power supply design.

## What is Dot Notation?

Transformer windings have **polarity marks** (dots) that show which terminals are **in-phase** with each other.

```
MSD1514-473MED Coupled Transformer (4-pin SMD):

    ●  Pin 1 (Dot marking - visible on PCB footprint)
    ┌─────────┐
    │1   •  4│●  Pins 1 & 4 have dots (in-phase)
    │  T1     │
    │2       3│  Pins 2 & 3 (opposite phase)
    └─────────┘

Pin Assignment:
- Pins 1-2: Primary winding (47µH)
- Pins 3-4: Secondary winding (47µH)
- Dot on Pin 1 and Pin 4 = same magnetic polarity
```

**What "in-phase" means**: When Pin 1 is positive, Pin 4 is also positive at the same instant. When Pin 1 goes negative, Pin 4 also goes negative.

### Physical Meaning of Dots

The dot indicates the **start of the winding** (where the wire begins). Transformers with dots in the same relative position have windings wound in the same direction.

```
Winding Direction (Conceptual):

Primary:          Secondary:
  Start •           Start •
   ↓ 1               ↓ 4
   │                 │
   │ 47µH            │ 47µH
   │                 │
   ↓ 2               ↓ 3
  End               End

Same winding direction = In-phase
```

## Why Polarity Matters for Flyback Converters

Flyback converters use transformer polarity to **invert voltage**. The secondary must be wound opposite to the primary's connection to create negative output.

### Correct Connection (Voltage Inversion)

```
Flyback Topology (Correct Orientation):

+15V IN ──┤1  •T1  4│●──── GND
          │         │
      SW ─┤2      3├───── D4 Cathode → -15V OUT

Energy Flow:
1. SW closes: Current flows 1→2 in primary, storing magnetic energy
2. SW opens: Magnetic field collapses, inducing voltage in secondary
3. Due to winding polarity: Pin 3 swings NEGATIVE, Pin 4 stays at GND
4. D4 rectifies negative pulses → -15V DC output

Result: Voltage INVERTED (+15V → -15V) ✅
```

### Wrong Connection (No Inversion!)

```
Flyback Topology (Incorrect - Rotated 180°):

+15V IN ──┤2    T1  3│──── GND
          │         │
      SW ─┤1  •   4│●──── D4 Cathode → +15V?? WRONG!

Energy Flow:
1. SW closes: Current flows 2→1 in primary
2. SW opens: Magnetic field collapses
3. Due to REVERSED polarity: Pin 4 swings POSITIVE, Pin 3 stays at GND
4. D4 blocks positive pulses (wrong direction!)

Result: Circuit doesn't work - no voltage inversion! ❌
```

**What happens**: The output will either be:

- **Wrong polarity** (+15V instead of -15V)
- **No output** (diode blocking everything)
- **Damaged components** (if diode conducts in reverse)

## How Flyback Energy Transfer Works

Unlike normal transformers (which transfer energy continuously), flyback transformers work in **two phases**:

### Phase 1: Energy Storage (Switch ON)

```
Switch Closed (SW pin connects to GND internally):

+15V ──┤1  •T1      │
       │            │  Secondary side:
       │ Primary    │  No current flows
       │ current    │  (D4 blocks)
      SW│ flows     │
       ↓            │
      GND          GND

Magnetic field builds up in transformer core
```

### Phase 2: Energy Release (Switch OFF)

```
Switch Open (SW pin floating):

       │            │●4── GND
       │ Primary    │
       │ voltage    │  Secondary
       │ spikes     │  voltage
      SW│ high      │  appears
       │            │  NEGATIVE
       X (open)    3├─→ D4 → -15V OUT

Magnetic field collapses, energy transfers to secondary
```

**Critical Point**: The polarity of the secondary voltage during collapse depends on how the windings are connected relative to their dots!

## Dot Convention Rules

### Rule 1: Dots Show Positive Voltage at Same Time

When current **enters** a dotted terminal on the primary, voltage will be **positive** at the dotted terminal on the secondary.

```
Primary current enters Pin 1 (dot)
  → Secondary Pin 4 (dot) goes positive
  → Secondary Pin 3 (no dot) goes negative
```

### Rule 2: For Voltage Inversion, Connect Opposite Polarity

For flyback inversion, we **intentionally** connect the secondary backwards relative to how we'd connect a normal step-down transformer:

```
Normal Step-Down Transformer:
Input+ → Primary dot      Secondary dot → Output+
Input- → Primary (no dot) Secondary (no dot) → Output-
(Same polarity in/out)

Flyback Inverter:
Input+ → Primary dot      Secondary dot → GND
Input- → Primary (no dot) Secondary (no dot) → Output-
(Opposite polarity = voltage inversion!)
```

## PCB Assembly Considerations

### Identifying Pin 1 on the Footprint

When placing T1 on the PCB, **always verify the pin 1 marking**:

```
MSD1514 Footprint Markings:
- Pin 1 dot (filled circle) on top-left or top-right corner
- Sometimes has beveled corner or notch
- Check component datasheet for orientation
```

**Critical**: If you rotate the component 180° during assembly, the transformer will be backwards!

### Verification Checklist

Before PCB assembly:

- ✅ **Pin 1 marking** on footprint matches schematic
- ✅ **Primary pins (1-2)** connect to +15V and SW
- ✅ **Secondary pins (3-4)** connect to D4 cathode and GND
- ✅ **Dot on Pin 4** connects to GND (for inversion)
- ✅ **No-dot on Pin 3** connects to D4 cathode (becomes -15V)

### Common Assembly Mistakes

| Mistake                                | Symptom                             | Fix                                            |
| -------------------------------------- | ----------------------------------- | ---------------------------------------------- |
| Component rotated 180°                 | No output or wrong polarity         | Check pin 1 orientation, rotate component      |
| Primary/secondary swapped              | Extremely low output voltage        | Verify pins 1-2 are primary, 3-4 are secondary |
| Dot connected to output instead of GND | Positive output instead of negative | Swap secondary connections (pins 3 and 4)      |

## Is This Common Knowledge?

**For power supply designers**: Yes, transformer phasing is fundamental.

**For beginners**: Often confusing and overlooked!

### Where Polarity is Critical

1. **Flyback converters** (like our LM2586 circuit) - polarity determines output sign
2. **Push-pull converters** - wrong phasing causes shoot-through and damage
3. **Forward converters** - affects reset winding operation
4. **Current transformers** - reversed polarity gives wrong current direction

### Where Polarity is Less Critical

1. **Isolation transformers** - only affects which terminal is "hot" vs "neutral"
2. **Signal transformers** - only affects signal phase (180° shift)
3. **Audio transformers** - might invert audio signal (usually not critical)

**Bottom line**: In **switching power supplies**, transformer polarity is **always critical**. Never assume "transformer is just a transformer."

## Practical Example: Our LM2586 Circuit

In our USB-PD power supply project, the LM2586 flyback converter generates -15V from +15V:

```
Complete Flyback Circuit (Diagram4):

+15V IN ────┬────────────────────────────────┐
            │                                │
        ┌───┴────┐                           │
        │  C13   │  100µF bulk               │
        │  C16   │  100nF ceramic            │
        └───┬────┘                           │
            │                                │
       ┌────┴──────────┐                     │
       │7 VIN      SW 5├──┐                  │
       │               │  │                  │
       │  LM2586SX-ADJ │  │  ┌──────────┐    │
       │               │  └──┤1  •T1  4│●───┘ (Pin 4 to +15V)
       │  ON/OFF 1  ○  │     │         │
       │               │     │  47µH   │
       │  FB 3         │     │  :47µH  │
       │  ├────────────┼─────┤2      3├───┐
       │  │  COMP 2    │     └──────────┘   │
       └──┴──┬─────────┘                    │
          │  │                              │ D4 (SS34)
         R7  └─── R9 ─── C15                ▼ Cathode
        10kΩ     3kΩ    47nF                │
          │       │      │                  ├──→ -15V OUT
         R8      GND    GND                 │
        910Ω                                │
          │                               C14
         GND                              100µF
                                            │
                                           GND

Component Values:
- T1: MSD1514-473MED (47µH:47µH, 1:1 ratio)
- Primary (Pins 1-2): Connected to +15V and SW
- Secondary (Pins 3-4): Pin 4 to GND, Pin 3 to D4 cathode
- D4: Schottky diode (SS34 or MBRS340)
- Output: -15V (inverted from +15V input)
```

**Key Connection**: Secondary Pin 4 (dot) → GND, Pin 3 (no dot) → D4 cathode

This configuration ensures:

- When SW closes: Primary stores energy
- When SW opens: Secondary Pin 3 swings negative
- D4 rectifies negative pulses → -15V output

**If we reversed the transformer** (rotated 180°):

- Primary would still work (just connected to pins 2-1 instead of 1-2)
- But secondary Pin 3 (no dot) would be at GND
- And secondary Pin 4 (dot) would swing positive
- D4 would block or conduct backwards → circuit failure!

## Summary

**Transformer polarity is critical for flyback converters because:**

1. **Dots show in-phase terminals** - when primary dot is positive, secondary dot is positive
2. **Flyback uses polarity to invert voltage** - we intentionally connect secondary backwards
3. **Wrong polarity = wrong output** - reversed transformer gives wrong output polarity or no output
4. **This is fundamental power supply knowledge** - not optional, not something to guess

**Remember**: Always check the datasheet for dot notation, verify pin assignments, and never rotate a transformer component without understanding the polarity consequences!

## References

- **LM2586 Datasheet**: Figure 16 (Flyback Regulator Application, page 14)
- **Coilcraft MSD1514 Series**: [Coupled Inductors Datasheet](https://www.coilcraft.com/en-us/products/power/coupled-inductors/shielded-coupled-inductors/msd/)
- **Texas Instruments Application Note**: "Flyback Transformer Design"
- **Our Circuit**: [Diagram4 - LM2586 Flyback Converter](../inbox/circuit-diagrams#diagram4-15v---15v-voltage-inverter-lm2586-flyback-u5)
- **Component Documentation**: [LM2586SX-ADJ Component Page](../components/lm2586sx-adj)
