# Board L firmware source (V72 import) and build-only target skeleton

This directory holds the **unchanged** V72 portable C sources for the Board L STM32G031F8P6
lamp controller: 64 files in `src/`. They are imported for review and continuation.

- `src/` itself is not a target build. Eight of its units are linked, unchanged, into the
  build-only image in [`target/`](target/README.md); none has been **flashed or run on hardware.**
- No production parameters are chosen in them.
- Provenance is in [`PROVENANCE.md`](PROVENANCE.md).

A separate, earlier bring-up firmware by the owner (2026-10-06, PlatformIO/CMSIS, not V72)
is kept unchanged in [`../board-l-bringup-mac-20261006/`](../board-l-bringup-mac-20261006/PROVENANCE.md).
Its reconciliation table against this firmware is there. It has no duty ceiling, so do not
use it at full knob on RS1 = 200 mΩ boards.

Do not edit files in `src/` in place as a "fix". Changes start a new reviewed revision on
top of this import. Physical programming of the delivered Board Ls is a separate
permission.

## What is here

| Area | Files | Role |
| --- | --- | --- |
| Lamp control core | `lamp_control.*`, `lamp_app.*` | State machine: RESET_OFF → WAIT_VALID → RAMP/READY. Every invalid, stale, thermal-denied or unconfigured input forces command 0. LATCH/AUTO recovery modes |
| Knob input | `sample_adapter.*` (V72 change), `input_conversion.*`, `normalized_transfer.*` | Endpoint/inversion/clamp calibration structure; mandatory `knob_window` 1..32 moving mean |
| Thermal | `thermal_gain.*` | Integer gain on the command; invalid thermal input stops light immediately |
| ADC acquisition | `acquisition_*`, `adc_*`, `discontinuous_acquisition.*`, `completed_frame_bridge.*`, `stm32g031_adc_transport.*` | Abstract frame/ownership contracts; STM32G031 transport is marked "source candidate only, never executed" |
| PWM / CTRL output | `tim3_*`, `ctrl_timer_map.*`, `output_composition.*`, `host_timer_output.*` | TIM3 CCR1 write seam; `tim3_fixed_volatile.c` is target-only MMIO (0x40000434) and has never been linked |
| Board binding | `board_binding.*`, `board_l_io.h` | Project connectivity map, not a verified peripheral mapping |
| Noise / animation | `noise_stage.*` | Random modulation stage |
| Host test | `test_input_app.c` | Only `main()` in the tree; host-only |

## Recorded status (from the packet, not re-run here)

- Host test, host-attempt4: **PASS 44**, exit 0, `target_execution: false`
  (`provenance/host-attempt4-result.json`). Compiled with `cc -std=c11 -O0 -Wall -Wextra
  -Werror -pedantic` (sanitized command in `provenance/`).
- Cortex-M0+ **object-only** compile of 4 changed units (`sample_adapter`,
  `board_binding`, `input_composition`, `output_composition`), exit 0
  (`provenance/m0plus-object-attempt1-result.json`). No link, no run.
- Re-run on 2026-10-31 with `make -C target host-test` (gcc 13.3.0): **PASS 44**, exit 0.
  All 33 non-test units also cross-compile for Cortex-M0+ (`make -C target v72-objects`).

A minimal target skeleton is in [`target/`](target/README.md): vector table, linker script,
clock, safe CTRL init order, `main` and a Makefile. Since phase 4, `main` runs the V72
`lamp_app` through the off-by-default adapter `target/lamp_target.c`, with host tests.
Since phase 5 the ADC sample source, IWDG, reset-cause latch and BOR option gate are in place
too. It builds but has never been flashed or run. Before any bench session, see
[`BEFORE-PROGRAMMING-CHECKLIST.md`](BEFORE-PROGRAMMING-CHECKLIST.md).

## Missing for a target build

Rows marked *(skeleton)* have a first build-only version in `target/`; none is verified on hardware.

| Missing | Why it matters |
| --- | --- |
| *(skeleton)* Startup code and vector table (`Reset_Handler`, default handlers) | Nothing executes on the MCU without it |
| *(skeleton)* Linker script for STM32G031F8 (64 KB flash / 8 KB SRAM) | Required to link |
| *(skeleton)* `main()` / scheduler / tick source for the target | Only the host test has a `main` |
| *(skeleton)* Clock tree configuration (64 MHz intent) | Timer, ADC and PWM timing depend on it |
| *(skeleton)* GPIO configuration, including the ordered safe init: CTRL pin defined low → TIM3 configured at 0 % → enable → ramp | Hardware CTRL pull-down stays the primary OFF guarantee; firmware must not glitch it |
| PA5/PA7 as analog/unused (#145 B-plan); PA15 never an output (shares a pin with SWCLK/BOOT0) | Board P V196/V198 leaves JOUT1.3/.4 NC |
| *(skeleton)* ADC peripheral bring-up and the chosen ADC cadence | `target/board_adc.c` is one scan per 1 kHz tick into V72 `sample_adapter`. It is unexecuted. V72 `stm32g031_adc_transport.c` is not used |
| *(proposed)* Chosen `knob_window`, ramp increment and response budget | Proposed: window 8 (max age 7 ticks, so all 8 samples count), about 2.5 s ramp. Not approved |
| *(proposed)* NTC (NCP18XH103) code-to-temperature table and derating/shutdown thresholds | `target/board_samples.c`: codes 104 → 69, open ≥ 3500. The NTC-to-TS correlation is unmeasured |
| Calibration storage and procedure (knob endpoints) | Not defined |
| *(skeleton)* Fault policy: BOR level, watchdog, reset-cause handling, sensor-fault reinit conditions | `target/board_policy.c`, `board_iwdg.c`: IWDG about 100 ms, a 3-reset latch, a BOR option gate. A sensor fault latches until reset |
| Option bytes / boot mode (`nBOOT_SEL`, #46) | Determines whether the programmed image boots. The firmware only reads them. Writing them is a bench step: `BEFORE-PROGRAMMING-CHECKLIST.md` |
| *(skeleton)* Build system (Makefile with header and configuration tracking, build receipt), pinned arm-none-eabi-gcc 13.2.1, CI host tests and a build-only target job | Reproducibility. Each image is an unflashed bench candidate identified by `target/build/board-l-skeleton.receipt.json` |
| *(proposed)* #52 peak-current mitigation | CTRL is filtered-analog. Single `CTRL_FULL_CCR`, default 2407 (75.2 %) for RS1 = 200 mΩ; the RS1 = 250 mΩ change is recommended |
