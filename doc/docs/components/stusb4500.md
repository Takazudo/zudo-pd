---
sidebar_position: 2
---

# STUSB4500 - USB Power Delivery Controller

USB-IF certified USB Power Delivery sink controller for reliable 15V/3A power negotiation from USB-C PD chargers.

- [View on JLCPCB: C2678061](https://jlcpcb.com/partdetail/C2678061)
- [Download Datasheet (PDF)](https://www.st.com/resource/en/datasheet/stusb4500.pdf)

:::tip Why STUSB4500 over CH224D?
**STUSB4500 is USB-IF certified** with significantly better charger compatibility:

| Feature          | CH224D   | STUSB4500       |
| ---------------- | -------- | --------------- |
| USB-IF Certified | No       | **Yes**         |
| Charger Compat.  | ~33%     | **~95%+**       |
| Error Recovery   | None     | **Built-in**    |
| Power Sequencing | None     | **VBUS_EN_SNK** |
| Retry on Failure | No       | **Yes**         |
| CC Protection    | 8V       | **22V**         |
| Configuration    | Resistor | **NVM + I2C**   |

CH224D failed with most modern GaN chargers. STUSB4500 is the recommended replacement for v1.1.
:::

## Overview

The STUSB4500 is a USB Power Delivery (PD) sink controller manufactured by STMicroelectronics. It implements a proprietary algorithm to negotiate power delivery contracts without MCU support (auto-run mode).

Key advantages:

- **USB-IF Certified**: Tested for interoperability with certified chargers
- **NVM Configuration**: Store up to 3 PDO profiles in non-volatile memory
- **Power Path Control**: VBUS_EN_SNK pin controls external load switch
- **Dead Battery Mode**: Can negotiate even with discharged battery
- **I2C Interface**: Optional MCU communication for advanced control

## Key Specifications

| Parameter                    | Value                              | Notes                         |
| ---------------------------- | ---------------------------------- | ----------------------------- |
| **JLCPCB Part Number**       | C2678061                           |                               |
| **Manufacturer Part Number** | STUSB4500QTR                       |                               |
| **Package**                  | QFN-24 (4mm × 4mm)                 | Surface-mount                 |
| **Stock Availability**       | 4,728 units                        | Good availability             |
| **Unit Price**               | ~$2.50                             | JLCPCB pricing                |
| **VDD Voltage Range**        | 4.1V - 22V DC                      | From USB-C VBUS               |
| **VBUS Tolerance**           | Up to 28V                          | Overvoltage tolerant          |
| **CC Pin Protection**        | Up to 22V                          | Short-to-VBUS protection      |
| **Output Voltage Options**   | 5V / 9V / 15V / 20V (configurable) | Via NVM programming           |
| **Maximum Current**          | 5A (100W)                          | Depends on PD source          |
| **PD Protocol Support**      | USB PD 2.0 / 3.0                   | USB-IF certified              |
| **Configuration Method**     | NVM + I2C                          | No MCU required for basic use |
| **Operating Temperature**    | -40°C to +105°C                    |                               |

## Pin Configuration

```
                 STUSB4500QTR (QFN-24)
                      Top View
    ┌──────────────────────────────────────┐
    │                                      │
    │ 1  CC1DB                   VDD    24 │
    │ 2  CC1                 VREG_2V7  23 │
    │ 3  NC                      VSYS  22 │
    │ 4  CC2                 VREG_1V2  21 │
    │ 5  CC2DB              POWER_OK2  20 │
    │ 6  RESET                  ALERT  19 │
    │ 7  SCL             VBUS_VS_DISCH 18 │
    │ 8  SDA                 A_B_SIDE  17 │
    │ 9  DISCH            VBUS_EN_SNK  16 │
    │ 10 GND                     GPIO  15 │
    │ 11 ATTACH            POWER_OK3   14 │
    │ 12 ADDR0                  ADDR1  13 │
    │                                      │
    │          ┌──────────────┐            │
    └──────────┤  Exposed Pad ├────────────┘
               │   GND (25)   │
               └──────────────┘

Note: Pin 16 (VBUS_EN_SNK) is critical for load switch control
```

### Pin Descriptions

| Pin | Name          | Function                             | Connection in Design                  |
| --- | ------------- | ------------------------------------ | ------------------------------------- |
| 25  | GND (EPAD)    | Ground / Thermal pad                 | System ground plane                   |
| 1   | CC1DB         | CC1 dead battery mode                | Connect to CC1                        |
| 2   | CC1           | USB-C Configuration Channel 1        | USB-C CC1 via ESD protection (D4)     |
| 3   | NC            | No connection                        | Leave unconnected                     |
| 4   | CC2           | USB-C Configuration Channel 2        | USB-C CC2 via ESD protection (D4)     |
| 5   | CC2DB         | CC2 dead battery mode                | Connect to CC2                        |
| 6   | RESET         | Active-HIGH reset                    | GND (normal operation)                |
| 7   | SCL           | I2C clock                            | NC (not used in this design)          |
| 8   | SDA           | I2C data                             | NC (not used in this design)          |
| 9   | DISCH         | VBUS discharge control               | Via R13 (470Ω) to VBUS_OUT            |
| 10  | GND           | Ground                               | System ground                         |
| 11  | ATTACH        | Cable attach indicator               | NC (optional LED/MCU)                 |
| 12  | ADDR0         | I2C address bit 0                    | GND (I2C address 0x28)                |
| 13  | ADDR1         | I2C address bit 1                    | GND (I2C address 0x28)                |
| 14  | POWER_OK3     | PDO3 selected indicator              | NC (optional LED/MCU)                 |
| 15  | GPIO          | General purpose I/O                  | NC                                    |
| 16  | VBUS_EN_SNK   | **Load switch enable (active HIGH)** | To P-MOSFET gate via R12 (56kΩ)       |
| 17  | A_B_SIDE      | Cable orientation indicator          | NC                                    |
| 18  | VBUS_VS_DISCH | VBUS voltage sense / discharge       | VBUS_IN via R_VS (470ohm)             |
| 19  | ALERT         | Interrupt output (open-drain)        | NC                                    |
| 20  | POWER_OK2     | PDO2 selected indicator              | NC (optional LED/MCU)                 |
| 21  | VREG_1V2      | 1.2V internal regulator output       | C34 (1µF) to GND                      |
| 22  | VSYS          | System voltage input (3.0-5.5V)      | GND (connect to ground when not used) |
| 23  | VREG_2V7      | 2.7V internal regulator output       | C30 (1µF) to GND                      |
| 24  | VDD           | Main power supply (4.1-22V)          | VBUS_IN + C1 (10µF) + C2 (100nF)      |

## Application Circuit

```
USB-C Connector (J1):
┌───────────────────┐
│  VBUS (A9,B9) ────┼───→ VBUS_IN ───→ VDD (pin 24)
│                   │         │
│  CC1 (A5) ────────┼───→ D4 (USBLC6-2SC6) ───→ CC1 (pin 2) ─┬─→ CC1DB (pin 1)
│  CC2 (B5) ────────┼───→ D4 (USBLC6-2SC6) ───→ CC2 (pin 4) ─┴─→ CC2DB (pin 5)
│                   │
│  GND (A12,B12) ───┼───→ GND (pins 10, 25/EPAD)
└───────────────────┘

STUSB4500 Power Supply:
VBUS_IN ───┬─── C1 (10µF) ─── GND
           └─── C2 (100nF) ── GND
           └───→ VDD (pin 24)

Internal Regulators:
VREG_2V7 (pin 23) ─── C30 (1µF) ─ GND
VSYS (pin 22) ─────── GND
VREG_1V2 (pin 21) ─── C34 (1µF) ─ GND

Load Switch Control:
                                      VBUS_IN
                                         │
                                      R11 (100kΩ)
                                         │
VBUS_EN_SNK (pin 16) ─── R12 (56kΩ) ──┬──┴─── Gate ─── Q1 (AO3401A)
                                      │                Source ─── VBUS_IN
                                     C35 (100nF)       Drain ──── VBUS_OUT
                                      │                           (to DC-DC)
                                     GND

VBUS Discharge:
DISCH (pin 9) ─── R13 (470Ω) ─── VBUS_OUT

VBUS Voltage Sense:
VBUS_IN ─── R_VS (470Ω) ─── VBUS_VS_DISCH (pin 18)

Configuration Pins:
RESET (pin 6) ──── GND (active-HIGH, GND = normal operation)
ADDR0 (pin 12) ─── GND
ADDR1 (pin 13) ─── GND
VSYS (pin 22) ──── GND

CC Line ESD Protection (D4 - USBLC6-2SC6):
USB-C CC1 (A5) ───→ Pin 1 (I/O1) ───→ Pin 6 (I/O1) ───→ STUSB4500 CC1/CC1DB
USB-C CC2 (B5) ───→ Pin 3 (I/O2) ───→ Pin 4 (I/O2) ───→ STUSB4500 CC2/CC2DB
                    Pin 2 (GND) ────→ GND
                    Pin 5 (VBUS) ───→ VBUS_IN
```

### Connection List

**Power Supply:**

- `USB-C VBUS` → `VBUS_IN` → `STUSB4500 VDD (pin 24)`
- `VBUS_IN` → `C1 (10µF)` → `GND`
- `VBUS_IN` → `C2 (100nF)` → `GND`
- `VREG_2V7 (pin 23)` → `C30 (1µF)` → `GND`
- `VREG_1V2 (pin 21)` → `C34 (1µF)` → `GND`
- `VSYS (pin 22)` → `GND`

**CC Lines with ESD Protection (D4 - USBLC6-2SC6):**

- `USB-C CC1 (A5)` → `D4 pin 1` → `D4 pin 6` → `STUSB4500 CC1 (pin 2)` + `CC1DB (pin 1)`
- `USB-C CC2 (B5)` → `D4 pin 3` → `D4 pin 4` → `STUSB4500 CC2 (pin 4)` + `CC2DB (pin 5)`
- `D4 pin 2 (GND)` → `GND`
- `D4 pin 5 (VBUS)` → `VBUS_IN`

**Load Switch (Power Path Control):**

- `VBUS_EN_SNK (pin 16)` → `R12 (56kΩ)` → `Q1 Gate`
- `VBUS_IN` → `R11 (100kΩ)` → `Q1 Gate` (pull-up)
- `Q1 Gate` → `C35 (100nF)` → `GND` (soft-start)
- `Q1 (AO3401A)`: Source=VBUS_IN, Drain=VBUS_OUT

**Discharge Circuit:**

- `DISCH (pin 9)` → `R13 (470Ω)` → `VBUS_OUT`

**VBUS Voltage Sense:**

- `VBUS_IN` → `R_VS (470Ω)` → `VBUS_VS_DISCH (pin 18)`

:::info How DISCH Works
When USB-C cable is disconnected, STUSB4500 opens an internal path from DISCH pin to GND. This allows capacitor charge to escape:

```
VBUS_OUT (15V) → R13 (470Ω) → DISCH → GND (inside STUSB4500)
```

The stored energy drains as heat through R13 (~0.5W briefly). This is required by USB-C spec to bring VBUS to safe level (&lt;0.8V) quickly, preventing hot-plug hazards.
:::

**Configuration:**

- `RESET (pin 6)` → `GND` (active-HIGH reset, GND = normal operation)
- `ADDR0 (pin 12)` → `GND`
- `ADDR1 (pin 13)` → `GND`

## Component Values

### Decoupling Capacitors

| Reference | Value | Type        | Voltage | Package | Purpose             |
| --------- | ----- | ----------- | ------- | ------- | ------------------- |
| C1        | 10µF  | Ceramic X5R | 25V     | 0805    | VDD bulk decoupling |
| C2        | 100nF | Ceramic X7R | 25V     | 0603    | VDD HF decoupling   |
| C30       | 1µF   | Ceramic X5R | 16V     | 0603    | VREG_2V7 decoupling |
| C34       | 1µF   | Ceramic X5R | 16V     | 0603    | VREG_1V2 decoupling |
| C35       | 100nF | Ceramic X7R | 50V     | 0603    | Gate soft-start     |

### Resistors

| Reference | Value | Tolerance | Package | Purpose                           |
| --------- | ----- | --------- | ------- | --------------------------------- |
| R11       | 100kΩ | ±1%       | 0603    | Gate pull-up                      |
| R12       | 56kΩ  | ±1%       | 0603    | Gate voltage divider (Vgs margin) |
| R13       | 470Ω  | ±1%       | 0603    | VBUS discharge (31mA @ 15V)       |
| R_VS      | 470Ω  | ±1%       | 0603    | VBUS_VS_DISCH series resistor     |

:::info R12 Value Selection
R12 was changed from 33kΩ to 56kΩ to provide adequate Vgs margin for Q1:

- With R12=56kΩ: Vgs = -15V × 100k/(100k+56k) = **-9.6V** (20% margin from ±12V max)
- With R12=33kΩ: Vgs = -11.3V (only 6% margin - too close to limit)
  :::

### Load Switch MOSFET

| Reference | Part    | Type      | Vds  | Id  | Rds(on) | Vgs(max) | Package |
| --------- | ------- | --------- | ---- | --- | ------- | -------- | ------- |
| Q1        | AO3401A | P-Channel | -30V | -4A | 44mΩ    | ±12V     | SOT-23  |

### CC Line ESD Protection (Recommended)

| Reference | Part        | Type            | Vwm | Channels | Capacitance | Package  | LCSC  |
| --------- | ----------- | --------------- | --- | -------- | ----------- | -------- | ----- |
| D4        | USBLC6-2SC6 | TVS Diode Array | 5V  | 2 + VBUS | 3.5pF       | SOT-23-6 | C7519 |

:::tip Why USBLC6-2SC6?

- **Low clamping voltage** (~17V) - better protection for CC lines operating at ~1.7V
- **Includes VBUS protection** - pin 5 can connect to VBUS_IN for additional transient protection
- **USB-specific design** - optimized for USB-C applications
- **Low capacitance** (3.5pF) - doesn't affect CC line signaling
  :::

## NVM Configuration

STUSB4500 stores PDO configuration in 40 bytes of non-volatile memory (NVM).

### Default PDO Configuration for This Design

| PDO  | Voltage | Current | Purpose            |
| ---- | ------- | ------- | ------------------ |
| PDO1 | 5V      | 1.5A    | Fixed (mandatory)  |
| PDO2 | **15V** | **3A**  | **Target voltage** |
| PDO3 | 20V     | 1.5A    | Fallback option    |

### Programming Methods

1. **ST GUI Tool (STSW-STUSB002)**
- Requires STEVAL-ISC005V1 eval board
- Windows application
- Easy point-and-click configuration

2. **Arduino/MCU via I2C**
- Community libraries available
- [GitHub: usb-c/STUSB4500](https://github.com/usb-c/STUSB4500)

3. **Pre-programmed Parts**
- Some distributors offer programming service

### NVM Write Cycles

- Limited to ~1000 write cycles
- Configure once during production
- Do not write NVM repeatedly in normal operation

## Power Sequencing

STUSB4500 provides built-in power sequencing via **VBUS_EN_SNK** pin:

```
Timeline:
┌─────────────────────────────────────────────────────────────────┐
│ Cable Connect                                                   │
│      │                                                          │
│      ▼                                                          │
│   VBUS = 5V (default)                                           │
│      │                                                          │
│   VBUS_EN_SNK = LOW ← Load switch OFF                           │
│      │                                                          │
│   PD Negotiation (retries if needed)                            │
│      │                                                          │
│   Negotiation SUCCESS → VBUS = 15V                              │
│      │                                                          │
│   VBUS_EN_SNK = HIGH ← Load switch ON                           │
│      │                                                          │
│   VBUS_OUT = 15V (stable, to DC-DC converters)                  │
└─────────────────────────────────────────────────────────────────┘
```

This eliminates inrush current issues during PD negotiation.

## Layout Recommendations

1. **Decoupling Caps**: Place C_VDD, C1, C2 as close as possible to their respective pins
2. **Ground Plane**: Connect EPAD to ground plane with multiple vias
3. **CC Traces**: Keep CC1/CC2 traces short, away from switching noise
4. **Load Switch**: Place Q1 and gate components near STUSB4500
5. **Thermal**: EPAD provides thermal dissipation

## Troubleshooting

| Symptom                  | Possible Cause            | Solution                                   |
| ------------------------ | ------------------------- | ------------------------------------------ |
| No PD negotiation        | NVM not programmed        | Program NVM with correct PDO configuration |
| Wrong voltage output     | PDO configuration error   | Verify NVM settings via I2C                |
| Load switch always OFF   | VBUS_EN_SNK not connected | Check connection to gate network           |
| Intermittent negotiation | Inadequate decoupling     | Check C_VDD, C1, C2 values and placement   |
| Overheating              | Poor thermal connection   | Improve EPAD ground connection             |
| I2C not responding       | Wrong address             | Check ADDR0/ADDR1 pin settings             |
| No VBUS voltage sense    | VBUS_VS_DISCH not connected | Connect pin 18 to VBUS_IN via 470ohm resistor |

## Known Issues / Design Errata

### v1 PCBA Issues (Fixed in v1.1)

Three issues were found in the v1 PCBA that prevented STUSB4500 from operating correctly:

1. **VBUS_VS_DISCH (pin 18) not connected**: Pin 18 was left as NC (no connection). The datasheet requires this pin to be connected to VBUS_IN through a 470ohm series resistor for VBUS voltage sensing and discharge. Fixed by adding R_VS (470ohm) between VBUS_IN and pin 18.

2. **VSYS (pin 22) shorted to VREG_2V7 (pin 23)**: A routing error connected pin 22 (VSYS input) to pin 23 (VREG_2V7 regulator output), overloading the internal 2.7V regulator. Fixed by cutting the trace and wiring VSYS to GND.

3. **VSYS (pin 22) left floating**: After the trace cut fix above, VSYS was left floating instead of being connected to GND. The datasheet recommends grounding VSYS when not used. Fixed by adding a bodge wire from pin 22 to GND.

For full details, see the [PCBA v1 Debug Report](/docs/inbox/pcba-v1-debug).

## References

- [STUSB4500 Datasheet (ST)](https://www.st.com/resource/en/datasheet/stusb4500.pdf)
- [STEVAL-ISC005V1 Eval Board](https://www.st.com/en/evaluation-tools/steval-isc005v1.html)
- [Application Note AN5225](https://www.st.com/resource/en/application_note/an5225-usbc-power-delivery-using-stusb1602-stmicroelectronics.pdf)
- [GitHub: usb-c/STUSB4500](https://github.com/usb-c/STUSB4500)
- [SparkFun Power Delivery Board](https://www.sparkfun.com/products/15801)
- [JLCPCB Part Page](https://jlcpcb.com/partdetail/C2678061)
