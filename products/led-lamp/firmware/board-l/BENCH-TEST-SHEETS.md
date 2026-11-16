# Board L bench test sheets

**Status: ALL SHEETS NOT EXECUTED.** No Board L has been programmed or energized with
this firmware. A sheet does not give permission: programming (including option bytes)
and energizing each need the owner's explicit permission, as in
[BEFORE-PROGRAMMING-CHECKLIST.md](BEFORE-PROGRAMMING-CHECKLIST.md).

These sheets record measurements. They do not tune firmware values. A row outside its
limit is a **stop**: power down, record it, and do not continue on that board.

Scope: the current path, zudo-pd P15 r1 (NVM accepted first) with the two existing
Board Ls, RS1 = 200 mΩ as built, firmware `target/` with `CTRL_FULL_CCR` = 2407
([current path](../../candidates/README.md#current-path-p15-r1--the-two-existing-board-ls)).

Expected values are desk values: typical AL8860 CTRL transfer, nominal parts. They are
not guaranteed limits.

## Header (fill once per board and session)

| Field | Value |
| --- | --- |
| Board L serial / marking | |
| Board P (P15) serial, NVM acceptance record | |
| Date, operator | |
| Firmware git commit, `make` size output, ELF SHA256 | |
| `CTRL_FULL_CCR` built / `BOARD_L_PRODUCTION` defined? | 2407 / |
| RS1 measured resistance (mΩ), four-wire Kelvin across pads (checklist 1.1) | |
| RS1 instrument identity and measurement date (board identity above) | |
| RS1 measurement executed? | NOT EXECUTED |
| Source: current-limited bench supply (limit) or P15 | |
| Instruments (scope, DMM, thermocouple) and probe points | |
| Ambient temperature | |

Codes below are 12-bit ADC codes, ratiometric to V3P3: V = code / 4095 × V3P3.

## Sheet B: boot and reset (CTRL must stay low)

Basis: checklist section 0.1. AN2606 Rev 71 Table 106 lists USART1/2 and I2C1/2 as the
G03x/G04x bootloader interfaces; RM0444 Rev 6 gives PA6 reset mode Analog. Neither is a
measurement. This sheet is the measurement.

Scope CH1 = TP1 (CTRL), CH2 = V3P3, trigger on V3P3 rising, ≥ 1 s capture, ≥ 10 kS/s.

| # | Condition | Expect | Stop if | Result | Executed? |
| --- | --- | --- | --- | --- | --- |
| B1 | Blank MCU, NRST held low, SW2 ON | TP1 ≈ 0 V for the whole capture | TP1 > 0.2 V at any point | | NOT EXECUTED |
| B2 | Blank MCU, NRST released (bootloader phase), 10 s | TP1 ≈ 0 V; no LED light; RS1 drop ≈ 0 mV | TP1 > 0.2 V, light, or RS1 drop | | NOT EXECUTED |
| B3 | Probe connect: read bootloader ID / version (read only) | Recorded value | — | | NOT EXECUTED |
| B4 | Target image, power-on | TP1 ≈ 0 V until the ramp; record the time from V3P3 = 3.0 V to the first CTRL edge | TP1 > 0.2 V before the ramp | | NOT EXECUTED |
| B5 | Target image, SW2 OFF → ON, 5 times, ≥ 2 s apart | Same as B4 each time | Any glitch > 0.2 V | | NOT EXECUTED |
| B6 | Target image, slow V3P3 ramp, only if the bench source allows a slow V15 ramp | Same as B4; record any edge on TP1 | Any glitch > 0.2 V | | NOT EXECUTED |
| B7 | Pin reset (NRST pulse) while lit | CTRL low during and after reset, ramp restarts | CTRL not low within one carrier period of NRST low | | NOT EXECUTED |
| B8 | Reset latch: checklist 6.4–6.5a | As in the checklist | As in the checklist | | NOT EXECUTED |
| B9 | IWDG: checklist 6.6 | Reset in about 100 ms (LSI typical) | No reset | | NOT EXECUTED |

## Sheet O: option bytes (read before any write)

Address FLASH_OPTR = 0x40022020. Write only with explicit permission.

| # | Step | Expect | Result (raw hex) | Executed? |
| --- | --- | --- | --- | --- |
| O1 | Read FLASH_OPTR under reset, save the probe log | Recorded factory value | | NOT EXECUTED |
| O2 | Decode RDP, BOR_EN, BORR_LEV, BORF_LEV, IWDG_SW, WWDG_SW, nBOOT_SEL/nBOOT1/nBOOT0, NRST_MODE | Recorded per field | | NOT EXECUTED |
| O3 | With target image and **unprogrammed** option bytes, power on | No light (TP1 ≈ 0 V); `g_boot_decision.refusals` contains 0x2 and/or 0x4 | | NOT EXECUTED |
| O4 | (Permission) write target: RDP 0xAA, BOR_EN 1, BORR/BORF 3, IWDG_SW 1 (dev), WWDG_SW 1, nBOOT_SEL/nBOOT1/nBOOT0 1/1/1, NRST_MODE 3, others unchanged | — | | NOT EXECUTED |
| O5 | Readback after write | Equals target | | NOT EXECUTED |
| O6 | Readback after OBL_LAUNCH | Equals target | | NOT EXECUTED |
| O7 | Readback after a full power cycle | Equals target | | NOT EXECUTED |
| O8 | Boot from main flash with PA14 floating, and with the probe attached | Firmware runs in both | | NOT EXECUTED |

Stop if RDP reads anything other than 0xAA before a write, or if any readback differs
from the target. Never write RDP Level 2.

## Sheet F: firmware image identity (checklist section 4)

Keep option-byte readbacks separately in sheet O. Use raw binary bytes matching
`objcopy -O binary` from the retained ELF, not the receipt file or whole ELF hash.
Readback requires separate authorization; this blank record grants none.

| Field | Value |
| --- | --- |
| Retained build receipt artifact | |
| Retained ELF artifact and ELF SHA256 | |
| Expected `artifacts.loadable_image_sha256` | |
| Expected `artifacts.loadable_image_bytes` | |
| ELF/linker-confirmed load start (current layout: `0x08000000`) | |
| Address range: start inclusive, end exclusive (start + expected bytes) | |
| Actual raw flash-image readback artifact | |
| Actual readback byte length and SHA256 | |
| Comparison outcome (length, range, representation and hash) | |
| Executed? | NOT EXECUTED |

## Sheet K: knob (BRIGHT_ADC on PA0)

Firmware placeholders: off band ≤ code 91 (≈ 0.073 V), full at code 4000 (≈ 3.22 V),
8-sample window. These are bring-up placeholders that need this calibration.

| # | Knob position | Measure | Expect | Result | Executed? |
| --- | --- | --- | --- | --- | --- |
| K1 | Fully counter-clockwise | BRIGHT_ADC (C22) V, ADC code (debugger), TP1 | ≈ 0 V, code ≤ 91, TP1 0 V (hard OFF) | | NOT EXECUTED |
| K2 | Just above the off band | Same | TP1 ≈ 0.41 V (CCR 518) | | NOT EXECUTED |
| K3 | 25 % / 50 % / 75 % rotation | Same | Monotonic increase | | NOT EXECUTED |
| K4 | Fully clockwise | Same | ≈ 3.2 V, code ≥ 4000, TP1 ≈ 1.90 V after a ≈ 2.5 s ramp | | NOT EXECUTED |
| K5 | Hold at the off-band edge 30 s | TP1 on scope | No chatter between OFF and the floor | | NOT EXECUTED |
| K6 | Sweep min → max → min in about 2 s | TP1 | Follows without steps larger than the ramp | | NOT EXECUTED |

Stop if TP1 > 1.95 V at any knob position with the default ceiling.

## Sheet C: CTRL output and LED current

| # | Point | Expect (typical) | Stop if | Result | Executed? |
| --- | --- | --- | --- | --- | --- |
| C1 | Carrier frequency at the PA6 side of R20 (before the RC filter) | 20 kHz (ARR + 1 = 3200 at 64 MHz) | Not 20 kHz: clock fallback | | NOT EXECUTED |
| C2 | TP1 mean at maximum | ≈ 1.90 V | > 1.95 V | | NOT EXECUTED |
| C3 | RS1 drop at maximum → total mean | ≈ 76 mV → ≈ 381 mA | > 80 mV | | NOT EXECUTED |
| C4 | Each ballast R30–R37 drop → branch mean (8 values) | ≈ 1.57 V → ≈ 48 mA | Any branch > 81 mA mean | | NOT EXECUTED |
| C5 | Coil / LED_N ripple at min and max V15, hottest branch | Gives the real hysteresis h | Mean × (1 + h) > 81 mA | | NOT EXECUTED |
| C6 | Pulse-skip burst rate near the floor | Recorded | Bursts < ~300 Hz | | NOT EXECUTED |
| C7 | Debugger halt while lit (development build) | TP1 holds its last value (≤ ceiling) | TP1 rises | | NOT EXECUTED |

The C4/C5 limit of 81 mA is the firmware design target from the #52 analysis, below the
90 mA LED absolute maximum. Meeting it on the bench does not make it a guaranteed limit.

## Sheet N: NTC (NTC_SENSE on PA4, RT1 10 kΩ B3380 to GND, R26 100 kΩ to V3P3)

Firmware thresholds: derate starts at code 104 (≈ 65 °C), no light at code ≤ 69
(≈ 80 °C), open sensor at code ≥ 3500.

| # | Condition | Measure | Expect | Result | Executed? |
| --- | --- | --- | --- | --- | --- |
| N1 | Cold board, ambient recorded | NTC_SENSE (C24) V, ADC code, thermocouple at RT1 | ≈ 0.30 V (code ≈ 372) at 25 °C | | NOT EXECUTED |
| N2 | Compare code with the B3380 curve at ambient | Code vs computed | Recorded difference | | NOT EXECUTED |
| N3 | NTC open (only with an approved fixture, no rework without approval) | Code, TP1 | Code ≥ 3500, OFF and latched until reset | | NOT EXECUTED |
| N4 | NTC short simulation (only with an approved fixture) | Code, TP1 | Code ≤ 69, OFF | | NOT EXECUTED |

Stop if N1 reads near 0 V (short) or near V3P3 (open) on an unmodified board.

## Sheet T: temperature (lit, steady state)

Thermocouple TC1 at the hottest LED solder point, TC2 at RT1, TC3 at U2 (AL8860), TC4
at RS1. Enclosure state recorded (open bench / closed enclosure).

| # | Condition | Measure every 2 min until 3 readings change < 1 °C | Expect | Stop if | Result | Executed? |
| --- | --- | --- | --- | --- | --- | --- |
| T1 | Knob max, open bench, ambient recorded | TC1–TC4, NTC code, TP1 | Steady state reached; record the NTC-to-TC1 offset | TC1 > 76 °C before derate starts | | NOT EXECUTED |
| T2 | Knob max, closed enclosure | Same | Same | Same | | NOT EXECUTED |
| T3 | Derate onset (only if reached naturally; no forced heating without approval) | NTC code at derate start vs TC1 | Derate begins before TC1 ≈ 76 °C | Derate after 76 °C | | NOT EXECUTED |
| T4 | Knob 50 %, closed enclosure | TC1–TC4 | Recorded | — | | NOT EXECUTED |

The 76 °C reference is the #52 analysis figure for 250 mΩ; with 200 mΩ the derate must
start earlier. Neither number is a measured LED rating.

## Close-out

Record which rows ran, which did not, and why. A row left blank stays NOT EXECUTED. Do
not mark a sheet PASS unless every row in it was executed and within its limits.
