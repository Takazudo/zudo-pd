---
sidebar_position: 4
---

# PCBA v1 Debug Report

Debug analysis of the first PCBA prototype (v1) for the USB-PD modular synthesizer power supply. The STUSB4500 USB-PD controller stage failed to negotiate power delivery. This report documents the root causes, required fixes, and rework instructions.

## Root Cause Summary

Three issues were identified in the STUSB4500 circuit on the v1 PCBA:

| # | Issue | Pin(s) | Severity | Status |
| --- | --- | --- | --- | --- |
| 1 | VBUS_VS_DISCH (pin 18) not connected | Pin 18 | Critical | **Fix required** |
| 2 | VSYS (pin 22) floating after disconnect fix | Pin 22 | Critical | **Fix required** |
| 3 | VSYS (pin 22) shorted to VREG_2V7 (pin 23) | Pin 22, 23 | Critical | **Already fixed** (trace cut) |

## Pin-by-Pin Analysis

Complete comparison of the v1 schematic against the STUSB4500 datasheet and ST reference designs (STEVAL-ISC005V1, SparkFun Power Delivery Board).

| Pin | Name | Datasheet Requirement | v1 Design | Status | Notes |
| --- | --- | --- | --- | --- | --- |
| 1 | CC1DB | Connect to CC1 | Connected to CC1 | OK | Dead battery mode |
| 2 | CC1 | USB-C CC1 via ESD | Via D4 (USBLC6-2SC6) | OK | |
| 3 | NC | No connection | Unconnected | OK | |
| 4 | CC2 | USB-C CC2 via ESD | Via D4 (USBLC6-2SC6) | OK | |
| 5 | CC2DB | Connect to CC2 | Connected to CC2 | OK | Dead battery mode |
| 6 | RESET | Active-HIGH reset, tie to GND for normal | GND | OK | |
| 7 | SCL | I2C clock (optional) | NC | OK | Not used in this design |
| 8 | SDA | I2C data (optional) | NC | OK | Not used in this design |
| 9 | DISCH | VBUS discharge via resistor | R13 (470ohm) to VBUS_OUT | OK | |
| 10 | GND | Ground | System ground | OK | |
| 11 | ATTACH | Cable attach indicator | NC | OK | Optional |
| 12 | ADDR0 | I2C address bit 0 | GND | OK | Address 0x28 |
| 13 | ADDR1 | I2C address bit 1 | GND | OK | Address 0x28 |
| 14 | POWER_OK3 | PDO3 indicator | NC | OK | Optional |
| 15 | GPIO | General purpose I/O | NC | OK | |
| 16 | VBUS_EN_SNK | Load switch enable | R12 (56kohm) to Q1 gate | OK | |
| 17 | A_B_SIDE | Cable orientation | NC | OK | Optional |
| **18** | **VBUS_VS_DISCH** | **VBUS_IN via 470ohm series resistor** | **NC** | **FAIL** | **Critical: must connect** |
| 19 | ALERT | Interrupt output | NC | OK | Optional |
| 20 | POWER_OK2 | PDO2 indicator | NC | OK | Optional |
| 21 | VREG_1V2 | 1uF decoupling to GND | C34 (1uF) to GND | OK | |
| **22** | **VSYS** | **GND (when not used) or 3.0-5.5V** | **Floating (after trace cut)** | **FAIL** | **Must wire to GND** |
| 23 | VREG_2V7 | 1uF decoupling to GND | C30 (1uF) to GND | OK | |
| 24 | VDD | VBUS_IN + decoupling | VBUS_IN + C1 (10uF) + C2 (100nF) | OK | |
| 25 | GND (EPAD) | Ground / thermal pad | System ground plane | OK | |

## Critical Issue 1: VBUS_VS_DISCH Not Connected (Pin 18)

### What Is VBUS_VS_DISCH?

Pin 18 (VBUS_VS_DISCH) serves two critical functions according to the STUSB4500 datasheet:

1. **VBUS voltage sensing**: The STUSB4500 uses this pin to monitor the actual VBUS voltage level. This is essential for verifying that the PD source is delivering the negotiated voltage.
2. **VBUS discharge path**: When a USB-C cable is disconnected, STUSB4500 uses this pin (in addition to the DISCH pin) to discharge VBUS capacitors safely.

### Impact of Leaving It Unconnected

Without VBUS_VS_DISCH connected:

- The IC cannot verify VBUS voltage levels during PD negotiation
- VBUS discharge on disconnect may be incomplete or slower
- The IC may fail to transition through its internal state machine correctly
- PD negotiation may fail silently or behave erratically

### Required Fix

Connect VBUS_VS_DISCH (pin 18) to VBUS_IN through a 470ohm series resistor (R_VS):

```
VBUS_IN ─── R_VS (470ohm) ─── VBUS_VS_DISCH (pin 18)
```

The 470ohm resistor limits current during the discharge phase when the IC pulls this pin low through an internal MOSFET. This matches the ST reference design (STEVAL-ISC005V1).

## Critical Issue 2: VSYS Floating After Trace Cut (Pin 22)

### What Happened

In the original v1 schematic, VSYS (pin 22) was incorrectly connected to the VREG_2V7 net (pin 23). This was identified as Issue #3 (see below) and fixed by cutting the trace on the PCBA. However, cutting the trace left VSYS floating - which is also incorrect.

### What VSYS Does

VSYS is the system voltage input for an optional external LDO or battery (3.0V - 5.5V range). When an external system supply is not used, the datasheet states:

> "It is recommended to connect the pin to ground when it is not used."

### Impact of Floating VSYS

A floating VSYS pin can cause:

- Undefined internal power management behavior
- Potential noise coupling from adjacent pins
- Unreliable startup sequencing
- The IC may not properly initialize its internal state machine

### Required Fix

Connect VSYS (pin 22) directly to GND:

```
VSYS (pin 22) ─── GND
```

No resistor needed - direct connection to ground.

## Critical Issue 3: VSYS-VREG_2V7 Short (Pin 22-23) - Already Fixed

### What Happened

The original v1 schematic had VSYS (pin 22) connected to the same net as VREG_2V7 (pin 23). This created a direct short between:

- **VSYS**: An input pin expecting either GND or an external 3.0-5.5V supply
- **VREG_2V7**: An output pin from the IC's internal 2.7V regulator

### Why This Was Bad

Shorting these pins forced the internal 2.7V regulator output into the VSYS input. The 2.7V regulator is designed to power internal logic and has limited current capability. Connecting it to VSYS (which has different impedance characteristics) could:

- Overload the internal regulator
- Create voltage instability on the 2.7V rail
- Prevent proper IC initialization
- Potentially damage the IC over time

### Fix Applied

The trace between pin 22 and pin 23 was cut on the v1 PCBA. This resolved the short but left VSYS floating (see Issue #2 above).

### Schematic Fix

In the schematic, VSYS (pin 22) must be moved from the VREG_2V7 net to GND. This was documented in commit `2865c9e` but the corresponding KiCad schematic change still needs to be completed.

## Additional Concerns

### NVM Default Configuration

The STUSB4500's factory-default NVM may not be configured for 15V/3A. The default configuration typically requests 5V only. Before the board can negotiate 15V, the NVM must be programmed with the correct PDO profile:

| PDO | Voltage | Current |
| --- | --- | --- |
| PDO1 | 5V | 1.5A |
| PDO2 | 15V | 3A |
| PDO3 | 20V | 1.5A |

Programming requires either the ST GUI tool (STSW-STUSB002) with an eval board, or an MCU via I2C.

### Power Path Switch Component Values

The current design uses R11 (100kohm) and R12 (56kohm) for the gate drive network with Q1 (AO3401A). The ST reference design uses R11 = 22kohm with the STL6P3LLH6 MOSFET. While the current values should work, verify that:

- Gate voltage divider provides sufficient Vgs for Q1
- Turn-on/turn-off timing is acceptable
- No oscillation at the gate during transitions

### Inrush Current

With the power path switch controlling &gt;3A of load current, ensure the soft-start capacitor C35 (100nF) provides adequate inrush limiting during turn-on.

## Bodge Wire Instructions for Existing PCBA Rework

For reworking v1 boards that already have the VSYS-VREG_2V7 trace cut:

### Fix 1: Wire VSYS to GND

1. Locate pin 22 (VSYS) on U3 (STUSB4500)
2. Solder a thin wire (30 AWG) from pin 22 to the nearest GND pad or via
3. Pin 22 is on the top-right side of the QFN-24 package (between pin 21 VREG_1V2 and pin 23 VREG_2V7)
4. Use flux and a fine-tip soldering iron

### Fix 2: Connect VBUS_VS_DISCH

1. Prepare a 470ohm 0402 or 0603 resistor (R_VS)
2. Locate pin 18 (VBUS_VS_DISCH) on U3 - right side of the package, between pin 17 (A_B_SIDE) and pin 19 (ALERT)
3. Solder one end of R_VS to pin 18
4. Solder the other end of R_VS to VBUS_IN (e.g., the VBUS trace near VDD pin 24 or C1/C2)
5. Secure the bodge wire/resistor with UV-cure adhesive or kapton tape

### Verification After Rework

After bodge wires are applied:

1. Continuity check: VSYS (pin 22) to GND should read &lt;1ohm
2. Continuity check: VBUS_VS_DISCH (pin 18) through R_VS to VBUS_IN should read ~470ohm
3. No shorts between adjacent pins (especially pin 22-23)
4. Connect a USB-C PD charger and verify VBUS negotiation

## Schematic Fix Checklist

Before ordering v1.1 PCBA:

- [ ] Connect VBUS_VS_DISCH (pin 18) to VBUS_IN via new R_VS (470ohm) resistor
- [ ] Connect VSYS (pin 22) to GND (not floating, not VREG_2V7)
- [ ] Verify VREG_2V7 (pin 23) has only C30 (1uF) decoupling - no other connections
- [ ] Run DRC (Design Rule Check) in KiCad
- [ ] Review all STUSB4500 pin connections against this debug report
- [ ] Program NVM with correct PDO configuration (15V/3A target)
- [ ] Verify power path switch gate drive values

## References

- [STUSB4500 Datasheet (ST)](https://www.st.com/resource/en/datasheet/stusb4500.pdf) - Pin descriptions and recommended connections
- [STEVAL-ISC005V1 Evaluation Board](https://www.st.com/en/evaluation-tools/steval-isc005v1.html) - ST reference design schematic
- [SparkFun Power Delivery Board](https://www.sparkfun.com/products/15801) - Open-source reference design
- [GitHub: usb-c/STUSB4500](https://github.com/usb-c/STUSB4500) - Community reference and Arduino library
- [ST Community: STUSB4500 not working](https://community.st.com/t5/power-management/stusb4500-not-working/td-p/811126) - Forum discussion on common failure modes
- [ST Community: STUSB4500 not communicating](https://community.st.com/t5/others-hardware-and-software/stusb4500-not-communicating-on-i2c-or-sinking-power/td-p/758753) - I2C and power issues
