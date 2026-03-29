---
title: "ESD Protection: How TVS Diodes Save Your Circuit"
sidebar_position: 8
---

# ESD Protection: How TVS Diodes Save Your Circuit

Understanding how TVS diodes protect sensitive IC pins from static electricity and voltage spikes.

## The Question

When looking at the USB-PD input circuit, there's a small component (D4) connected to the CC lines:

> "What is D4 for? Why do the CC lines need special protection?"

**Short answer**: D4 is an ESD protection device that acts like a pressure relief valve - it dumps dangerous voltage spikes to ground before they can destroy the STUSB4500.

## What is ESD?

**ESD** = **E**lectro**S**tatic **D**ischarge

It's the sudden flow of electricity when two objects with different charges come into contact.

### Real-world examples

| Action                           | Voltage generated |
| -------------------------------- | ----------------- |
| Walking on carpet                | 1,500 - 35,000V   |
| Sliding across car seat          | 7,000 - 25,000V   |
| Picking up plastic bag from desk | 1,000 - 20,000V   |
| Normal indoor movement           | 500 - 5,000V      |

**You can't feel ESD below ~3,000V**, but even 100V can damage sensitive electronics!

### The danger to electronics

```
Human body static: 10,000V typical

IC maximum voltage rating: 5-25V typical

Ratio: 400x more than the IC can handle! 💀
```

## Why CC Lines Are Vulnerable

The USB-C connector has several types of pins:

```
USB-C Connector (simplified)
┌─────────────────────────────────────┐
│                                     │
│  VBUS ─── Power (has big capacitors to absorb energy)
│                                     │
│  CC1  ─── Signal (thin trace, directly to IC) ⚠️ VULNERABLE
│  CC2  ─── Signal (thin trace, directly to IC) ⚠️ VULNERABLE
│                                     │
│  GND  ─── Ground (already at 0V, safe)
│                                     │
│  D+/D- ── Data (usually have protection)
│                                     │
└─────────────────────────────────────┘
```

**CC lines are the first point of contact** when you plug in a cable, and they connect directly to sensitive IC pins with no bulk capacitors to absorb energy.

## What is a TVS Diode?

**TVS** = **T**ransient **V**oltage **S**uppressor

It's a special diode designed to clamp voltage spikes by conducting large currents to ground.

### Normal diode vs TVS diode

| Type          | Purpose        | Response time   | Current handling     |
| ------------- | -------------- | --------------- | -------------------- |
| Normal diode  | Rectification  | Moderate        | Low-medium           |
| **TVS diode** | **Protection** | **Nanoseconds** | **Very high (amps)** |

### How TVS works

```
Voltage
   ▲
   │
40V│─ ─ ─ ─ ─ ─ ─ ─ ─┬─────────── Clamping voltage (TVS conducts heavily)
   │                 /
   │                /
27V│─ ─ ─ ─ ─ ─ ─ /─ ─ ─ ─ ─ ─ ─ Breakdown voltage (TVS starts conducting)
   │             /│
   │            / │
   │           /  │
25V│─ ─ ─ ─ ─/─ ─│─ ─ ─ ─ ─ ─ ─ Working voltage (TVS is invisible)
   │        ╱    │
   │       ╱     │
   │      ╱      │
 0V└─────────────┴──────────────▶ Current
         Normal   Spike!
       operation  (ESD event)
```

**Three regions:**

1. **Below 25V (working)**: TVS has very high impedance - signal passes through normally
2. **25-27V (breakdown)**: TVS starts conducting, limiting voltage rise
3. **Above 27V (clamping)**: TVS conducts heavily, dumping current to GND

## CC Line ESD Protection

:::info Current Design Uses USBLC6-2SC6
The v1.1 design uses **[USBLC6-2SC6](../components/usblc6-2sc6)** (D4) instead of ESDA25L for CC line protection. USBLC6-2SC6 provides:

- Lower clamping voltage (~17V vs ~44V)
- Additional VBUS protection channel
- Better suited for USB-C applications

The principles below still apply - only the specific component has changed.
:::

### Circuit connection (USBLC6-2SC6)

```
USB-C Connector        D4 (USBLC6-2SC6)        STUSB4500
      │               ┌──────────────┐              │
 CC1 ─┼───────────────┤ 1 (I/O1)     │              │
      │               │         6    ├──────────────┤ CC1 (pin 2)
      │               │              │              │
      │               │ 2 (GND)──GND │              │
      │               │              │              │
 CC2 ─┼───────────────┤ 3 (I/O2)     │              │
      │               │         4    ├──────────────┤ CC2 (pin 4)
      │               │              │              │
VBUS ─┼───────────────┤ 5 (VBUS)     │              │
      │               └──────────────┘              │
```

### Internal structure

The USBLC6-2SC6 is a **dual TVS array** with VBUS protection:

```
     I/O1 (1)              I/O1 (6)
        │                      │
        └────┬────────────┬────┘
             │   VBUS(5)  │
             │     │      │
        ┌────┴─────┼──────┴────┐
        │    ─┬─   │     ─┬─   │
        │   ╲│╱    │    ╲│╱    │
        │    │     │     │     │
        ├────┴─────┼─────┴─────┤
        │          │           │
        └────┬─────┼──────┬────┘
             │     │      │
     I/O2 (3)│    GND(2)  │I/O2 (4)
             │            │

Each channel clamps to GND and VBUS independently
```

### Key specifications (USBLC6-2SC6)

| Parameter             | Value       | Why it matters                          |
| --------------------- | ----------- | --------------------------------------- |
| **Working voltage**   | 5.25V       | Optimized for USB signal levels         |
| **Breakdown voltage** | 6V          | Starts protecting above this            |
| **Clamping voltage**  | 17V @ 1A    | Much lower than ESDA25L (44V)           |
| **Capacitance**       | 3.5pF       | Low enough to not affect CC signaling   |
| **ESD rating**        | 15kV (HBM)  | Survives typical human static discharge |
| **VBUS channel**      | Yes (Pin 5) | Additional protection for power rail    |

## ESD Event Timeline

What happens when you touch the USB-C cable with static charge:

```
Time 0ns:
├─ Your finger approaches USB-C plug
├─ Static charge: 10,000V
├─ CC line voltage: 0V
└─ D4 state: High impedance (invisible)

Time 1ns:
├─ Spark jumps from finger to CC pin
├─ CC line voltage shoots up rapidly
├─ Heading toward 10,000V!
└─ D4 state: Still high impedance

Time 2ns:
├─ CC line reaches 27V (breakdown voltage)
├─ D4 starts conducting
├─ Current diverts to GND
└─ Voltage rise slows dramatically

Time 5ns:
├─ CC line clamped at ~40V
├─ D4 conducting heavily (amps of current)
├─ All excess energy dumped to GND
└─ STUSB4500 sees only 40V spike (survivable!)

Time 100ns:
├─ ESD event over
├─ CC line returns to normal
├─ D4 returns to high impedance
└─ Circuit continues working normally ✓
```

**Without D4**: CC line would reach thousands of volts → STUSB4500 destroyed

**With D4**: CC line clamped to ~17V → STUSB4500 well protected

## Why 25V Working Voltage?

USB-PD CC lines can see various voltages:

| Condition        | CC voltage | Notes                   |
| ---------------- | ---------- | ----------------------- |
| Normal signaling | 0 - 3.3V   | Typical operation       |
| VCONN power      | 5V         | Powering active cables  |
| Fault condition  | Up to 22V  | USB-PD spec allows this |

The 25V working voltage ensures:

- D4 **doesn't interfere** with normal CC operation (0-22V)
- D4 **does protect** against overvoltage (&gt;27V)

## Why Low Capacitance Matters

CC lines carry **communication signals** for USB-PD negotiation:

```
CC Signal (simplified)
     ┌───┐   ┌───┐   ┌───┐
     │   │   │   │   │   │
─────┘   └───┘   └───┘   └─── Clean signal

With HIGH capacitance TVS:
     ╱───╲   ╱───╲   ╱───╲
    ╱     ╲ ╱     ╲ ╱     ╲
───╱       ╳       ╳       ╲── Rounded, distorted signal ❌

With LOW capacitance TVS (3pF):
     ┌───┐   ┌───┐   ┌───┐
     │   │   │   │   │   │
─────┘   └───┘   └───┘   └─── Clean signal ✓
```

USB-PD specification allows up to **200pF** on CC lines, so 3pF is negligible.

## Placement Matters

TVS diodes must be placed **as close as possible** to the connector:

```
GOOD placement:
USB-C ──┬── TVS ──────────────── STUSB4500
        │                            │
       GND                          GND

ESD enters here, immediately clamped ✓

BAD placement:
USB-C ──────────────── TVS ──┬── STUSB4500
                             │       │
                            GND     GND

ESD travels long trace before clamping ❌
(trace inductance can cause voltage overshoot)
```

## Other TVS Diodes in the Circuit

Our circuit has multiple TVS diodes for different protection needs:

| Component | Type        | Protects         | Working Voltage |
| --------- | ----------- | ---------------- | --------------- |
| **D4**    | USBLC6-2SC6 | CC1, CC2, VBUS   | 5.25V           |
| **TVS1**  | SMAJ15A     | VBUS power rail  | 15V             |
| **TVS2**  | SD05        | +5V output rail  | 5V              |
| **TVS3**  | SMAJ15A     | +12V output rail | 15V             |

Each TVS is matched to the voltage of the line it protects.

## Key Takeaways

1. **ESD is invisible but deadly** - you can't feel it below 3,000V, but 100V can kill an IC
2. **TVS diodes are voltage-activated switches** - invisible during normal operation, conduct during spikes
3. **Response time is critical** - TVS diodes respond in nanoseconds to catch fast ESD events
4. **CC lines are vulnerable** - first point of contact, thin traces, directly connected to IC
5. **Working voltage must exceed normal operation** - 25V TVS for CC lines that can see up to 22V
6. **Low capacitance preserves signal quality** - 3pF doesn't affect CC communication
7. **Placement near the connector** - clamp the spike before it travels into the circuit

## Common Mistakes to Avoid

❌ **Wrong**: "TVS diodes are like fuses - they blow and need replacement"

- TVS diodes are **not sacrificial** - they survive ESD events and keep working
- They can handle thousands of ESD strikes

✅ **Correct**: "TVS diodes clamp voltage repeatedly without damage"

---

❌ **Wrong**: "Any diode can protect against ESD"

- Regular diodes are too slow and can't handle the current
- TVS diodes are specifically designed for fast, high-current events

✅ **Correct**: "TVS diodes have nanosecond response and high peak current ratings"

---

❌ **Wrong**: "Higher voltage TVS = better protection"

- If working voltage is too high, the TVS won't activate in time
- Match the TVS working voltage to slightly above the normal line voltage

✅ **Correct**: "Choose TVS working voltage just above the maximum normal operating voltage"

## See Also

- [USBLC6-2SC6 Documentation](../components/usblc6-2sc6) - Full component specifications
- [ESDA25L Documentation](../components/esda25l) - Legacy component (replaced by USBLC6-2SC6)
- [SMAJ15A Documentation](../components/smaj15a) - VBUS protection TVS
- [SD05 Documentation](../components/sd05) - 5V rail protection TVS
- [USB Type-C Pinout](./usb-type-c-pinout) - Understanding CC and other pins
