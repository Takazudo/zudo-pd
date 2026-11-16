# Board L: checklist before any programming or energizing

**Status:** PROCEDURE ONLY. Nothing here has been executed, and nothing here gives
permission. Programming a Board L, including its option bytes, needs the owner's explicit
permission. Energizing a Board L needs the same.

Record every reading with the board serial, date, instrument and firmware commit, on the
matching sheet in [BENCH-TEST-SHEETS.md](BENCH-TEST-SHEETS.md).

A reading outside its expectation is a **stop** condition: power down, record it, and do
not continue.

Pin and net names are from `scripts/schgen/board_l_spec.py`. Firmware values are from
`target/board_l_proposal.h`. The current analysis is in
`candidates/board-l-led-margin-52/ANALYSIS.md`.

## 0. Programming energizes the LED driver

- The ST-LINK/V2 adapter only senses target voltage on J3.4. Board L must supply its own
  3.3 V ([SWD adapter](../../doc/src/content/docs/architecture/swd-adapter.mdx)).
- V3P3 comes from U4 (AP63203), which runs from V15. So programming needs V15 present.
  V15 also powers U2 (AL8860) and the LED array.
- What holds CTRL low on a blank or unprogrammed MCU is **R21 (33 kΩ) with PA6 in its
  reset state**. Section 0.1 gives the state table and the sources. This is a datasheet
  check, not a measurement: it does not prove that CTRL never glitches during supply ramp,
  brown-out, a fault or a corrupted image. Check 2.3 still measures TP1 on every board.
- **Correction (2026-11-04 review, R5).** An earlier version of this checklist said a
  blank STM32G0 bootloader might enable SPI1 on PA4–PA7 and drive CTRL through PA6 (MISO).
  That hypothesis is **withdrawn**. For the exact STM32G03xxx/G04xxx bootloader, AN2606
  Rev 71 Table 106 lists USART1, USART2, I2C1 and I2C2 only, with no SPI (verified from a
  text extraction, section 0.1). PA4 (NTC_SENSE, about 0.30 V) is therefore not an SPI chip select either.

### 0.1 CTRL (PA6) state from reset to firmware start

Sources (exact part STM32G031F8P6, `component-stm32g031f8p6`):

| Ref | Document | Locator | Retention in this repo |
| --- | --- | --- | --- |
| [AN2606] | ST AN2606 *Introduction to system memory boot mode on STM32 MCUs*, **Rev 71** (page footer "November 2026 AN2606 Rev 71 1/584") | §47 STM32G03xxx/STM32G04xxx: §47.1 Table 106 "STM32G03xxx/G04xxx configuration in system memory boot mode", pp. 256–257; §47.3 Table 107 bootloader versions, p. 258 | **Text extraction only, not the PDF bytes.** Verified directly against a plain-text extraction of the PDF uploaded by the owner on 2026-11-03: `an2606-rev71-extracted.txt`, 918,954 bytes, SHA256 `b1598663b4da310e2479efd1b9e55640f8eedb662c343e79a6bb46e0845a7947` as received. The extraction is not retained in this repository and its hash is not a PDF hash. The 2026-11-04 review's PDF of the same revision, fetched from `https://www.st.com.cn/resource/en/application_note/an2606-introduction-to-system-memory-boot-mode-on-stm32-mcus-stmicroelectronics.pdf`, had SHA256 `dd8e48f0ae32ae3fb168d9d8da72092714289b9e410d2fcb5964b10dfc86396a`; those PDF bytes were not re-downloaded here (st.com refused both the cloud container and the local proxy) |
| [RM0444] | ST RM0444 *STM32G0x1 advanced Arm-based 32-bit MCUs*, **Rev 6** (cover "December 2024"; revision history 09-Dec-2024; PDF CreationDate 2024-12-09) | §7.5.1 GPIO port mode register (GPIOx_MODER), pp. 238–239: "Reset value: 0xEBFF FFFF (port A)"; MODE6[1:0] at bits 13:12; "11: Analog mode (reset state)" | **PDF bytes read** (not compared with a hash published by ST). Uploaded by the owner on 2026-11-03 as `rm0444.pdf.zip` (7,125,914 bytes, SHA256 `a5b2bd9bb005664046b41ce64203e284cb45568b3119a8729259a63994f3892f`), containing `rm0444-stm32g0x1-advanced-armbased-32bit-mcus-stmicroelectronics.pdf` (17,180,597 bytes, 1384 pages, SHA256 `0b9146260790b48735631e7735c60c42b900415c7b519ee7623c10e3d96faec3`). The PDF is not stored in this repository. Also consistent with ST's CMSIS-SVD `STM32G031.svd` v1.6 (`modm-io/cmsis-svd-stm32@e79021ac`, SHA256 `382bc7d42fae87578b64db7a07afe69a9d07319389a9d4250699e19144d31329`): `GPIOA.MODER resetValue 0xEBFFFFFF` |

Evidence status: the RM0444 rows rest on the original PDF bytes (hash above). The AN2606
rows rest on a text extraction of Rev 71, not on PDF bytes. The component owner record
`src-c529334-rm` in `.claude/skills/component-stm32g031f8p6/sources.json` still reads
SOURCE UNAVAILABLE; updating it is a separate component-spec-audit change and is not
claimed here.

| Phase | PA6 state | Who holds CTRL | Basis |
| --- | --- | --- | --- |
| V3P3 rising, before POR release | Not specified here | R21 to GND, C21 | No register is valid yet. [DS] power-on behaviour is not retained: **unverified** |
| NRST held low (pin reset, debugger connect-under-reset) | Reset state: MODE6 = 11, Analog. Output driver and input buffer off | R21 | [RM0444] GPIOA_MODER reset value |
| Reset released, **blank flash** (empty check selects system memory, Pattern 11) | Bootloader runs. Table 106 lists only RCC (HSI), RAM, system memory, IWDG, USART1, USART2, I2C1 and I2C2; no SPI. PA6 is not a bootloader pin, so it stays in its reset state | R21 | [AN2606] Table 106 |
| Reset released, **target image**, first instructions of `Reset_Handler` | Analog until `board_ctrl_force_off()` sets PA6 to push-pull output low; this runs before RAM init (`target/startup_stm32g031.c`) | R21, then PA6 low | Source code |
| `main()` until the ramp | PA6 output low; handed to TIM3_CH1 (AF1) only after CCR = 0 is loaded (`target/board_ctrl.c`) | PA6 low, then TIM3 at CCR 0 | Source code; host tests in `target/test/` |
| Option bytes **unprogrammed** with a target image | Firmware refuses light (BOR gate, section 3.5), so PA6 stays low | PA6 low | Source code and `boot policy` host test |
| Debugger halt, development build | TIM3 keeps its last CCR (at most `CTRL_FULL_CCR`) | TIM3 | Source code (section 6.3) |

Bootloader pins on this TSSOP20 part, from Table 106 and its note ("On SO8, WLCSP18,
TSSOP20, and UFQFN28 packages USART1 PA9/PA10 IOs are remapped on PA11/PA12"), checked
against `pinmap-c529334` and `scripts/schgen/board_l_spec.py`:

| Bootloader signal | Pin (TSSOP20 pad) | Board L net | Effect on CTRL |
| --- | --- | --- | --- |
| USART1_TX / RX | PA11 / PA12 (16 / 17), remapped | Unused, no-connect | None |
| USART2_TX / RX | PA2 / PA3 (9 / 10) | UART_TX / UART_RX, J4 pads | None. Alternate push-pull with pull-up |
| I2C1_SCL / SDA | PB6 (20, shared bond) / PB7 (1, shared bond) | Unused, no-connect | None |
| I2C2_SCL / SDA | PB10 / PB11 | Not bonded on TSSOP20 (absent from `pinmap-c529334`) | None |
| — | PA6 (13) | PWM_DIM → R20 → CTRL | Not configured by the bootloader |

Table 107 notes that bootloader V5.2 can stay in the USART2 detection loop if PA3 is held
low. On Board L, PA3 is the J4 UART_RX pad with the bootloader's own pull-up; this
affects only bootloader detection, not CTRL. Record the version read in sheet B3.

What this table does **not** cover, and what must be measured instead (sheet B in
[BENCH-TEST-SHEETS.md](BENCH-TEST-SHEETS.md)):

- The CTRL waveform during V3P3 ramp and brown-out.
- The bootloader version and its behaviour on these two parts.
- A corrupted or foreign image already in flash. The two Board Ls are believed blank
  (owner answer 2026-10-31), but their factory state is not recorded.
- Treat the first power-up as **not yet measured**, not as known safe. Section 2 keeps the
  current limit, the TP1 watch and the abort rule.
- At full CTRL on an RS1 = 200 mΩ board, the #52 worst-case hot branch is 88.6–96.9 mA, which
  can exceed the 90 mA LED absolute maximum. Check 1.1 therefore comes first.
- A halted core in a **development** build keeps TIM3 running at its last duty (at most the
  ceiling) while the IWDG is frozen and nothing supervises temperature. Keep debug halts short
  while the LEDs are lit.
- Back-feeding V3P3 from a bench supply with V15 absent has **not been evaluated**. Do not
  use it as a "safe" programming mode without a separate review.

## 1. Unpowered checks (no source connected, SW2 OFF)

| # | Check | Expect | Why |
| --- | --- | --- | --- |
| 1.1 | Read the RS1 value **by 4-wire (Kelvin) resistance** across the RS1 pads. The marking code is not in the retained evidence, so do not rely on it or a photograph. Record board identity, instrument/date and measured resistance in the bench header | 200 mΩ ±1 % as built (RLP25FEER200), or 250 mΩ if reworked (RLP25FEER250) | Selects the duty ceiling, below |
| 1.2 | Confirm the firmware ceiling matches 1.1 | 200 mΩ requires `CTRL_FULL_CCR` 2407, the default. 3200 is allowed **only** if 1.1 measured 250 mΩ and the owner approved it | #52: the default keeps the hot branch ≤ 81 mA at h = 30 % and ballast ±2 % (typical CTRL transfer only) |
| 1.3 | Resistance TP1 (CTRL) to GND | About 33 kΩ (R21), possibly lower through R20 into the unpowered PA6 | The pull-down that holds CTRL OFF is present |
| 1.4 | R20 10 kΩ, R21 33 kΩ, C21 present (visual, plus 1.3) | Fitted | The CTRL filter and OFF path |
| 1.5 | V15 to GND, V3P3 to GND | No short | First power |
| 1.6 | J3 order: 1 SWDIO, 2 SWCLK, 3 NRST, 4 V3P3 (sense), 5 GND. Align the pin-1 marks at both ends | As listed | Unkeyed headers |
| 1.7 | SW2 position | OFF | No input path before the source is connected |

## 2. First energizing, MCU blank or not yet programmed (only with permission)

The datasheet state is CTRL low (section 0.1), but it is not yet measured. Before SW2 ON:

- **1.1 must be done.** RS1 measured as 200 mΩ means the worst case can exceed the LED
  absolute maximum, so keep the exposure short by procedure.
- **Limit the source:**
  - if the owner's fixture allows a current-limited bench source in place of Board P
    (VBUS_L on J2.1/J2.2, GND on J2.5/J2.6), set a limit well below the full-load input
    current;
  - no such fixture is defined in this repository, so this choice belongs to the owner.
  - when Board P is used instead, it is a zudo-pd P15 r1 whose NVM has passed
    P15-NVM-4/5 on a 5 V-only source and P15-NVM-6 with no load, **before** it mates with
    Board L ([current path](../../candidates/README.md#current-path-p15-r1--the-two-existing-board-ls)).
    P15 has no hardware voltage window and no current limit toward Board L, so the first
    energizing of each Board L should still use the current-limited bench source.
- **Optional mitigation:** hold NRST low (J3.3 to GND, or the probe's connect-under-reset)
  while switching on. Per [RM0444], PA6 is then in Analog mode and R21 holds CTRL. The
  bootloader cannot run while NRST is held. This removes the bootloader phase from the
  first observation; it does not cover the supply ramp before POR.
- **Watch TP1 on a scope or meter** that is already connected at SW2 ON. Decide within
  **1 s**.
- **Abort:** if TP1 > 0.2 V, any LED lights or the RS1 drop rises, set SW2 OFF at once and
  record it. Do not program that board until the cause is understood.

Then measure:

| # | Point | Expect | Stop if |
| --- | --- | --- | --- |
| 2.1 | V15 (C10) | Within the rail's input range | Out of range |
| 2.2 | V3P3 (C16/C17) | About 3.3 V | Outside 3.27–3.33 V. That is the analysis range, so outside it the CTRL numbers no longer hold |
| 2.3 | TP1 (CTRL), measured first, within 1 s | About 0 V | **> 0.2 V**, the typical AL8860 off threshold, which is not guaranteed: SW2 OFF immediately |
| 2.4 | RS1 drop (V15 − SET) | About 0 mV, no LED current | Any visible light, or a measurable drop |
| 2.5 | NTC_SENSE (C24) | About 0.30 V at 25 °C (board-l.mdx) | Near 0 V (short) or near 3.3 V (open) |
| 2.6 | BRIGHT_ADC (C22) across the knob range | Follows the knob, 0 to about 3.2 V (R22 loads the wiper) | Stuck |

## 3. Option-byte readback plan (read before any write)

1. With the probe attached (connect under reset, NRST on J3.3), **read only**
   FLASH_OPTR at 0x40022020. Save the raw 32-bit value and the probe log.
2. Decode the fields (ST `stm32g031xx.h`):

   | Field | Bits | Proposed target |
   | --- | --- | --- |
   | RDP | 7:0 | 0xAA, Level 0. Never Level 2 |
   | BOR_EN | 8 | 1 |
   | BORR_LEV | 10:9 | 3 |
   | BORF_LEV | 12:11 | 3 |
   | IWDG_SW | 16 | 1 in development, 0 in production |
   | WWDG_SW | 19 | 1 |
   | nBOOT_SEL / nBOOT1 / nBOOT0 | 24 / 25 / 26 | 1 / 1 / 1 |
   | NRST_MODE | 28:27 | 3 |
   | Others | — | Unchanged from step 1 |

3. Only with explicit permission, write the target values. Then read FLASH_OPTR back:
   - after programming;
   - after OBL_LAUNCH;
   - after a full power cycle.

   All three readbacks must match the target value.
4. Check that the board boots from main flash with PA14 floating, and again with the probe
   attached. This is the #46 acceptance (owner skill `cov-c529334-options`).
5. The firmware refuses all light unless BOR_EN = 1 and both BOR levels are 3. With
   unprogrammed option bytes, a programmed image must therefore keep TP1 at about 0 V.
   `g_boot_decision.refusals` should then contain 0x2 (BOR disabled) and/or 0x4 (BOR level).
   Use this as a check of the gate itself.

## 4. Image identity (before writing flash)

Record:

- the git commit;
- the `make` size output;
- the SHA256 of `build/board-l-skeleton.elf`;
- the `CTRL_FULL_CCR` value used, which must agree with check 1.2;
- whether `BOARD_L_PRODUCTION` was defined.

`make` writes all of these to `build/board-l-skeleton.receipt.json`. Keep that file with the
session record. Stop if source revision/dirty-state identity is unavailable,
`source.firmware_dirty` is true, `toolchain.matches_pin` is
false, or `ctrl_ceiling.adopted_default` is false on an RS1 = 200 mΩ board. Build from a
clean `make clean && make`, not from a reused build directory.

For a separately authorized firmware readback, retain the receipt and the exact ELF
and its SHA256. Compare the **raw binary flash image**, in the same representation as
`objcopy -O binary` used by `target/tools/build_receipt.py`, with
`artifacts.loadable_image_sha256`. Read exactly `artifacts.loadable_image_bytes` bytes.
Confirm the start address from that ELF's load addresses and linker inputs:
`target/stm32g031f8_flash.ld` currently places FLASH at `0x08000000`, including the
flash load image for `.data`. Record the range as start-inclusive/end-exclusive:
`[0x08000000, 0x08000000 + artifacts.loadable_image_bytes)` for this layout.
Stop if the ELF/layout does not support that range; do not assume the address for a
different image. Preserve binary padding/gaps exactly as represented by objcopy.

Record expected hash/length/range and the actual readback artifact, byte length,
SHA256 and comparison outcome in bench sheet F. Option-byte readbacks belong
separately in sheet O. The receipt-file hash and whole ELF-file hash are **not**
raw-flash comparison hashes; an arbitrarily sized full-flash dump is not the image.
This defines identity evidence only: no programming or readback is authorized here,
and physical results remain NOT EXECUTED until separately performed.

Production builds do not freeze the IWDG under the debugger.

## 5. First run with the image (only with permission). Measure, do not tune

| # | Point | Expect (nominal, typical AL8860 transfer) | Stop if |
| --- | --- | --- | --- |
| 5.1 | TP1 at power-on, before the ramp | About 0 V | > 0.2 V |
| 5.2 | TP1, knob at minimum | 0 V (hard OFF) | — |
| 5.3 | TP1, knob just above the off band | About 0.41 V (CCR 518, the 5 % floor) | — |
| 5.4 | TP1, knob at maximum | About 1.90 V (2407/3200 × 3.3 V × 33/43). The ramp to it takes about 2.5 s | > 1.95 V with the default ceiling |
| 5.5 | RS1 drop at maximum → total mean current | About 76 mV / 200 mΩ ≈ 381 mA (typical) | > 80 mV (0.762 × the 104 mV VSENSE maximum) |
| 5.6 | Each ballast R30–R37 (33 Ω) drop → branch mean | About 1.57 V (≈ 48 mA) | Any branch > 81 mA **mean**. Peak needs 5.7 |
| 5.7 | Coil/LED_N current ripple at minimum and maximum V15 (scope) | Gives the real h, the unpublished VSENSE_HYS | Peak = mean × (1 + h) > 81 mA on the hottest branch |
| 5.8 | Pulse-skip sweep near the floor (LED_N on a scope) | The burst rate | Bursts < ~300 Hz: raise `CTRL_MIN_CCR` (board-l.mdx Gate 4) |
| 5.9 | NTC_SENSE against a thermocouple at the hottest LED solder point | The NTC-to-TS correlation | Derate (code 104) must begin before TS ≈ 76 °C at 250 mΩ, and earlier at 200 mΩ |

## 6. OFF-path checks on the bench

All of these are debugger-observable. Each must end with TP1 at about 0 V.

| # | Action | Expect |
| --- | --- | --- |
| 6.1 | Knob to minimum | OFF; light returns when the knob is raised |
| 6.2 | Open the NTC, e.g. lift RT1 or disconnect it only if a fixture allows | OFF, latched until a reset. **Do not rework the board just for this test without approval** |
| 6.3 | Halt in the debugger, development build | Record TP1. TIM3 is not frozen by this firmware, so CTRL keeps its last duty while halted. The IWDG is frozen in development builds only |
| 6.4 | Three software resets (SYSRESETREQ), each within 10 s of the previous boot | OFF after the third (`g_reset_record.count` = 3); a pin reset keeps it OFF |
| 6.5 | After 6.4, leave it parked ≥ 10 s, then power cycle | Light allowed again (count 0). A power cycle within 10 s may keep the latch while SRAM is retained (duration [DS]): record which happened |
| 6.5a | Software resets spaced > 10 s apart in normal operation | Never latches (the count is consecutive) |
| 6.6 | Stop refreshing the IWDG, e.g. hold a breakpoint in a production build | A reset in about 100 ms. The LSI tolerance is [DS] |

Close by recording which rows ran, which did not, and why.
