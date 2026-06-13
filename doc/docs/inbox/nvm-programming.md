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

The safest configuration **eliminates PDO3 entirely** so 20V is never an option, regardless of how the STUSB4500 prioritizes PDOs internally:

| PDO | Voltage | Current | Notes |
| --- | --- | --- | --- |
| PDO1 | 5V | 1.5A | Mandatory by USB-PD spec, always advertised |
| PDO2 | **15V** | **3A** | Target operating point |
| ~~PDO3~~ | ~~20V~~ | ~~–~~ | **Disabled** by setting `SNK_PDO_NUMB = 2` |

Additional settings:

- `SNK_PDO_NUMB` = **2** (only PDO1 + PDO2; PDO3 never advertised → 20V never requested)
- `POWER_ONLY_ABOVE_5V` = **enabled** (VBUS_EN_SNK only activates after 15V negotiation succeeds)

:::tip Why SNK_PDO_NUMB = 2 instead of 3?
The STUSB4500's priority logic between PDOs is documented ambiguously across ST sources (some say PDO3 has highest priority by number, some say highest-power wins). The only way to *guarantee* 20V is never requested is to not advertise it at all. The design needs 15V, not 20V, and a charger lacking 15V wouldn't power this device usefully anyway.
:::

## Hardware Required

### Programming Tool: Pogo Pin Clip (4P, 2.54mm)

A spring-loaded pogo pin clip clamps onto the PCB edge and contacts bare copper pads for temporary I2C connection. No soldered header needed.

| Item | Description | Source | Approx. Price |
| --- | --- | --- | --- |
| Pogo pin clip | 4P single-row, 2.54mm pitch, with dupont wires | [AliExpress](https://ja.aliexpress.com/item/1005006108783889.html) | ~410 JPY |

**Clip mechanical specs:**

- **AliExpress item**: 1005006108783889 (equivalent to Adafruit 5433 / The Pi Hut variant)
- **Max landing depth**: 25 mm from board edge — the clip body cannot reach further inward
- **Recommended landing**: 2–3 mm inward from the board edge — gives the clip body a lip to grip and centers the pogo tips on the pad
- **Minimum pad-to-edge clearance**: 0.3 mm for JLCPCB manufacturing (0.5 mm is safer to avoid routing issues)

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

**Pad placement on PCB:**

The 4 SMD pads sit in a single row. **J2 must be placed at the PCB edge** so the pogo clip can grip the board — see the `PogoPad footprint design` subsection below for the concrete pad/layer/silkscreen spec.

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

### PogoPad footprint design

The footprint `PogoPad_1x04_P2.54mm` records the concrete numbers used in the actual KiCad file:

| Property | Value |
| --- | --- |
| Pad shape | Rectangular |
| Pad size | 1.5 mm × 2.5 mm |
| Pitch | 2.54 mm (0.1 inch) |
| Layers | `F.Cu` + `F.Mask` only |
| `F.Paste` | **Not included** |

**Why no solder paste (`F.Paste`)?**
Pogo pins contact bare copper directly — no solder joint is formed. Including `F.Paste` would deposit solder paste on these pads during SMT manufacturing, which would harden into a rough surface that prevents reliable pogo tip contact. JLCPCB also rejects paste on edge pads. Omitting `F.Paste` keeps the copper surface clean and exposed.

**Silkscreen markings:**

- Pin labels: `SCL`, `SDA`, `GND`, `NC` (one per pad)
- An edge-side line running parallel to the pad row, indicating the board edge
- A `<-- EDGE` text marker placed outside the board outline (for placement orientation only — this gets cut off during PCB fabrication, which is intentional)

**File locations in this repo:**

- `footprints/kicad/PogoPad_1x04_P2.54mm.kicad_mod` (master copy)
- `footprints/kicad/zudo-power.pretty/PogoPad_1x04_P2.54mm.kicad_mod` (KiCad library path)

Both locations must exist and stay in sync. See `footprints/CLAUDE.md` for the dual-location rule and the workflow for keeping them in sync.

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
2. Extract the archive — you'll find **two .bin files**:
- `Nucleo_F072RB_STUSB_HID_NVM_config_*.bin` (HID variant)
- `Nucleo_F072RB_STUSB_UART_NVM_config_*.bin` (UART variant)
3. **Use the UART variant.** Reason explained in the callout below.
4. Connect NUCLEO-F072RB to Windows PC via USB (CN1, the ST-Link USB Mini-B)
5. The Nucleo appears as a USB mass storage device labeled `NODE_F072RB`
6. Drag the UART `.bin` file onto the Nucleo drive
7. The LD1 LED blinks rapidly during flashing, then settles. The drive will disappear/remount.
8. **Unplug and replug USB** — the Nucleo needs to re-enumerate with the new firmware
9. Verify in Windows Device Manager: **Ports (COM & LPT)** should show "STMicroelectronics STLink Virtual COM Port (COMx)". If no COM port appears, install the [ST-Link VCP driver](https://www.st.com/en/development-tools/stsw-link009.html).

:::warning HID vs UART .bin choice (critical)
The HID variant requires a **separate USB connection to the STM32F072's native USB pins (PA11/PA12)**, which on the NUCLEO-F072RB are only broken out to header pins — not wired to CN1. The HID firmware is intended for use with the **STEVAL-ISC005V1** daughter board, which provides this second USB connection.

For our setup (bare NUCLEO-F072RB, no STEVAL daughter board), only the UART firmware works because it communicates through the **ST-Link's built-in Virtual COM Port (VCP)** over the same CN1 USB cable.

Symptom of wrong choice: GUI shows "STM32-Nucleo-board not Detected" even after flash + replug. Only "ST-Link debug" appears in Device Manager. Fix: re-flash with the UART .bin.
:::

Sources:
- [STSW-STUSB002 quick start guide (PDF)](https://www.st.com/resource/en/product_presentation/stswstusb002_quick_start_v3_2.pdf) — explicit UART vs HID guidance
- [NUCLEO-F072RB schematic (MB1136-C03)](https://www.st.com/resource/en/schematic_pack/mb1136-default-c03_schematic.pdf) — confirms CN1 is ST-Link only

### Step 2: Connect to zudo-pd Board

1. **Use a low-power USB-C charger** for the programming session — see warning below
2. Plug the charger into the zudo-pd USB-C connector (to power the STUSB4500 via VDD)
3. Connect the pogo clip's dupont wires to the Nucleo's **Arduino-compatible CN5 header**:
- Nucleo **D15** (SCL, labeled on board silkscreen) &rarr; pogo clip wire for pad 1
- Nucleo **D14** (SDA) &rarr; pogo clip wire for pad 2
- Nucleo **GND** (any GND pin) &rarr; pogo clip wire for pad 3
- Pogo pad 4 unused
4. Clamp the pogo clip onto the zudo-pd board edge, aligning the pogo pins with J2 pads
5. The STUSB4500 should be detected at I2C address `0x28`

### Step 2.5: If the GUI Still Says "STUSB4500 not Detected"

Before debugging the Nucleo or STSW-STUSB002, first prove the zudo-pd board is actually
powered on the STUSB4500 side.

Do **not** use TP1 / TP3 / TP4 / TP5 for this check. TP1 is downstream of the Q1 load
switch, and TP3-TP5 are downstream converter rails. These can all read **0 V** during NVM
programming, especially before a valid PD contract enables `VBUS_EN_SNK`.

Use the J3 debug pogo block instead:

| Probe point | Expected with 5 V USB source | Meaning |
| --- | --- | --- |
| **J3 pad 4, VDD / VBUS_IN** to GND | about **5 V** | USB VBUS is reaching U1 pin 24 |
| **J3 pad 3, VREG_2V7** to GND | about **2.7 V** | STUSB4500 is awake |
| **J2 pad 1, SCL** to GND | about **2.7 V idle** | I2C pull-up R15 is present and powered |
| **J2 pad 2, SDA** to GND | about **2.7 V idle** | I2C pull-up R16 is present and powered |

Decision tree:

| Measurement | Likely fault |
| --- | --- |
| J3 pad 4 = **0 V** | The USB source is not applying VBUS, or the USB-C connector / VBUS_IN path is open |
| J3 pad 4 = **5 V**, J3 pad 3 = **0 V** | STUSB4500 not starting, VREG_2V7 short/open, bad U1 soldering, or bad U1 |
| J3 pad 3 = **2.7 V**, but GUI does not detect chip | Pogo alignment, SCL/SDA swapped, missing GND between Nucleo and zudo-pd, or Nucleo firmware/COM issue |

If J3 pad 4 is 0 V with a USB-C-to-USB-C charger, try a known-good **USB-A-to-USB-C 5 V**
source. USB-A-to-C supplies 5 V directly through the cable, which separates "board cannot
request VBUS over CC" from "VBUS trace or chip supply is physically broken."

:::warning Charger choice for initial programming
The factory NVM in a fresh STUSB4500 advertises PDO3 = 20V/1.0A with **highest priority**. A full PD charger that supports 20V will negotiate 20V on first plug-in, sending **20V through your DC-DC converters designed for 15V** — likely damaging them.

**Use a 5V-only USB-C charger** (any phone charger) or a PD charger that maxes out at 9V/15V (no 20V profile) for the initial programming session. The chip's VDD only needs 5V to communicate via I2C.

After NVM is written with `SNK_PDO_NUMB = 2` (no 20V advertised), you can safely switch to your real PD charger.
:::

:::tip Detection sequence
The GUI launch normally shows two dialogs in sequence:

1. **"STM32-Nucleo-board not Detected"** — appears if no Nucleo is connected, GUI starts in "File Edition mode"
2. **"STM32-Nucleo-board connected. But STUSB4500 not Detected"** — appears when Nucleo is found but no chip yet (i.e., pogo clip not connected to powered zudo-pd)

After clipping the pogo onto the powered board, **close and reopen the GUI** — it scans for the chip on startup. Status bar should change to:

```
[OK] STUSB4500 Detected [COM3] ST-ii0244, at address 0x28 (I2C bus 1)
```

Once detected, the "Read device NVM" and "Write device NVM" buttons appear in the top-right.
:::

### Step 3: Program NVM

1. With chip detected (status bar shows `[OK] STUSB4500 Detected`), click **"Read device NVM"** to load actual chip values into the GUI
2. The "SNK Parameters" tab will populate with the factory defaults — confirm they match the expected defaults (PDO1: 5V/1.5A, PDO2: 15V/1.5A, PDO3: 20V/1.0A)
3. Configure target settings:

| Field | New value | Reason |
| --- | --- | --- |
| **SNK_PDO_NUMB** | **`2`** | Only advertise PDO1 + PDO2. PDO3 (20V) never negotiated. |
| **PDO2 Current** | **`3.00 A`** | Design needs 3A on the 15V rail |
| **POWER_ONLY_ABOVE_5V** | **checked** | VBUS_EN_SNK only enables after 15V negotiated |
| PDO1 (5V/1.5A) | keep | Mandatory USB-PD default |
| PDO2 Voltage (15V) | keep | Target rail voltage |
| Other settings | leave alone | Don't touch FLEX_I, UVLO/OVLO, GPIO, etc. |

4. Verify "**Verify after write**" checkbox at top-right is checked (default)
5. Click **"Write device NVM"**
6. Wait for the write to complete and verification to succeed

### Step 4: Verify

1. Click **"Read device NVM"** again to confirm the new values stuck (especially `POWER_ONLY_ABOVE_5V` — it sometimes doesn't save on the first write)
2. Remove the pogo clip from the board
3. Reconnect a real USB-C PD charger that supports 15V
4. Measure VBUS_OUT with a multimeter — should read **15V** (or 5V if charger doesn't support 15V — fallback behavior)
5. Verify VBUS_EN_SNK behavior (should stay LOW at 5V, go HIGH only after 15V negotiation completes)

### Verifying via the GUI's Dashboard tab

The "Dashboard" tab shows real-time CC state — useful for diagnosis. With charger plugged in and pogo clip still attached:

- **CC Connection** section should show **"Sink attached"** or similar (NOT "No device attached")
- **CC Operation** should show the negotiated PD contract (voltage, current)
- **Monitoring** shows live VBUS voltage and current

If Dashboard says **"No device attached"** while a PD charger is plugged in, the chip's CC pins are not seeing a valid source termination — this is a hardware-level issue, not a NVM issue. See [PCBA v2 Debug Report](/docs/inbox/pcba-v2-debug) for the CC1DB internal short failure mode we encountered.

## NVM Write Cycle Limit

The STUSB4500 NVM is rated for approximately **1,000 write cycles**. Configure once during production. Do not write NVM repeatedly in normal operation.

## Common Pitfalls (from actual programming sessions)

| Symptom | Cause | Fix |
| --- | --- | --- |
| GUI shows "STM32-Nucleo-board not Detected" after flashing | Flashed HID `.bin` instead of UART `.bin` | Re-flash with `Nucleo_F072RB_STUSB_UART_NVM_config_*.bin` |
| Only "ST-Link debug" in Device Manager, no COM port | ST-Link VCP driver not installed | Install [STSW-LINK009](https://www.st.com/en/development-tools/stsw-link009.html) |
| GUI launches but says "Offline - File Edition mode" | Nucleo not actually re-enumerated after flash | Unplug Nucleo USB and replug |
| "I2C Read error. Error number: -2 (0xFFFFFFFE)" on GUI startup | Expected — fires when GUI tries to read NVM with no chip on bus yet | Click OK. Connect zudo-pd via pogo clip, then relaunch GUI. |
| TP1 / TP3 / TP4 / TP5 all read 0 V during programming | Expected if Q1 and the downstream converters are off | Check J3 pad 4 (VDD/VBUS_IN) and J3 pad 3 (VREG_2V7) instead |
| J3 pad 4 reads 0 V with a USB-C charger | Source is not applying VBUS, CC termination is not being accepted, or USB-C connector/VBUS path is open | Try USB-A-to-C 5 V source; then check CC1/CC2 to GND are ~5.1kohm each |
| J3 pad 4 reads 5 V but J3 pad 3 reads 0 V | U1 is powered but not awake | Inspect U1 soldering/EPAD, VREG_2V7 capacitor C30, and shorts on VREG_2V7 |
| Status stays "STUSB4500 Not Detected" even with pogo clip on powered board | Charger may be negotiating 20V on factory NVM and chip is in error state | Switch to a 5V-only charger for the programming session |
| Bin file remains visible on NODE_F072RB drive after drag | Flash failed (USB cable might be charge-only, no data) | Use a USB data cable, not charge-only |
| "POWER_ONLY_ABOVE_5V" doesn't save after Write NVM | Sometimes the first write doesn't persist this bit | Click Read NVM to verify, then re-write if needed |
| Dashboard says "No device attached" with charger plugged in | Chip's CC pins not seeing source termination (hardware issue, not NVM) | See [PCBA v2 Debug Report](/docs/inbox/pcba-v2-debug) for the CC1DB internal short failure |

## Schematic Fix Checklist

- [x] Remove no-connect markers from SCL (pin 7) and SDA (pin 8)
- [x] Add R15 (4.7kohm, 0603) from SCL to VREG_2V7
- [x] Add R16 (4.7kohm, 0603) from SDA to VREG_2V7
- [x] Add J2 symbol (`Connector_Generic:Conn_01x04`) connected to SCL, SDA, GND, NC
- [x] Create custom footprint `PogoPad_1x04_P2.54mm` in zudo-pd library
- [x] Assign footprint to J2
- [x] Place J2 pads at board edge in PCB layout
- [x] Run DRC

## References

- [STSW-STUSB002 Data Brief (PDF)](https://www.st.com/resource/en/data_brief/stsw-stusb002.pdf) - GUI tool documentation
- [STSW-STUSB002 Quick Start Guide (PDF)](https://www.st.com/resource/en/product_presentation/stswstusb002_quick_start_v3_2.pdf) - **HID vs UART .bin selection guidance**
- [STSW-STUSB002 Download](https://www.st.com/en/embedded-software/stsw-stusb002.html) - Software download page
- [STSW-LINK009 - ST-Link VCP Driver](https://www.st.com/en/development-tools/stsw-link009.html) - Required if COM port doesn't appear in Device Manager
- [NUCLEO-F072RB Schematic (MB1136-C03 PDF)](https://www.st.com/resource/en/schematic_pack/mb1136-default-c03_schematic.pdf) - Confirms CN1 USB is wired to ST-Link only
- [NUCLEO-F072RB on DigiKey Japan](https://www.digikey.jp/ja/products/detail/stmicroelectronics/NUCLEO-F072RB/5047984) - Board purchase
- [SparkFun STUSB4500 Arduino Library](https://github.com/sparkfun/SparkFun_STUSB4500_Arduino_Library) - Alternative MCU-based programming
- [GitHub: usb-c/STUSB4500](https://github.com/usb-c/STUSB4500) - Official ST reference code with NVM flasher
- [STUSB4500 Datasheet](https://www.st.com/resource/en/datasheet/stusb4500.pdf) - NVM register map details
- [Pogo Pin Clip (AliExpress)](https://ja.aliexpress.com/item/1005006108783889.html) - 4P 2.54mm programming clip tool
- [PCBA v2 Debug Report](/docs/inbox/pcba-v2-debug) - CC1DB internal short failure mode discovered during v2 testing
