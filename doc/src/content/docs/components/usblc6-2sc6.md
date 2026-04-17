---
title: USBLC6-2SC6 - USB ESD Protection (D4)
sidebar_position: 5
---

# USBLC6-2SC6 - USB ESD Protection (D4)

TVS diode array for USB Type-C CC line and VBUS ESD protection. Replaces ESDA25L in v1.1 design.

- [View on JLCPCB: C7519](https://jlcpcb.com/partdetail/C7519)
- [Download Datasheet (PDF)](https://www.st.com/resource/en/datasheet/usblc6-2.pdf)

## Overview

The USBLC6-2SC6 is a 6-pin TVS diode array specifically designed for USB ESD protection. It provides 2 bidirectional channels for data/CC lines plus a VBUS protection channel, making it ideal for USB Type-C applications.

:::tip Why USBLC6-2SC6 over ESDA25L?
| Feature | ESDA25L | USBLC6-2SC6 |
|---------|---------|-------------|
| Clamping Voltage | ~44V | **~17V** |
| VBUS Protection | No | **Yes (Pin 5)** |
| Working Voltage | 25V | 5.25V |
| Capacitance | 3pF | 3.5pF |
| Design Target | High-voltage lines | **USB signals** |

USBLC6-2SC6 has lower clamping voltage, providing better protection for CC lines operating at ~1.7V.
:::

## Key Specifications

| Parameter                    | Value       | Notes                    |
| ---------------------------- | ----------- | ------------------------ |
| **JLCPCB Part Number**       | C7519       |                          |
| **Manufacturer Part Number** | USBLC6-2SC6 | STMicroelectronics       |
| **Package**                  | SOT-23-6    | 6-pin surface-mount      |
| **Stock Availability**       | 354,000+    | Excellent availability   |
| **Unit Price**               | ~$0.13      |                          |
| **Working Voltage**          | 5.25V       | USB specification        |
| **Breakdown Voltage**        | 6V min      |                          |
| **Clamping Voltage**         | 17V @ 1A    | Much lower than ESDA25L  |
| **Peak Pulse Current**       | 3A          | 8/20µs waveform          |
| **Capacitance**              | 3.5pF typ   | Low impact on CC signals |
| **ESD Rating**               | 15kV (HBM)  | IEC 61000-4-2            |
| **Channels**                 | 2 + VBUS    | I/O1, I/O2, and VBUS     |

## Pin Configuration

```
          USBLC6-2SC6 (SOT-23-6)
                Top View

        ┌─────────────────────┐
        │                     │
 I/O1 ──┤ 1               6 ├── I/O1
        │     ┌───────┐       │
  GND ──┤ 2   │       │   5 ├── VBUS
        │     └───────┘       │
 I/O2 ──┤ 3               4 ├── I/O2
        │                     │
        └─────────────────────┘

Pin 1: I/O1 input  (CC1 from USB-C)
Pin 2: GND
Pin 3: I/O2 input  (CC2 from USB-C)
Pin 4: I/O2 output (CC2 to STUSB4500)
Pin 5: VBUS        (optional VBUS protection)
Pin 6: I/O1 output (CC1 to STUSB4500)
```

### Internal Structure

```
                    VBUS (Pin 5)
                        │
            ┌───────────┼───────────┐
            │           │           │
I/O1 ───────┼─────┬─────┼─────┬─────┼─────── I/O1
(Pin 1)     │    ─┴─    │    ─┴─    │       (Pin 6)
            │   ╲│╱     │   ╲│╱     │
            │    │      │    │      │
            ├────┴──────┼────┴──────┤
            │           │           │
I/O2 ───────┼─────┬─────┼─────┬─────┼─────── I/O2
(Pin 3)     │    ─┴─    │    ─┴─    │       (Pin 4)
            │   ╲│╱     │   ╲│╱     │
            │    │      │    │      │
            └────┴──────┴────┴──────┘
                        │
                       GND (Pin 2)
```

## Application in STUSB4500 Circuit (D4)

```
USB-C (J1)           D4 (USBLC6-2SC6)          STUSB4500 (U1)
┌─────────┐         ┌─────────────────┐        ┌─────────────┐
│         │         │                 │        │             │
│ CC1 (A5)├────────→│ 1 (I/O1)   (I/O1) 6 │───→│ CC1 (pin 2) │
│         │         │                 │     └─→│ CC1DB (pin 1)│
│         │         │ 2 (GND)         │        │             │
│ CC2 (B5)├────────→│ 3 (I/O2)   (I/O2) 4 │───→│ CC2 (pin 4) │
│         │         │                 │     └─→│ CC2DB (pin 5)│
│         │         │ 5 (VBUS)        │        │             │
│ VBUS    ├─────────┼─────────────────┤        │             │
│         │         │                 │        │             │
└─────────┘         └─────────────────┘        └─────────────┘
                            │
                           GND
```

### Connection List

| D4 Pin | Name          | Connected To                          |
| ------ | ------------- | ------------------------------------- |
| 1      | I/O1 (input)  | USB-C CC1 (J1 pin A5)                 |
| 2      | GND           | System ground                         |
| 3      | I/O2 (input)  | USB-C CC2 (J1 pin B5)                 |
| 4      | I/O2 (output) | STUSB4500 CC2 (pin 4) + CC2DB (pin 5) |
| 5      | VBUS          | VBUS_IN                               |
| 6      | I/O1 (output) | STUSB4500 CC1 (pin 2) + CC1DB (pin 1) |

## Why This Protection Matters

| Threat          | Source                  | USBLC6-2SC6 Protection            |
| --------------- | ----------------------- | --------------------------------- |
| ESD             | Cable insertion/removal | 15kV HBM rating                   |
| CC overvoltage  | Faulty cable/adapter    | 17V clamping (vs 44V for ESDA25L) |
| VBUS transients | Hot-plug events         | Pin 5 VBUS clamping               |
| Transients      | Hot-plug events         | Fast response time                |

The lower clamping voltage (17V vs 44V) provides much better protection for the STUSB4500's CC pins.

## How It Works: Avalanche Breakdown

TVS diodes protect circuits using a phenomenon called **avalanche breakdown**. Here's how it works:

### Normal Operation (V &lt; 5.25V)

```
I/O1 (CC1) ────●──────────────────●──── I/O1
               │                  │
               ▼ (reverse bias)   ▼ (reverse bias)
               │                  │
GND ───────────┴────────●─────────┴──── VBUS
                        │
               (all diodes OFF - high impedance)
```

- All TVS diodes are **reverse biased** → no current flows
- Signal passes through unaffected
- Only ~3.5pF capacitance added to the line

### ESD Event (High Voltage Spike)

When an ESD spike arrives (e.g., +8kV from human touch):

```
                  ⚡ Incoming electron (accelerated by ESD voltage)
                     ↓
                     ●→→→→ accelerates in electric field
                         ↓
                         💥 COLLISION with silicon atom!
                        ╱ ╲
                       ●   ●  ← 2 electrons now!
                      ↓     ↓
                     💥     💥
                    ╱ ╲   ╱ ╲
                   ●   ● ●   ●  ← 4 electrons!
                   ↓   ↓ ↓   ↓
                  ... CHAIN REACTION ...
```

This is **impact ionization**:

1. High voltage creates strong electric field in the diode's depletion region
2. Stray electrons accelerate to **high kinetic energy**
3. Electrons **collide** with silicon crystal lattice
4. Each collision **knocks loose** more electrons (creates electron-hole pairs)
5. **Exponential multiplication** = massive current flows through the TVS

### Why Voltage Stays Constant (Clamping)

```
        Current
           ↑
           │                    ╱
           │                   ╱
           │                  ╱  ← Massive current increase
           │                 ╱     with tiny voltage change
           │                │
           │                │ Breakdown!
           │                │ (V_BR ≈ 6V)
           │________________│___________→ Voltage
           0                6V
```

The avalanche multiplication is **extremely sensitive** to electric field:

- Small voltage increase → field increases slightly → **exponentially more** ionization
- Current increases 1000x while voltage increases only ~1V
- Result: Voltage is effectively "clamped" at breakdown voltage

**Analogy:** Like a **pressure relief valve** - below threshold the valve is closed, at threshold it opens and pressure stays constant no matter how much more you push.

### Energy Absorption

Where does the ESD energy go?

```
ESD spike energy → Electron kinetic energy → Lattice vibrations → HEAT
     (8kV)              (accelerated)           (phonons)        (absorbed)
```

The TVS diode:

1. **Clamps voltage** at ~17V (limits how high it can go)
2. **Conducts the current** through itself → to GND
3. **Converts energy to heat** in its own silicon body (P = V × I = 17V × 3A = 51W briefly)

The protected IC (STUSB4500) never sees the dangerous voltage - the TVS diode **"takes the hit"** and dissipates it as heat instead.

### Bidirectional Protection

The USBLC6-2SC6 has back-to-back diodes for each channel:

| ESD Polarity          | Diode Behavior      | Clamping Voltage |
| --------------------- | ------------------- | ---------------- |
| Positive spike (+8kV) | Avalanche breakdown | ~17V             |
| Negative spike (-8kV) | Forward conduction  | ~-0.7V           |

This provides full protection regardless of ESD polarity.

## Design Considerations

### Placement

- Place D4 between USB-C connector and STUSB4500
- Short traces from pin 2 to GND for effective clamping
- Signal flow: USB-C → D4 → STUSB4500

### VBUS Connection (Pin 5)

Pin 5 can be:

- **Connected to VBUS_IN** (recommended) - provides additional transient protection on the power rail
- **Left unconnected** - CC protection still works, but no VBUS clamping

### Capacitance Impact

- 3.5pF typical capacitance is acceptable for CC communication
- USB PD CC signaling tolerates up to 200pF
- Slightly higher than ESDA25L (3pF) but negligible difference

## Alternative Parts

| Part              | LCSC     | Package  | Clamping V | Capacitance | Notes                         |
| ----------------- | -------- | -------- | ---------- | ----------- | ----------------------------- |
| USBLC6-2SC6       | C7519    | SOT-23-6 | 17V        | 3.5pF       | **Recommended (ST original)** |
| USBLC6-2SC6 (UMW) | C2687116 | SOT-23-6 | 15V        | 0.8pF       | Budget alternative            |
| PRTR5V0U2X        | C12333   | SOT-143  | 17V        | 1pF         | Nexperia, different footprint |

## References

- [USBLC6-2SC6 Datasheet (ST)](https://www.st.com/resource/en/datasheet/usblc6-2.pdf)
- [JLCPCB Part Page](https://jlcpcb.com/partdetail/C7519)
- [USB Type-C ESD Protection App Note](https://www.st.com/resource/en/application_note/an4641-design-guidelines-for-using-st-esd-protection-device-for-usb-typec-interface-stmicroelectronics.pdf)
