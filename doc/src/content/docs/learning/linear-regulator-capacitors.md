---
title: Linear Regulator Capacitor Selection
sidebar_position: 4
---

# Linear Regulator Capacitor Selection

Understanding why linear regulators need specific capacitor values and placements for stable, low-noise operation.

## Overview

Linear voltage regulators (like LM7812, LM7805, LM7912) require external capacitors for:

1. **Stability** - Prevent oscillation
2. **Noise filtering** - Remove high-frequency switching noise
3. **Transient response** - Handle sudden load changes
4. **Decoupling** - Provide local energy storage

## The Two-Capacitor Strategy

Every linear regulator needs **two types** of capacitors on both input and output:

```
Complete Circuit (LM7812 example):

Input Capacitors:                    Regulator IC:                    Output Capacitors:
+13.5V ──┬────────────────┬───────────┬──────────────────┬───────────┬────────────────┬─── +12V
         │                │           │                  │           │                │
        C20              C14          │   LM7812         │          C17              C21
       470µF            470nF         │  (TO-263-2)      │         100nF            470µF
    electrolytic       ceramic        │                  │        ceramic        electrolytic
     (farther)        (CLOSE!)     ┌──┤1 IN         OUT 3├──┐     (CLOSE!)        (farther)
         │                │         │  │                  │  │         │                │
         │                │      ┌──┤2 GND              │  │         │                │
         │                │      │  └──────────────────┘  │         │                │
         │                │      │                         │         │                │
        GND              GND    GND                       GND       GND              GND
```

**Key points:**

- **Input side**: C20 (bulk) farther, C14 (ceramic) CLOSE to pin 1
- **Output side**: C17 (ceramic) CLOSE to pin 3, C21 (bulk) farther
- **IC in the middle**: Shows physical relationship between caps and IC pins

## Why Two Different Capacitor Types?

### Ceramic Capacitors (Small: 100nF, 470nF)

**Characteristics:**

- **Low ESR** (Equivalent Series Resistance) &lt; 10mΩ
- **Low ESL** (Equivalent Series Inductance) &lt; 1nH
- **Fast response** to high-frequency noise
- **Small physical size**

**Purpose:**

- Filter **high-frequency noise** (1MHz - 100MHz+)
- Handle **fast transients** (nanosecond response)
- Provide **local decoupling** for IC

**Why close to IC:**

- Even 1cm of trace adds ~10nH inductance
- At high frequencies, inductance blocks current
- Must minimize trace length for effectiveness

### Electrolytic Capacitors (Large: 470µF)

**Characteristics:**

- **High capacitance** (1000x larger than ceramic)
- **Higher ESR** (~100mΩ typical)
- **Higher ESL** (~10nH typical)
- **Slow response** compared to ceramic

**Purpose:**

- Provide **bulk energy storage**
- Handle **low-frequency ripple** (100Hz - 10kHz)
- Manage **load transients** (millisecond response)
- Supply **inrush current** during startup

**Why farther is OK:**

- Lower frequency operation is less sensitive to inductance
- Large physical size makes close placement difficult
- Bulk storage doesn't need ultra-fast response

## Frequency Coverage

Together, the two capacitor types cover the full spectrum:

| Frequency Range      | Handled By            | Purpose                                         |
| -------------------- | --------------------- | ----------------------------------------------- |
| **DC - 10kHz**       | 470µF electrolytic    | Bulk storage, load transients, ripple filtering |
| **10kHz - 100kHz**   | Both working together | Mid-range filtering, switching noise            |
| **100kHz - 100MHz+** | 100nF/470nF ceramic   | High-frequency decoupling, IC bypass            |

## Why Different Values: Input vs Output?

### Input Ceramic: 470nF (Larger)

```
DC-DC Switching → [470nF] → Linear Regulator
  (Noisy!)       (Heavy filtering)
```

**Reasons:**

1. **Input sees switching noise** from upstream DC-DC converter (LM2596S)
2. **Switching frequency** typically 50kHz - 500kHz generates harmonics
3. **Larger cap** provides better attenuation at switching frequency
4. **Load transients** - regulator draws varying current from input
5. **Datasheet recommendation**: LM78xx typically specifies 0.33µF - 0.47µF

**Example calculation:**

```
Switching freq: 150kHz
Ripple current: 100mA
Required impedance: V_ripple / I_ripple = 10mV / 100mA = 0.1Ω

Ceramic impedance at 150kHz:
Z = 1 / (2π × 150kHz × 470nF) = 2.26Ω (too high!)

With 470nF: Provides some attenuation
Without it: Full switching noise reaches regulator → instability
```

### Output Ceramic: 100nF (Smaller)

```
Linear Regulator → [100nF] → Clean Output
  (Pre-filtered)   (Light decoupling)
```

**Reasons:**

1. **Output already filtered** by linear regulator's internal circuitry
2. **Main purpose** is local high-frequency decoupling
3. **Smaller value sufficient** for clean, regulated output
4. **Faster response** at very high frequencies (smaller = lower ESL)
5. **Datasheet recommendation**: LM78xx typically specifies 0.1µF

**Why not larger?**

- Output is already low-noise from regulator
- 100nF is optimal for HF decoupling (best impedance at 1-10MHz)
- Larger caps can reduce phase margin (potential instability)

## Physical Placement is Critical

### Ceramic Capacitor Placement (CRITICAL)

```
IC Pin ──┤<-- 2mm max -->├── Ceramic Cap

✓ Trace length: 2-5mm
✗ Trace length: >10mm (inductance kills effectiveness)
```

**PCB Layout Rules:**

1. **Place RIGHT NEXT to IC pins** (2-5mm max trace length)
2. **Short, wide traces** (minimize inductance)
3. **Direct path to GND plane** (via right next to cap)
4. **No other signals** between cap and IC pin

**Why so critical?**

```
Trace inductance: L = 1nH/mm (typical)
10mm trace = 10nH

At 10MHz:
Z_inductance = 2π × 10MHz × 10nH = 0.63Ω

This impedance blocks high-frequency current!
The ceramic cap becomes useless if placed too far.
```

### Electrolytic Capacitor Placement (Less Critical)

```
IC Pin ──┤<-- 10-50mm OK -->├── Electrolytic Cap
```

**PCB Layout Rules:**

1. **Can be placed 10-50mm from IC** (still reasonable)
2. **Normal trace width** (2-3mm copper)
3. **Connect to power plane** (not critical if traces are adequate)
4. **Keep away from heat sources** (electrolytics are temperature sensitive)

**Why less critical?**

- Operates at lower frequencies where inductance matters less
- Large physical size prevents very close placement anyway
- Bulk storage function doesn't need ultra-fast response

## Why Output Ceramic Must Be So Close: Preventing Oscillation

### The Problem: Linear Regulators Can Oscillate

**Short answer:** The regulator oscillates, so kill the vibration near! 🎯

Linear regulators contain an **internal feedback loop** that can become unstable:

```
Internal Feedback Loop:
Output voltage → Error amp → Pass transistor → Output
                    ↑                            │
                    └────── Feedback ────────────┘

If phase shift occurs in this loop:
→ Positive feedback at certain frequencies
→ Oscillation! (typically 100kHz - 10MHz)
```

**Without proper output capacitor:**

```
Output voltage waveform:
     ╱╲╱╲╱╲╱╲╱╲╱╲╱╲
    ╱            ╲╱   (Oscillating at MHz frequency!)
   ╲╱
```

**With ceramic cap VERY CLOSE:**

```
Output voltage waveform:
    ────────────────   (Stable! ✅)
```

### Why "CLOSE" is Critical: The Physics

**Trace inductance blocks high-frequency current:**

```
If ceramic cap is FAR (>5cm):

IC Output ──┬── 5cm trace (~50nH inductance) ── Ceramic cap ── GND
            │          ↑
         Oscillation   Inductance blocks MHz currents! ❌
         (1-10MHz)     Cap can't "see" the oscillation
            │          Vibration stays at IC output!
            └──→ ╱╲╱╲╱╲╱╲╱╲  (Unstable!)
```

**At MHz frequencies, even short traces act like inductors:**

| Trace Length | Inductance | Impedance at 1MHz | Impedance at 10MHz |
| ------------ | ---------- | ----------------- | ------------------ |
| 1mm          | ~1nH       | 0.006Ω            | 0.06Ω              |
| 1cm          | ~10nH      | 0.06Ω             | 0.6Ω               |
| 5cm          | ~50nH      | 0.3Ω              | **3Ω** ❌          |

**At 10MHz with 5cm trace:** 3Ω impedance blocks oscillation current from reaching the capacitor!

**If ceramic cap is VERY CLOSE (&lt;2mm):**

```
IC Output ──┬── 2mm trace (~2nH) ── Ceramic cap ── GND
            │       ↑
         Oscillation  Minimal inductance! ✅
         (1-10MHz)    Cap immediately shorts vibration to ground
            │
            └──→ ──────────  (Stable! No oscillation)
```

**Why it works:**

1. Oscillation current has **very low impedance path** to ground
2. High-frequency vibrations are **immediately damped**
3. Feedback loop remains **stable**
4. Output stays **clean and steady**

### Visual Analogy: Shock Absorber

Think of the output ceramic capacitor like a **car shock absorber:**

```
🚗 Bouncing Spring (Oscillation):
    ╱╲     Spring bouncing up/down
   ╱  ╲    (Like regulator oscillating)
  ╱    ╲
 ╱      ╲

🔧 Shock Absorber (Ceramic Cap):
   Must be attached DIRECTLY to spring!

✅ Shock absorber attached directly:
   Spring ── [shock absorber] ── chassis
           (dampens vibration immediately)

❌ Shock absorber via long flexible cable:
   Spring ── [5m rubber hose] ── [shock absorber] ── chassis
           (too slow, spring keeps bouncing!)
```

**Same principle for capacitors:**

- **Regulator = Spring** (can oscillate)
- **Ceramic cap = Shock absorber** (dampens oscillation)
- **Trace inductance = Flexible cable** (blocks effectiveness)
- **Solution: Attach directly!** (minimize trace length)

### The Numbers: Why &lt;2mm Matters

**PCB trace inductance rule of thumb:** ~1nH per millimeter

```
Best practice trace lengths:

✅ Excellent: <2mm trace
   - Inductance: ~2nH
   - Impedance at 10MHz: 0.12Ω
   - Result: Cap effectively shorts oscillation ✅

✅ Good: 2-5mm trace
   - Inductance: ~5nH
   - Impedance at 10MHz: 0.3Ω
   - Result: Cap still effective, minor degradation

⚠️ Acceptable: 5-10mm trace
   - Inductance: ~10nH
   - Impedance at 10MHz: 0.6Ω
   - Result: Reduced effectiveness, may work

❌ Poor: >10mm trace
   - Inductance: >10nH
   - Impedance at 10MHz: >0.6Ω
   - Result: Oscillation likely! ❌
```

### Input vs Output: Different Priorities

**Why is output ceramic placement MORE critical than input?**

| Side       | What Happens If Cap Is Far  | Consequence                          |
| ---------- | --------------------------- | ------------------------------------ |
| **Input**  | More noise reaches IC       | Regulator filters it (PSRR helps) ✅ |
| **Output** | Oscillation can't be damped | **Regulator oscillates!** ❌         |

**Input capacitor far:**

```
Switching noise → [far cap can't filter well] → Regulator IC
                                                    ↓
                                    PSRR (Power Supply Rejection)
                                    filters most of it ✅
                                                    ↓
                                            Output (mostly OK)
```

**Output capacitor far:**

```
Regulator IC → Oscillation starts → [far cap can't damp] → Output
     ↑                                                          │
     └────────── Positive feedback ─────────────────────────────┘
                 (Oscillation continues! ❌)
```

**Key insight:**

- Input: Regulator helps compensate for poor cap placement
- Output: **Nothing can save you** if cap is too far! ⚠️

### PCB Layout Checklist for Stability

**Critical rules for output ceramic capacitor:**

- [ ] **Distance:** &lt;2mm from IC output pin (ideal)
- [ ] **Trace width:** As wide as possible (reduces inductance)
- [ ] **Via to ground:** Place GND via **right next to** capacitor
- [ ] **No obstacles:** Direct, straight path from IC pin to cap
- [ ] **Keep away from:** High-speed signals, switching nodes

**Example of GOOD layout:**

```
        IC Output Pin
             │
             │ <── 1-2mm trace, 2mm wide
             ↓
          [Ceramic]
             │
           [Via] <── Ground via right next to cap
             │
        ════╧════  (Ground plane)
```

**Example of BAD layout:**

```
        IC Output Pin
             │
             ├── routes around other components
             │
        <5cm total trace length>
             │
             ↓
          [Ceramic] <── TOO FAR! ❌
             │
           [Via]
```

### Real-World Impact

**What you'll see with improper placement:**

```
Oscilloscope measurement (no load):

Bad placement (ceramic 3cm away):
  ┌─────────────────────────────┐
  │  ╱╲╱╲╱╲╱╲╱╲╱╲╱╲╱╲╱╲╱╲╱╲╱╲  │ ← 500mV oscillation!
  │╱  Expected 12.00V       ╲│ ← Unstable
  │                           ╲│
  └─────────────────────────────┘

Good placement (ceramic <2mm away):
  ┌─────────────────────────────┐
  │─────────────────────────────│ ← Flat 12.00V
  │     Stable output ✅         │ ← <1mV noise
  │                             │
  └─────────────────────────────┘
```

**Summary:** The regulator oscillates at MHz frequencies. To kill this vibration, the ceramic capacitor must be **physically close** (&lt;2mm) so trace inductance doesn't block the damping current. Think "shock absorber attached directly to spring" - distance kills effectiveness! 🎯

## Common Mistakes and Fixes

### ❌ Mistake 1: Swapping Ceramic Values

```
Input: 100nF (too small for switching noise)
Output: 470nF (unnecessary, wastes space)
```

**Result:** Input switching noise gets through → regulator instability

**Fix:** Follow datasheet: Input 470nF, Output 100nF

### ❌ Mistake 2: Ceramic Too Far from IC

```
IC Pin ────── [20mm trace] ────── Ceramic Cap
```

**Result:** Trace inductance blocks high-frequency current → cap is useless

**Fix:** Place ceramic RIGHT NEXT to pin (2-5mm max)

### ❌ Mistake 3: Only Using Electrolytic Caps

```
Input: Only 470µF electrolytic
Output: Only 470µF electrolytic
```

**Result:** No high-frequency filtering → oscillation, instability

**Fix:** Always pair electrolytic with ceramic

### ❌ Mistake 4: Using Low-Quality Ceramics

```
Using Y5V dielectric ceramic (capacitance varies wildly)
```

**Result:** Capacitance drops 80% at rated voltage and temperature

**Fix:** Use X7R or X5R dielectric (stable across temperature/voltage)

### ❌ Mistake 5: Wrong Electrolytic Polarity (Negative Rails)

```
-12V rail: Negative terminal to GND (WRONG!)
```

**Result:** Electrolytic explodes or fails

**Fix:** Negative rail → Negative terminal to -12V, Positive terminal to GND

## Practical Examples from This Project

### Positive Rails (+12V, +5V)

**LM7812 (TO-263-2):**

```
Input:
- C14: 470nF ceramic X7R (RIGHT NEXT to pin 1)
- C20: 470µF electrolytic (10-20mm from pin 1)

Output:
- C17: 100nF ceramic X7R (RIGHT NEXT to pin 3)
- C21: 470µF electrolytic (10-20mm from pin 3)
```

**Why this works:**

- DC-DC converter upstream generates 150kHz switching noise
- C14 (470nF) filters this switching noise at input
- C20 (470µF) provides bulk storage for load transients
- C17 (100nF) decouples high-frequency noise at output
- C21 (470µF) provides output bulk capacitance

### Negative Rail (-12V)

**LM7912 (TO-252-3):**

```
Input:
- C16: 470nF ceramic (CLOSE to pin 1)
- C24: 470µF electrolytic (farther) ※ Negative to -13.5V, Positive to GND

Output:
- C19: 100nF ceramic (CLOSE to pin 2)
- C25: 470µF electrolytic (farther) ※ Negative to -12V, Positive to GND
```

**Critical polarity note:**

- For negative voltage rails, electrolytic polarity is REVERSED
- Negative terminal connects to negative voltage (e.g., -12V)
- Positive terminal connects to GND (0V)

## Advanced: ESR and Stability

### Why ESR Matters

Linear regulators need some ESR (Equivalent Series Resistance) in the output capacitor for stability:

```
Too low ESR → Phase shift → Oscillation
Optimal ESR → Stable operation
Too high ESR → Poor transient response
```

**Typical requirements (from datasheets):**

- LM78xx: Output cap ESR should be 0.1Ω - 10Ω
- Pure ceramic (ESR &lt; 10mΩ) can cause instability
- Electrolytic + ceramic combination provides optimal ESR

**Our design:**

- C21/C23/C25 (electrolytic 470µF): ESR ~100mΩ (provides damping)
- C17/C18/C19 (ceramic 100nF): ESR &lt; 10mΩ (provides HF decoupling)
- **Together:** Optimal combination for stability and performance

### Load Transient Response

When load current changes suddenly:

```
Load step: 0A → 1A in 1µs

Without capacitors:
- Output dips 2V (regulator can't respond fast enough)
- Takes 100µs to recover

With proper capacitors:
- Ceramic provides instant current (sub-µs response)
- Electrolytic provides sustained current (µs-ms response)
- Output dips only 50mV
- Recovers in 10µs
```

## Testing and Validation

### What to Check on PCB

1. **Ceramic placement:** Measure distance from cap to IC pin
- ✓ Goal: &lt; 5mm
- ✗ Problem: &gt; 10mm

2. **Output ripple:** Measure with oscilloscope (20MHz bandwidth)
- ✓ Goal: &lt; 1mVp-p at full load
- ✗ Problem: &gt; 10mVp-p (missing/far ceramic caps)

3. **Load transient:** Step load from 0% to 100%
- ✓ Goal: &lt; 100mV deviation, &lt; 50µs recovery
- ✗ Problem: &gt; 500mV deviation (missing bulk caps)

4. **Oscillation check:** Probe output with 100MHz scope, no load
- ✓ Goal: Clean DC, no oscillation
- ✗ Problem: MHz oscillation (ceramic too far or missing)

## Summary: Quick Reference

| Parameter                  | Input Side             | Output Side            | Reason                                     |
| -------------------------- | ---------------------- | ---------------------- | ------------------------------------------ |
| **Ceramic value**          | 470nF                  | 100nF                  | Input needs more switching noise filtering |
| **Ceramic type**           | X7R/X5R                | X7R/X5R                | Stable across temperature                  |
| **Ceramic placement**      | RIGHT NEXT to pin      | RIGHT NEXT to pin      | Minimize trace inductance                  |
| **Electrolytic value**     | 470µF                  | 470µF                  | Bulk storage and load transients           |
| **Electrolytic placement** | 10-50mm from pin OK    | 10-50mm from pin OK    | Less critical for low frequencies          |
| **Electrolytic polarity**  | + to voltage, - to GND | + to voltage, - to GND | (Reversed for negative rails!)             |

## Key Takeaways

1. **Always use BOTH ceramic and electrolytic** - they work together across different frequencies
2. **Ceramic placement is CRITICAL** - must be right next to IC pins (&lt; 5mm)
3. **Different values for input/output** - input handles more noise (470nF), output is cleaner (100nF)
4. **Electrolytic provides bulk storage** - placement less critical (10-50mm OK)
5. **Negative rail polarity** - don't forget to reverse electrolytic polarity!
6. **Use quality parts** - X7R/X5R ceramics, low-ESR electrolytics
7. **PCB layout matters** - short, wide traces for ceramics, good ground plane

## Further Reading

- **LM7812 Datasheet**: Section "Application Information" for recommended capacitor values
- **LM7805 Datasheet**: See "Output Capacitor" section for stability requirements
- **LM7912 Datasheet**: Note reversed polarity requirements for negative regulators
- **Decoupling Capacitor Guide**: Understanding ESR, ESL, and frequency response
- **PCB Layout Guide**: High-frequency design techniques for power supplies

## Related Learning Articles

- [Buck Converter Feedback Networks](./buck-converter-feedback.md) - Understanding voltage divider design
- [Open-Drain PG Pin Operation](./open-drain-pg-pin.md) - Power-good signal implementation
