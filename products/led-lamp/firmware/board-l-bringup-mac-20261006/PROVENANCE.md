# Recovered Board L bring-up firmware (2026-10-06), imported unchanged

**Status:** historical evidence of the owner's intent. It is not the project firmware,
not reviewed, and not evidence that any Board L was programmed.

## Origin

- Source: the owner's Mac, `~/repos/circuits/zudo-led-lamp/firmware/`. The files were
  untracked and never committed. Repository HEAD there was `main` 1fc399e2.
- File mtimes: 2026-10-06 03:37–03:40.
- The project manager transcribed them read-only on 2026-10-31.
- They were imported here on 2026-10-31 by a byte copy. `SHA256SUMS` equals the
  manager's PROVENANCE record:

| File | Bytes | SHA256 |
| --- | ---: | --- |
| `platformio.ini` | 157 | 6af145abada218c083fb59669d613c686eaa212bed6c144af3eadbcaa090d535 |
| `boards/zudo_led_lamp_g031f8.json` | 670 | a76b2d530790b2b4bc974442a543a0ea07694c67d2509c279e317a66ad631e7c |
| `src/main.c` | 10004 | 5a152126b5f3633ca696bec1c2743f746f4bc2c9bc45e736c199ae80515d32cc |

Verify with `sha256sum -c SHA256SUMS` from this directory. **Do not edit these three
files.** Corrections belong in `firmware/board-l/`.

## Not recovered byte-exact

- The original `README.md`: 2137 B, SHA256 580b4272…. Only a summary exists, in the
  manager log.
- The original `.gitignore`.
- The PlatformIO build outputs: `.pio/…/firmware.bin` (2076 B, dddf3ea2…) and
  `firmware.elf` (d88222e6…).

These build outputs are deliberately **not** imported. Their existence does **not** show
that any board was flashed, and the programming state of the delivered boards is
unestablished.

## What was checked here

- A compile-only check passed: arm-none-eabi-gcc 13.2.1 with `-Os -Wall -Wextra` and the
  pinned ST `cmsis_device_g0` @7c77b7c headers produced no warnings, and `main.o` has
  1359 B of text.
- PlatformIO itself was not run, and nothing was linked, executed or flashed.

## Reconciliation with `firmware/board-l` (V72 + target layer)

| Item | This bring-up | Project firmware / proposal | Result |
| --- | --- | --- | --- |
| CTRL carrier | TIM3_CH1 on PA6 (AF1), PSC 0, ARR 3199, PWM mode 1, CC1P 0 | Same (`board_l_proposal.h`) | Agrees |
| CTRL nature | Into the R20/R21/C21 RC filter, so filtered-analog | Same (#52 `ANALYSIS.md` §1) | Agrees, by design |
| Floor | `DUTY_FLOOR_Q16` 10617, which is CCR 518 (16.2 %, 0.41 V, about 5 %) | `CTRL_MIN_CCR` 518 | Agrees |
| Full scale | `DUTY_FULL_Q16` 65535, which is CCR 3199 (≈100 %, 2.53 V), with **no ceiling** | CCR 2656 (83 %) while RS1 = 200 mΩ | **Differs.** At 200 mΩ the bring-up reaches the #52 worst-case hot-branch peak of 88.6 mA (h = 20 %) or 96.9 mA (h = 30 %), which is above the 90 mA LED absolute maximum |
| Ramp | 2 perceptual steps per 20 ms frame, about 2.5 s from 0 to 255 | Was 1 s; **now about 2.5 s** (`LAMP_RAMP_INCREMENT` 26) | Aligned on time. The bring-up ramps before gamma, V72 ramps the command |
| Gamma | 2.2 LUT (also in `board-l.mdx`) | V72 `normalized_transfer` has no default gamma | Owner precedent for a later default; not adopted here |
| Knob off | Perceptual ≤ 2 → 0 (hard off); calibration 60..4000 is placeholder | V72 knob zero → OFF (tested) | Agrees in intent. Codes need bench calibration |
| Thermal | NTC codes 104 (≈65 °C) → 69 (≈80 °C) linear derate; ≤ 69 or ≥ 3500 (open) means immediate OFF | V72 `thermal_gain`; invalid thermal → OFF (tested). The sample port is not wired yet | Agrees in intent. The bring-up has no plausibility check beyond open/short |
| PDOK / ATT | Read and printed, **not gating** | Not wired | Gating policy is open (`board-l.mdx` asks for PD-status checks before ramp) |
| Clock failure | Spins forever in the PLL wait with PA6 still Hi-Z (safe) | Explicit `halt_off()` | Equivalent safe state |
| Watchdog / BOR / option bytes | None; the option bytes are left at whatever is programmed | IWDG, reset-count latch, BOR level 3, nBOOT_SEL=1 (PROPOSAL) | **Differs.** The bring-up is not a production policy |
| UART | USART2 PA2/PA3, 115200 8N1, 5 Hz status | Not present | Useful bench diagnostic; candidate to port |
| Startup | PA6 Hi-Z until TIM3 is at 0 %, then AF | `pwm_init_zero` before AF, OFF by default | Agrees |
