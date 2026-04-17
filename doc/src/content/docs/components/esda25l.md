---
title: ESDA25L - TVS Diode (Legacy)
sidebar_position: 4
---

# ESDA25L - TVS Diode (Legacy)

:::caution Not Used in Current Design
ESDA25L has been **replaced by [USBLC6-2SC6](./usblc6-2sc6.md)** in v1.1 design.

**Reason**: ESDA25L's clamping voltage (~44V) is too high for CC line protection. USBLC6-2SC6 clamps at ~17V and includes VBUS protection.
:::

TVS diode for high-voltage ESD and overvoltage protection.

- [View on JLCPCB: C343997](https://jlcpcb.com/partdetail/C343997)

## Overview

The ESDA25L is a TVS (Transient Voltage Suppressor) diode designed for ESD protection on USB Type-C CC (Configuration Channel) lines. It protects the STUSB4500 CC pins from electrostatic discharge and voltage transients.

## Key Specifications

| Parameter                    | Value      | Notes                    |
| ---------------------------- | ---------- | ------------------------ |
| **JLCPCB Part Number**       | C343997    |                          |
| **Manufacturer Part Number** | ESDA25L    | STMicroelectronics       |
| **Package**                  | SOT-23     | 3-pin surface-mount      |
| **Stock Availability**       | 4,584      | Good availability        |
| **Unit Price**               | ~$0.15     |                          |
| **Working Voltage**          | 25V        | CC lines up to 22V       |
| **Breakdown Voltage**        | 27.6V min  |                          |
| **Clamping Voltage**         | 40V @ 1A   |                          |
| **Peak Pulse Current**       | 3A         | 8/20µs waveform          |
| **Capacitance**              | 3pF typ    | Low impact on CC signals |
| **ESD Rating**               | 15kV (HBM) | IEC 61000-4-2            |

## Pin Configuration

```
    ESDA25L (SOT-23)
       Top View

    ┌───────────────┐
    │   ┌─────┐     │
    │   │     │     │
 K1 │1  │     │  3│ K2
    │   │     │     │
    │   └─────┘     │
    │       2       │
    └───────┬───────┘
            A (Common Anode)

Pin 1: Cathode 1 (K1) - CC1
Pin 2: Anode (A) - GND
Pin 3: Cathode 2 (K2) - CC2

Internal Structure:
CC1 ───┤◄├───┬───┤►├─── CC2
              │
             GND
```

## Application in STUSB4500 Circuit

```
USB-C Connector              STUSB4500
┌──────────────┐            ┌──────────────┐
│              │            │              │
│  CC1  ───────┼────────┬───┤ CC1 (pin 2)  │
│              │        │   │              │
│  CC2  ───────┼────┬───┼───┤ CC2 (pin 3)  │
│              │    │   │   │              │
└──────────────┘    │   │   └──────────────┘
                    │   │
                    │   │   ESDA25L
                    │   │   ┌────────┐
                    │   └───┤ K1 (1) │
                    │       │        │
                    │       │ A  (2) ├─── GND
                    │       │        │
                    └───────┤ K2 (3) │
                            └────────┘
```

## Why CC Protection is Important

| Threat        | Source                  | Protection          |
| ------------- | ----------------------- | ------------------- |
| ESD           | Cable insertion/removal | 15kV HBM rating     |
| Short to VBUS | Faulty cable/adapter    | 25V working voltage |
| Transients    | Hot-plug events         | Fast clamping       |

The STUSB4500 has internal CC protection up to 22V, but external TVS provides additional margin and faster response.

## Design Considerations

### Placement

- Place ESDA25L as close as possible to USB-C connector
- Short traces to GND for effective clamping
- Before any series resistors on CC lines

### Capacitance Impact

- 3pF typical capacitance is acceptable for CC communication
- USB PD CC signaling tolerates up to 200pF

## Alternative Parts

| Part      | Package  | Voltage | Capacitance | Notes             |
| --------- | -------- | ------- | ----------- | ----------------- |
| ESDA25L   | SOT-23   | 25V     | 3pF         | Recommended       |
| ESDA25W   | SOT-353  | 25V     | 1.5pF       | Lower capacitance |
| ESDA25SC6 | SOT-23-6 | 25V     | 1.5pF       | 4-channel version |

## References

- [ESDA25L Datasheet (ST)](https://www.st.com/resource/en/datasheet/esda25.pdf)
- [JLCPCB Part Page](https://jlcpcb.com/partdetail/C343997)
- [USB Type-C ESD Protection App Note](https://www.st.com/resource/en/application_note/an4641-design-guidelines-for-using-st-esd-protection-device-for-usb-typec-interface-stmicroelectronics.pdf)
