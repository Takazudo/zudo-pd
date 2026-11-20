---
title: Lamp prototype preparation
description: Preparation list and post-arrival sequence for the P15 r1 + Board L lamp prototype; consolidates existing procedures, nothing run.
sidebar_position: 2
---

Adopted path: shared **P15 r1** and the **two Board Ls received from the 2026-09-19 order**, with
RS1 = 200 mΩ and `CTRL_FULL_CCR` = 2407. Status and owners are on the [LED Lamp](./index.mdx) landing.

This page consolidates existing procedures and adds no new steps. Nothing on it has been run. Every programming,
energizing, option-byte, readback or fit step needs the owner's explicit permission. HUSB238, the 250 mΩ rework,
the 3200 ceiling and new animation behaviour are not adopted.

Procedure owners:

- **[PD-PROG]** [P15 NVM programming](../architecture/board-p15-programming.md) (P15-NVM-1–7).
- **[CHK]** [`firmware/board-l/BEFORE-PROGRAMMING-CHECKLIST.md`](https://github.com/Takazudo/zudo-pd/blob/main/products/led-lamp/firmware/board-l/BEFORE-PROGRAMMING-CHECKLIST.md).
- **[SHEETS]** [`firmware/board-l/BENCH-TEST-SHEETS.md`](https://github.com/Takazudo/zudo-pd/blob/main/products/led-lamp/firmware/board-l/BENCH-TEST-SHEETS.md).
- **[SWD]** [SWD adapter](./architecture/swd-adapter.mdx) (historical LED page).
- **[ENC]** [`enclosure/README.md`](https://github.com/Takazudo/zudo-pd/blob/main/products/led-lamp/enclosure/README.md).
- **[MFG]** [P15 order handoff](https://github.com/Takazudo/zudo-pd/blob/main/manufacturing/p15-order-handoff.md).
- **[STATE]** [LED status checkpoint](./architecture/current-state.mdx) (owner actions 1–7; historical LED page).

## 1. Preparation list

Quantities are for the full path: 2 P15 + 2 Board L. Lamp-level items are **per lamp**. Whether one or two lamps
will be enclosed is not stated anywhere (**UNKNOWN**).

| Item | Qty | Source / note | Status |
| --- | --- | --- | --- |
| P15 r1 assembled modules | 2 | [P15 order handoff](https://github.com/Takazudo/zudo-pd/blob/main/manufacturing/p15-order-handoff.md): frozen `corner-support-review/board-p15/` gerbers, BOM and CPL with their hashes | NOT ORDERED; owner checkout checks open (D5/D9 polarity, stock, eligibility, cost) |
| Board L (2026-09-19) | 2 (have) | `products/led-lamp/boards/board-l/` | Received; not inspected; MCU believed blank; RS1 marking not evidenced |
| **P15 programming jig** | | | |
| USB-to-I2C bridge: NUCLEO-F072RB with the STSW-STUSB002 GUI on a Windows PC, or a 3.3 V MCU with the SparkFun STUSB4500 library | 1 | Archived [NVM programming notes](../inbox/nvm-programming.md) (Option A recommended); [PD-PROG] uses a 3.3 V NUCLEO rail | UNKNOWN whether owned |
| External I2C pull-ups to the jig 3.3 V rail (**not** to P15 J3.3 VREG_2V7) | 2 (SCL, SDA) | [PD-PROG]: start at 2.2 kΩ; allowed range 967 Ω–3.39 kΩ at ≤ 100 pF bus | Clip and wire capacitance UNMEASURED; NUCLEO VOL at 1.3 mA to be measured |
| 4P 2.54 mm pogo-pin edge clip with dupont wires (P15 J2: 1 SCL, 2 SDA, 3 GND, 4 NC) | 1 | Archived [NVM programming notes](../inbox/nvm-programming.md) | UNKNOWN whether owned |
| Current-limited **5 V-only** USB-C source | 1 | [PD-PROG] steps 1–8 | Exact device UNKNOWN |
| PD test source that also offers 20 V, through a current-limited path, no load | 1 | [PD-PROG] step 9 (P15-NVM-6) | Exact device UNKNOWN |
| USB-C cable for P15 J1 (≥ 3 A for the 15 V / 3 A contract) | 1–2 | — | e-marking need not stated (UNKNOWN) |
| **Board L programming** | | | |
| Genuine ST-LINK/V2 with 20-pin ribbon | 1 | [SWD] (UM1075 CN3 pinout). Clones are not covered | UNKNOWN whether owned |
| SWD adapter PCB (`products/led-lamp/boards/swd-adapter/`, J1 DS254P-2X10, J2 PZ254V-11-05P) | 1 | Ordered in the 2026-09-19 release with JLCPCB-soldered connectors | Receipt and condition not recorded (UNKNOWN); needs continuity, pin-19 isolation and VAPP-GND checks |
| Straight pin-for-pin 1×5 female-to-female cable, adapter J2 → Board L J3 | 1 | [SWD]: unkeyed; align the pin-1 marks | — |
| Board L J3 1×5 header | 1 per board | Requested JLCPCB-soldered in the 2026-09-19 release (override of hand-fit) | Fitted state on received boards: inspect |
| Programming/readback software for the ST-LINK (option-byte read, flash write, raw readback) | 1 | **Not specified in the repo** | UNKNOWN; owner choice |
| Firmware image | 1 | Each build writes `firmware/board-l/target/build/board-l-skeleton.receipt.json`; the 2026-11-20 candidate is recorded in [the committed receipt](https://github.com/Takazudo/zudo-pd/blob/main/products/led-lamp/firmware/board-l/receipts/2026-11-20-unflashed-bench-candidate.md) (`.bin` `421e5b6d…2a9e`, 10908 B; no image committed) | UNFLASHED BENCH CANDIDATE; rebuild cleanly at the session commit ([CHK] §4) |
| **Board L first energizing** | | | |
| Current-limited bench supply into J2.1/J2.2 (VBUS_L) and J2.5/J2.6 (GND), in place of P15 | 1 | [CHK] §2 | Fixture **not defined** in the repo (owner) |
| Optional NRST hold (J3.3 to GND, or probe connect-under-reset) | — | [CHK] §2 | Optional |
| **Instruments** | | | |
| Four-wire (Kelvin) milliohm meter for RS1 | 1 | [CHK] 1.1 | Record instrument identity and date |
| DMM | 1 | [CHK] §1–2, sheets | — |
| Oscilloscope: ≥ 2 channels, ≥ 1 s capture at ≥ 10 kS/s for TP1 and V3P3; also LED_N/coil ripple, the 20 kHz carrier and I2C rise time | 1 | [SHEETS] B, C; [PD-PROG] P15-NVM-2 | — |
| Thermocouples TC1–TC4 and reader (hottest LED joint, RT1, U2, RS1) | 4 | [SHEETS] T | — |
| **Enclosure, per lamp** | | | |
| Printed parts: 7 shell, 8 spacers, 3 posts, 3 feet | 21 | `products/led-lamp/doc/public/assets/enclosure/smoke-reversing-stls.zip` (`d2ee9e0b…`); valid for P15 (see [print inputs](https://github.com/Takazudo/zudo-pd/blob/main/products/led-lamp/candidates/p15-r1-enclosure-fit/PRINT-INPUTS.md)) | Not printed |
| Fitting coupons: square post, square holes 4.0/4.2/4.4, pin 2.4, socket clearance 0.2/0.4/0.6 | 8 (one set) | Same ZIP; print first | `_3dp/*.3mf` lack 7 of the 8 coupons |
| Filament: PETG (clear, amber, teal, smoke as desired); TPU optional for feet | — | [ENC] | — |
| M3 × ~25 mm nylon screws | 5 | [ENC] step 4 | Lengths to verify against real hardware |
| M3 × 14 mm nylon screw (Board P independent hole) | 1 | [ENC] step 4 | — |
| M3 nylon nuts | 6 | [ENC] step 4 | — |

## 2. Post-arrival sequence

This order follows the owner actions in [STATE]. Each row links its procedure. Stop on any out-of-limit reading.

1. **P15 incoming inspection** (per unit, 2 units)
   - Check identity, polarity of D5/D9 and other polarized parts, and the connectors.
   - Before any NVM work, keep Board L and Board B disconnected throughout.
   - Procedure: [PD-PROG] section "One common Board P", [MFG] owner checks.
2. **P15 provisioning on a 5 V-only source.** Follow [PD-PROG] steps 1–8:
   1. Check VBUS_IN and VREG_2V7.
   2. Enable the jig rail, then clip on (P15-NVM-1/2).
   3. Dump the 40 bytes with their hash (P15-NVM-3).
   4. Write `stusb4500-15v.bin` (`76622e14…`).
   5. Do the immediate readback.
3. **P15 full power cycle and readback**
   - Remove the jig rail first. Remove VBUS until J3.3 reads &lt; 0.1 V.
   - Re-apply 5 V and wait ≥ 30 ms.
   - Do the readback: an exact hash match (P15-NVM-4), then PDO registers 0x85–0x90 show 2 PDOs, PDO2 = 15 V / 3 A
     (P15-NVM-5).
   - Check VDD ≥ 4.1 V at 4.75 V input (P15-NVM-7).
4. **P15 PD acceptance with no load** ([PD-PROG] step 9, P15-NVM-6)
   - Use a 20 V-capable source through a current-limited path.
   - VBUS_OUT must stay off during the 5 V phase, then follow 15 V after the 15 V contract. This is the only evidence
     for the POWER_ONLY_ABOVE_5V bit.
5. **Board L identity and unpowered checks** ([CHK] §1; [SHEETS] header)
   - Record the board serial or marking and its photos.
   - Check SW2 OFF and the J3 order: 1 SWDIO, 2 SWCLK, 3 NRST, 4 V3P3 sense, 5 GND.
   - Check TP1–GND ≈ 33 kΩ, and that R20, R21 and C21 are fitted.
   - Check V15 and V3P3 for shorts.
6. **RS1 Kelvin measurement** ([CHK] 1.1–1.2)
   - Measure four-wire across the RS1 pads. Expect 200 mΩ ±1 %.
   - Record the instrument and date.
   - Any other value is a stop; do not change the ceiling.
7. **First energizing, MCU blank** (permission; [CHK] §2, [SHEETS] B1–B2)
   - Use the current-limited bench source, not P15.
   - Connect a scope to TP1 before SW2 ON, and decide within 1 s. Abort if TP1 > 0.2 V or any light appears.
   - Take rail readings 2.1–2.6.
8. **Option-byte readback, read-only first** ([CHK] §3, [SHEETS] O1–O3)
   - Read FLASH_OPTR at 0x40022020 under reset, save it, and decode it.
   - Writing the target values (O4–O8: write, OBL_LAUNCH, power-cycle readbacks, boot with PA14 floating) is a
     separate permission.
9. **Firmware identity** ([CHK] §4, [SHEETS] F)
   - Do a clean build at a clean commit. The receipt must show `firmware_dirty` false, `matches_pin` true and
     `adopted_default` true (2407).
   - Retain the ELF and receipt.
   - Any authorized readback must match `loadable_image_sha256` over `[0x08000000, +loadable_image_bytes)`.
   - The owner first decides the open first-image behaviour: D1 noise and D2 gamma (recommendation: steady,
     linear), plus D3 values (`target/OPEN-PRODUCT-DECISIONS.md`).
10. **Startup, current and thermal** (permission; [CHK] §5–6, [SHEETS] B4–B9, K, C, N, T)
    - Check TP1 before the ramp, about 1.90 V at maximum, the RS1 drop ≤ 80 mV, and each branch ≤ 81 mA mean.
    - Measure the ripple h and the pulse-skip floor.
    - Do the NTC correlation and the OFF-path and reset-latch checks.
    - The 200 mΩ derate-onset temperature is not computed (UNKNOWN). 76 °C is the 250 mΩ figure.
11. **Mate an accepted P15 with a passing Board L** ([STATE] action 6)
    - Align JOUT1 to J2 (unkeyed; verify the orientation).
    - Record the contract voltage, ATT/PDOK and the input current.
    - The firmware does not read PDOK/ATT.
12. **Enclosure fit** ([ENC]; [STATE] action 7)
    1. Print the coupons first and choose `--post-clearance` and `socket_diameter`.
    2. Dry-fit the boards.
    3. Measure the seated JOUT1↔J2 gap against the 11 mm nominal.
    4. Check USB plug seating, wheel and slider access, retention, appearance and powered temperatures (sheet T2/T4).
    - CAD clearance is nominal only. Physical fit is NOT RUN.

## Genuine unknowns

- Whether the owner already has the ST-LINK/V2, NUCLEO and pogo clip, and the state of the received SWD adapter.
- The ST-LINK host software.
- The exact 5 V-only source and 20 V PD test source, and the current-limited path device.
- The current-limited bench-supply fixture for Board L J2.
- The P15 cable rating or e-marking need.
- The number of lamps to enclose.
- The 200 mΩ derate-onset temperature.
- Board L factory programming state and RS1 marking.
- Whether J3 is fitted on the received boards.
- The P15 order status, cost and stock.
