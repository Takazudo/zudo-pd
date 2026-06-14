---
title: STUSB4500 Pin Cheat-Sheet (beginner)
sidebar_position: 11
---

A rough "what is each pin for" guide for the STUSB4500 USB-PD sink controller (U1, QFN-24)
as wired on this board. Grouped by function so the whole chip makes sense, not just 24
isolated pins. For the authoritative electrical detail see the ST datasheet (DS12499) Table 1
and Figure 10; for the v3 pin-18 failure story see
[v3 PD Failure Diagnosis](v3-pd-failure-diagnosis.md).

## The one-line mental model

```
CC1/CC2 negotiate the contract
        │
        ▼
VBUS_VS_DISCH confirms real VBUS arrived and is in range
        │
        ▼
VBUS_EN_SNK flips ON → drives Q1 (load switch) → power flows downstream
```

v3 failed because **VBUS_VS_DISCH couldn't see VBUS** (it was tied to GND). Fixed in v0.4.0:
`VBUS_IN → R14 (470 Ω) → pin 18`.

## USB-C orientation / connection sense

| Pin | Name | Rough purpose | On this board |
| --- | --- | --- | --- |
| 2 | **CC1** | USB-C Configuration Channel. Detects attach + cable orientation, and carries the **PD negotiation messages** ("give me 15 V/3 A"). | External 5.1 kΩ Rd (R17) to GND |
| 4 | **CC2** | Same as CC1, other orientation. | External 5.1 kΩ Rd (R18) to GND |
| 1 | **CC1DB** | "Dead Battery" pin — lets the chip signal presence *before* it has power (battery-powered designs). | Not used (no battery). Tied to GND via **0 Ω R19** (jumper kept as a test/probe point) |
| 5 | **CC2DB** | Same, for CC2. | Tied to GND via **0 Ω R20** |
| 17 | **A_B_SIDE** | Output: tells you which orientation the cable was plugged in. Pure status/debug. | Not used |

## Power pins (supply + internal regulators)

| Pin | Name | Rough purpose | On this board |
| --- | --- | --- | --- |
| 24 | **VDD** | Main chip supply. This is what wakes the chip up. | From VBUS_IN, decoupled by C1/C2 |
| 23 | **VREG_2V7** | The chip's own internal 2.7 V regulator output. Runs internal logic **and** powers the I²C bus (SCL/SDA pull-ups land here). | 1 µF decap (C30). Also the "is the chip alive?" probe → should read 2.7 V |
| 21 | **VREG_1V2** | Internal 1.2 V regulator output for the digital core. | 1 µF decap (C34). Nothing else connected |
| 22 | **VSYS** | System-supply input. Datasheet: "connect to GND if not used." | Tied to GND (correct for a VBUS-only board) |
| 25 | **EP** | Exposed pad (metal belly of the QFN). Thermal + electrical ground. Must be soldered or the chip misbehaves. | To GND |

## VBUS power-path control (the load switch)

| Pin | Name | Rough purpose | On this board |
| --- | --- | --- | --- |
| 18 | **VBUS_VS_DISCH** | "Voltage Sense + Discharge." Chip watches the **real VBUS voltage** here to confirm 15 V actually arrived and is in range before enabling power. Also bleeds VBUS down on unplug. **Must see real VBUS through a series resistor** — a divider-to-GND breaks it (the v3 bug). | `VBUS_IN → R14 (470 Ω) → pin 18`, also to TP6. HV-tolerant pin (no external divider) |
| 16 | **VBUS_EN_SNK** | "VBUS Enable, Sink" — the chip's **"turn power on now" output**. After a successful contract it drives the gate of load-switch MOSFET Q1 (AO3401A) to connect VBUS downstream. | → Q1 gate (net `VBEN`) |

## Status / flag outputs (open-drain — need a pull-up if you read them)

| Pin | Name | Rough purpose | On this board |
| --- | --- | --- | --- |
| 11 | **ATTACH** | "Something is plugged in" flag (asserts when a USB-C attach is detected on CC). | Routed to a probe pad. Optional status |
| 20 | **POWER_OK2** | "Power contract is good" flag. Asserts when a valid PD contract is established. | Optional status (net `PDOK`) |
| 14 | **POWER_OK3** | Same family as POWER_OK2 — distinguishes which negotiated voltage/PDO succeeded. | Optional status |
| 19 | **ALERT** (ALERT#) | Interrupt line: "something changed, read my registers over I²C." Only matters with a live host MCU. | Not used (NVM-programmed once, then standalone) |

## I²C / config (used during NVM programming, then idle)

| Pin | Name | Rough purpose | On this board |
| --- | --- | --- | --- |
| 7 | **SCL** | I²C clock. Used to write the NVM (the 15 V/3 A PDO settings) from the Nucleo. | Pull-up R15 to VREG_2V7; on J2 pogo |
| 8 | **SDA** | I²C data. | Pull-up R16 to VREG_2V7; on J2 pogo |
| 12 | **ADDR0** | I²C address select strap (tie high/low to set address). | To GND |
| 13 | **ADDR1** | Second address strap. Both ADDR pins to GND → **I²C address 0x28**. Datasheet: "to ground if no connection to MCU." | To GND |
| 6 | **RESET** (RST) | Active-high reset input. Tied to GND = "never reset" = chip runs normally. | To GND (not used) |
| 15 | **GPIO** | General-purpose pin the chip can be NVM-configured to output (e.g. error/attach state). | No function assigned in NVM (unused) |
| 9 | **DISCH** | VBUS discharge-path control (distinct from VBUS_VS_DISCH). Often left to the chip's internal handling. | Not part of this board's power path |
| 3 | **NC** | No connect. | Floating (intentional) |

## Why "not used → tie to GND" is correct (not lazy)

A floating CMOS input can drift to a mid-rail voltage and oscillate or latch unpredictably.
Tying an unused input to a defined level (GND here) makes its state deterministic. For
RESET, GND is also the *active* run state. For the ADDR straps, GND is a meaningful choice
that sets the I²C address. So every "tie to GND" on this chip is a deliberate, datasheet-
sanctioned choice — not a placeholder.
