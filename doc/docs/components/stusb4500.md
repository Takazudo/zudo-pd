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
              STUSB4500 (QFN-24)
                  Top View
    ┌─────────────────────────────────┐
    │                                 │
 A_B│1                            24│ VREG_1V2
CC1 │2                            23│ CC1DB
CC2 │3                            22│ CC2DB
VBUS│4                            21│ DISCH
 VDD│5                            20│ ATTACH
 GND│6                            19│ GPIO
    │                                │
VREG│7                            18│ ALERT
_2V7│                                │
 SCL│8                            17│ ADDR1
 SDA│9                            16│ ADDR0
    │10                           15│ RESET
VSYS│11                           14│ POWER_OK3
 GND│12                           13│ POWER_OK2
    │       ┌──────────────┐         │
    └───────┤  Exposed Pad ├─────────┘
            │     GND      │
            └──────────────┘

Note: Pin 10 is VBUS_EN_SNK (critical for load switch control)
```

### Pin Descriptions

| Pin  | Name        | Function                             | Connection in Design                       |
| ---- | ----------- | ------------------------------------ | ------------------------------------------ |
| EPAD | GND         | Ground / Thermal pad                 | System ground plane                        |
| 1    | A_B_SIDE    | Cable orientation indicator          | NC or monitor (optional)                   |
| 2    | CC1         | USB-C Configuration Channel 1        | USB-C connector CC1                        |
| 3    | CC2         | USB-C Configuration Channel 2        | USB-C connector CC2                        |
| 4    | VBUS_VS     | VBUS voltage sense                   | USB-C VBUS via resistor divider (optional) |
| 5    | VDD         | Main power supply (4.1-22V)          | USB-C VBUS + 100nF decoupling              |
| 6    | GND         | Ground                               | System ground                              |
| 7    | VREG_2V7    | 2.7V internal regulator output       | 1µF decoupling to GND                      |
| 8    | SCL         | I2C clock                            | I2C bus or NC (with pull-up if used)       |
| 9    | SDA         | I2C data                             | I2C bus or NC (with pull-up if used)       |
| 10   | VBUS_EN_SNK | **Load switch enable (active HIGH)** | To P-MOSFET gate network                   |
| 11   | VSYS        | System voltage input (3.0-5.5V)      | 3.3V or tie to VREG_2V7                    |
| 12   | GND         | Ground                               | System ground                              |
| 13   | POWER_OK2   | PDO2 selected indicator              | LED or MCU (optional)                      |
| 14   | POWER_OK3   | PDO3 selected indicator              | LED or MCU (optional)                      |
| 15   | RESET       | Active-low reset                     | VDD via 10kΩ (or MCU controlled)           |
| 16   | ADDR0       | I2C address bit 0                    | GND or VDD (sets I2C address)              |
| 17   | ADDR1       | I2C address bit 1                    | GND (with &gt;10kΩ pull-up recommended)    |
| 18   | ALERT       | Interrupt output (open-drain)        | MCU interrupt or NC                        |
| 19   | GPIO        | General purpose I/O                  | NC or custom use                           |
| 20   | ATTACH      | Cable attach indicator               | LED or MCU (optional)                      |
| 21   | DISCH       | VBUS discharge control               | Via 470Ω to VBUS (for discharge)           |
| 22   | CC2DB       | CC2 dead battery mode                | Connect to CC2 or GND                      |
| 23   | CC1DB       | CC1 dead battery mode                | Connect to CC1 or GND                      |
| 24   | VREG_1V2    | 1.2V internal regulator output       | 1µF decoupling to GND                      |

## Application Circuit

```
USB-C Connector (6-pin):
┌─────────────────────────────┐
│  VBUS  ────────────────────┼──┬──→ VDD (pin 5)
│                            │  │
│  CC1   ────────────────────┼──┼──→ CC1 (pin 2), CC1DB (pin 23)
│  CC2   ────────────────────┼──┼──→ CC2 (pin 3), CC2DB (pin 22)
│                            │  │
│  GND   ────────────────────┼──┼──→ GND (pins 6, 12, EPAD)
└────────────────────────────┘  │
                                │
STUSB4500 Power Supply:         │
                                │
VBUS ───────────────────────────┼──→ VDD (pin 5)
                                │        │
                               C_VDD   100nF
                                │        │
                               GND      GND

Internal Regulators:
VREG_2V7 (pin 7) ─── C1 (1µF) ─── GND
VREG_1V2 (pin 24) ── C2 (1µF) ─── GND

Load Switch Control:
                                      VBUS_IN
                                         │
                                        R1 (100kΩ)
                                         │
VBUS_EN_SNK (pin 10) ─── R2 (33kΩ) ──┬───┴─── Gate ─── Q1 (AO3401A)
                                     │                 Source ─── VBUS_IN
                                    C5 (100nF)         Drain ──── VBUS_OUT
                                     │                            (to DC-DC)
                                    GND

VBUS Discharge:
DISCH (pin 21) ─── R3 (470Ω) ─── VBUS_OUT

Configuration Pins:
RESET (pin 15) ─── R4 (10kΩ) ─── VDD
ADDR0 (pin 16) ─── GND
ADDR1 (pin 17) ─── GND (or 10kΩ to VDD)
VSYS (pin 11) ──── VREG_2V7 (pin 7)

Optional CC Protection:
CC1 (pin 2) ───┬─── TVS1 (ESDA25L) ─── GND
CC2 (pin 3) ───┘
```

### Connection List

**Power Supply:**

- `USB-C VBUS` → `STUSB4500 VDD (pin 5)` + `C_VDD (100nF)` → `GND`
- `VREG_2V7 (pin 7)` → `C1 (1µF)` → `GND`
- `VREG_1V2 (pin 24)` → `C2 (1µF)` → `GND`
- `VSYS (pin 11)` → `VREG_2V7 (pin 7)`

**CC Lines:**

- `USB-C CC1` → `STUSB4500 CC1 (pin 2)` → `CC1DB (pin 23)`
- `USB-C CC2` → `STUSB4500 CC2 (pin 3)` → `CC2DB (pin 22)`
- Optional: `TVS1 (ESDA25L)` from CC1/CC2 to GND for ESD protection

**Load Switch (Power Path Control):**

- `VBUS_EN_SNK (pin 10)` → `R2 (33kΩ)` → `Q1 Gate`
- `VBUS_IN` → `R1 (100kΩ)` → `Q1 Gate` (pull-up)
- `Q1 Gate` → `C5 (100nF)` → `GND` (soft-start)
- `Q1 (AO3401A)`: Source=VBUS_IN, Drain=VBUS_OUT

**Discharge Circuit:**

- `DISCH (pin 21)` → `R3 (470Ω)` → `VBUS_OUT`

**Configuration:**

- `RESET (pin 15)` → `R4 (10kΩ)` → `VDD`
- `ADDR0 (pin 16)` → `GND`
- `ADDR1 (pin 17)` → `GND`

## Component Values

### Decoupling Capacitors

| Reference | Value | Type        | Voltage | Package | Purpose             |
| --------- | ----- | ----------- | ------- | ------- | ------------------- |
| C_VDD     | 100nF | Ceramic X7R | 25V     | 0603    | VDD decoupling      |
| C1        | 1µF   | Ceramic X5R | 16V     | 0603    | VREG_2V7 decoupling |
| C2        | 1µF   | Ceramic X5R | 16V     | 0603    | VREG_1V2 decoupling |
| C5        | 100nF | Ceramic X7R | 25V     | 0603    | Gate soft-start     |

### Resistors

| Reference | Value | Tolerance | Package | Purpose              |
| --------- | ----- | --------- | ------- | -------------------- |
| R1        | 100kΩ | ±1%       | 0603    | Gate pull-up         |
| R2        | 33kΩ  | ±1%       | 0603    | Gate voltage divider |
| R3        | 470Ω  | ±1%       | 0603    | VBUS discharge       |
| R4        | 10kΩ  | ±1%       | 0603    | RESET pull-up        |

### Load Switch MOSFET

| Reference | Part    | Type      | Vds  | Id  | Rds(on) | Package |
| --------- | ------- | --------- | ---- | --- | ------- | ------- |
| Q1        | AO3401A | P-Channel | -30V | -4A | 44mΩ    | SOT-23  |

### CC Protection (Optional but Recommended)

| Reference | Part    | Type      | Vwm | Package |
| --------- | ------- | --------- | --- | ------- |
| TVS1      | ESDA25L | TVS Diode | 25V | SOT-23  |

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

## References

- [STUSB4500 Datasheet (ST)](https://www.st.com/resource/en/datasheet/stusb4500.pdf)
- [STEVAL-ISC005V1 Eval Board](https://www.st.com/en/evaluation-tools/steval-isc005v1.html)
- [Application Note AN5225](https://www.st.com/resource/en/application_note/an5225-usbc-power-delivery-using-stusb1602-stmicroelectronics.pdf)
- [GitHub: usb-c/STUSB4500](https://github.com/usb-c/STUSB4500)
- [SparkFun Power Delivery Board](https://www.sparkfun.com/products/15801)
- [JLCPCB Part Page](https://jlcpcb.com/partdetail/C2678061)
