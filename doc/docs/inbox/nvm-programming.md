---
sidebar_position: 5
---

# STUSB4500 NVM Programming Setup

The STUSB4500 requires NVM (non-volatile memory) programming to configure its USB-PD negotiation behavior. Factory defaults will negotiate **20V** (not 15V), which would damage downstream circuits. This page documents the hardware setup, required NVM values, and schematic changes needed.

## Why NVM Programming Is Required

The STUSB4500QTR ships from the factory with these default PDO profiles:

| PDO | Voltage | Current | Priority |
| --- | --- | --- | --- |
| PDO1 | 5V | 1.5A | Lowest (3rd) |
| PDO2 | 15V | 1.5A | Middle (2nd) |
| PDO3 | **20V** | 1.0A | **Highest (1st)** |

### Problems with Factory Defaults

1. **Wrong voltage**: PDO3 (20V) has highest priority. With multi-voltage chargers (5V/9V/15V/20V), the IC negotiates **20V** instead of 15V. This feeds 20V into DC-DC converters designed for 15V input.
2. **Insufficient current**: Even when 15V is negotiated (charger lacks 20V), only 1.5A is requested. The design needs 3A.
3. **No power sequencing**: `POWER_ONLY_ABOVE_5V` defaults to disabled, so VBUS_EN_SNK enables at 5V before PD negotiation completes. This exposes downstream circuits to voltage transitions.

### Target NVM Configuration

| PDO | Voltage | Current | Priority |
| --- | --- | --- | --- |
| PDO1 | 5V | 1.5A | Lowest (3rd) |
| PDO2 | **15V** | **3A** | **Highest (1st)** |
| PDO3 | 20V | 1.5A | Lowest (2nd) |

Additional settings:

- `POWER_ONLY_ABOVE_5V` = **enabled** (VBUS_EN_SNK only activates after 15V negotiation succeeds)
- `SNK_PDO_NUMB` = 3 (advertise all 3 PDOs)
- PDO2 priority set to highest

## Hardware Required

### Programming Tool: Pogo Pin Clip (4P, 2.54mm)

A spring-loaded pogo pin clip clamps onto the PCB edge and contacts bare copper pads for temporary I2C connection. No soldered header needed.

| Item | Description | Source | Approx. Price |
| --- | --- | --- | --- |
| Pogo pin clip | 4P single-row, 2.54mm pitch, with dupont wires | [AliExpress](https://ja.aliexpress.com/item/1005006108783889.html) | ~410 JPY |

### Option A: NUCLEO-F072RB + STSW-STUSB002 GUI (Recommended)

Only one board is needed. The STEVAL-ISC005V1 eval board is **not required** since we program the STUSB4500 on our own PCB.

| Item | Part | Source | Approx. Price |
| --- | --- | --- | --- |
| NUCLEO-F072RB | STM32 Nucleo board | [DigiKey Japan](https://www.digikey.jp/ja/products/detail/stmicroelectronics/NUCLEO-F072RB/5047984) | ~2,200 JPY |
| STSW-STUSB002 | Windows GUI software | [ST Website](https://www.st.com/en/embedded-software/stsw-stusb002.html) | Free |

The Nucleo board acts as a **USB-to-I2C bridge** when flashed with the included `.bin` firmware.

**Connection:**

```
Windows PC ─── USB ───→ NUCLEO-F072RB ─── pogo clip ───→ zudo-pd board edge pads
                        D15 (PB8) = SCL ────────────────→ J2 pad 1 (SCL)
                        D14 (PB9) = SDA ────────────────→ J2 pad 2 (SDA)
                        GND ────────────────────────────→ J2 pad 3 (GND)
                        (unused) ───────────────────────→ J2 pad 4 (NC)
```

The pogo clip's dupont wires connect to the Nucleo's D14, D15, and GND pins. The clip clamps onto the zudo-pd board edge where J2 pads are located.

The Nucleo I2C operates at 3.3V, compatible with STUSB4500's VREG_2V7 (2.7V) via open-drain I2C bus. No level shifter needed.

:::info Why not STEVAL-ISC005V1?
The STEVAL-ISC005V1 (~7,000 JPY on DigiKey Japan) has its own STUSB4500 and USB-C connector. It's designed for evaluating the IC standalone. Since we have our own PCB with the STUSB4500 already soldered, we only need the Nucleo as an I2C bridge. The GUI documentation confirms it works with "evaluation board, or custom board containing STUSB device."
:::

### Option B: Arduino / MCU via I2C (Alternative)

If you already have a 3.3V Arduino or similar MCU board, the [SparkFun STUSB4500 Arduino Library](https://github.com/sparkfun/SparkFun_STUSB4500_Arduino_Library) supports full NVM programming via `write()`. No Windows GUI needed.

**Requirements:**

- Arduino or MCU board with 3.3V I2C (not 5V - would need level shifter)
- SparkFun library installed
- Connect SCL, SDA, GND to zudo-pd J2 pads via pogo clip

## Schematic Changes for I2C Programming Pads

The v1 schematic has SCL (pin 7) and SDA (pin 8) as NC (not connected). These must be connected to edge pads with pull-up resistors for NVM programming.

### New Components

| Ref | Part | LCSC / Source | Value | Package | Purpose |
| --- | --- | --- | --- | --- | --- |
| J2 | Pogo pad 1x4 | No component (bare PCB pads) | - | Custom SMD pads | I2C programming pads (board edge) |
| R15 | Resistor | [C23162](https://jlcpcb.com/partdetail/C23162) | 4.7kohm | 0603 | I2C SCL pull-up |
| R16 | Resistor | [C23162](https://jlcpcb.com/partdetail/C23162) | 4.7kohm | 0603 | I2C SDA pull-up |

:::info J2 Pogo Pads - No Assembly Cost
J2 is not a physical component - it is bare copper SMD pads on the PCB edge. No JLCPCB component or assembly fee is needed. The pogo pin clip (external tool) clamps onto these pads during programming. This saves ~$7 compared to a THT pin header (Extended part fee + hand-soldering fee).
:::

### KiCad Symbol and Footprint

| Item | Recommendation |
| --- | --- |
| **Symbol** | `Connector_Generic:Conn_01x04` (built-in KiCad library) |
| **Footprint** | Custom `zudo-pd:PogoPad_1x04_P2.54mm` (create in project footprint library) |

**Custom footprint specifications:**

- 4 SMD pads in a single row
- Pad size: 2.0mm x 1.0mm (rectangular) or 1.5mm diameter (round)
- Pitch: 2.54mm (0.1 inch)
- **Must be placed at the PCB edge** so the pogo clip can grip the board
- No solder mask on pads (exposed copper for contact)
- Silkscreen labels: SCL, SDA, GND, NC

**Pad placement on PCB:**

```
                    PCB edge
───────────────────────┐
                       │
  ○ SCL  (pad 1)      │  ← 2.54mm pitch
  ○ SDA  (pad 2)      │     bare copper pads
  ○ GND  (pad 3)      │     within ~10mm of edge
  ○ NC   (pad 4)      │
                       │
───────────────────────┘
```

### Circuit

```
                    VREG_2V7 (pin 23, 2.7V)
                         │
                    ┌────┴────┐
                    │         │
                R15 (4.7kΩ) R16 (4.7kΩ)
                    │         │
SCL (pin 7) ────────┤         │
                    │         │
SDA (pin 8) ────────┼─────────┤
                    │         │
              J2 pad 1     J2 pad 2     J2 pad 3    J2 pad 4
                (SCL)       (SDA)        (GND)       (NC)
                    │         │            │            │
              ┌─────┴─────────┴────────────┴────────────┴──┐
              │        J2 (Pogo Pads, 1x4, 2.54mm)         │
              │        Bare copper pads at board edge       │
              └────────────────────────────────────────────┘
```

Pull-ups connect to VREG_2V7 (2.7V) since this is the I2C bus voltage for the STUSB4500. The Nucleo's 3.3V I2C is compatible with 2.7V open-drain signaling.

### Connection List

- `STUSB4500 SCL (pin 7)` &rarr; `R15 (4.7kohm)` &rarr; `VREG_2V7`
- `STUSB4500 SCL (pin 7)` &rarr; `J2 pad 1`
- `STUSB4500 SDA (pin 8)` &rarr; `R16 (4.7kohm)` &rarr; `VREG_2V7`
- `STUSB4500 SDA (pin 8)` &rarr; `J2 pad 2`
- `J2 pad 3` &rarr; `GND`
- `J2 pad 4` &rarr; `NC` (not connected)

## Programming Procedure

### Step 1: Flash the Nucleo Firmware

1. Download STSW-STUSB002 from [ST website](https://www.st.com/en/embedded-software/stsw-stusb002.html)
2. Connect NUCLEO-F072RB to Windows PC via USB
3. The Nucleo appears as a USB mass storage device
4. Copy the included `.bin` file to the Nucleo drive
5. The Nucleo LED blinks to confirm firmware is loaded

### Step 2: Connect to zudo-pd Board

1. Plug a USB-C PD charger into the zudo-pd USB-C connector (to power the STUSB4500 via VDD)
2. Connect the pogo clip's dupont wires to the Nucleo:
- Nucleo D15 (SCL) &rarr; pogo clip wire for pad 1
- Nucleo D14 (SDA) &rarr; pogo clip wire for pad 2
- Nucleo GND &rarr; pogo clip wire for pad 3
3. Clamp the pogo clip onto the zudo-pd board edge, aligning the pogo pins with J2 pads
4. The STUSB4500 should be detected at I2C address 0x28

### Step 3: Program NVM

1. Open STSW-STUSB002 GUI on Windows
2. The GUI should show "STUSB 45 is Detected"
3. Click "Read device NVM" to verify communication
4. Configure PDO settings:
- SNK_PDO_NUMB: 3
- PDO1: 5V, 1.5A (mandatory)
- PDO2: 15V, 3A (target - set highest priority)
- PDO3: 20V, 1.5A (fallback)
5. Enable `POWER_ONLY_ABOVE_5V` checkbox
6. Click "Write device NVM"
7. Check "Verify after write" to confirm

### Step 4: Verify

1. Remove the pogo clip from the board
2. Reconnect the USB-C PD charger
3. Measure VBUS_OUT with a multimeter - should read 15V
4. Verify VBUS_EN_SNK behavior (should stay LOW at 5V, go HIGH only after 15V negotiation)

## NVM Write Cycle Limit

The STUSB4500 NVM is rated for approximately **1,000 write cycles**. Configure once during production. Do not write NVM repeatedly in normal operation.

## Schematic Fix Checklist

- [ ] Remove no-connect markers from SCL (pin 7) and SDA (pin 8)
- [ ] Add R15 (4.7kohm, 0603) from SCL to VREG_2V7
- [ ] Add R16 (4.7kohm, 0603) from SDA to VREG_2V7
- [ ] Add J2 symbol (`Connector_Generic:Conn_01x04`) connected to SCL, SDA, GND, NC
- [ ] Create custom footprint `PogoPad_1x04_P2.54mm` in zudo-pd library
- [ ] Assign footprint to J2
- [ ] Place J2 pads at board edge in PCB layout
- [ ] Run DRC

## References

- [STSW-STUSB002 Data Brief (PDF)](https://www.st.com/resource/en/data_brief/stsw-stusb002.pdf) - GUI tool documentation
- [STSW-STUSB002 Download](https://www.st.com/en/embedded-software/stsw-stusb002.html) - Software download page
- [NUCLEO-F072RB on DigiKey Japan](https://www.digikey.jp/ja/products/detail/stmicroelectronics/NUCLEO-F072RB/5047984) - Board purchase
- [SparkFun STUSB4500 Arduino Library](https://github.com/sparkfun/SparkFun_STUSB4500_Arduino_Library) - Alternative MCU-based programming
- [GitHub: usb-c/STUSB4500](https://github.com/usb-c/STUSB4500) - Official ST reference code with NVM flasher
- [STUSB4500 Datasheet](https://www.st.com/resource/en/datasheet/stusb4500.pdf) - NVM register map details
- [Pogo Pin Clip (AliExpress)](https://ja.aliexpress.com/item/1005006108783889.html) - 4P 2.54mm programming clip tool
