# Board L firmware: V72 source inventory and gap to product firmware

**State: portable C continuation exists outside Git; it is NOT target-linked, NOT
flashed, and NOT a firmware release.** Repository `main` has no `firmware/`
directory, and `board-l.mdx` states "this repository has no executable control firmware".
Nothing was rewritten or built in this phase.

## Where it is

Handoff supplemental archive `LED-source-evidence-cloud-handoff.zip` (4,659,867 B,
SHA256 `e85faff85af2128f0fdc4cfefcc5703e4d1d798d1e10388aa79b47d1f33c2e47`), at
`packets/v72-codex-knob-averaging-20261025/source/` (64 files, about 2,760 lines of C).
Earlier states are in V68 (input/app composition), V70 (disabled ADC operation config)
and V71 (latched policy / response budget), each with its failure history kept.
Imported unchanged into [`firmware/board-l/src/`](../firmware/board-l/README.md) on 2026-10-31.

## Modules present

| Area | Files | What it is |
| --- | --- | --- |
| Lamp control core | `lamp_control.c/h`, `lamp_app.c/h` | Pure state machine: RESET_OFF → WAIT_VALID → RAMP/READY. Any invalid, stale, thermal-denied or unconfigured input forces command 0. LATCH or AUTO recovery mode; knob zero is not recovery |
| Knob input | `sample_adapter.c/h` (V72 change), `input_conversion`, `normalized_transfer` | Calibrated endpoint/inversion/clamp; mandatory `knob_window` 1..32 moving mean; no production window chosen |
| Thermal | `thermal_gain.c/h` | Integer gain applied to the command; thermal invalidity is immediate and never averaged. No NTC curve/threshold calibration |
| ADC acquisition | `acquisition_*`, `adc_*`, `discontinuous_acquisition`, `completed_frame_bridge`, `stm32g031_adc_transport` | Abstract ADC frame/ownership contracts; the STM32G031 transport is "source candidate only, never executed" |
| PWM / CTRL output | `tim3_access`, `tim3_preload`, `tim3_readiness`, `tim3_profile`, `tim3_fixed_volatile.c`, `ctrl_timer_map`, `output_composition`, `host_timer_output` | TIM3 CCR1 write seam. Its fixed-address TU (0x40000434) is target-only and never linked. A completed store is not a pin-OFF proof |
| Board binding | `board_binding.c/h`, `board_l_io.h` | Project connectivity map; explicitly not a verified peripheral mapping |
| Noise / animation | `noise_stage.c/h` | Random modulation stage |
| Tests | `test_input_app.c` (host) | The only `main()` in the tree |

## Recorded verification (not re-run here)

- Host tests: host-attempt4 **PASS 44**, exit 0, `target_execution: false`. Attempts
  1–3 (one compile failure, one wrong assertion, 42 passes) were kept.
- Cortex-M0+ object-only compile of 4 changed objects (`-mcpu=cortex-m0plus -mthumb`),
  exit 0. No link, no run, no MMIO.
- Archived binaries/objects must not be executed. The toolchain is not in the cloud
  image.

## Not present: needed for product firmware

| Need | Status in V72 | Note |
| --- | --- | --- |
| Startup code, vector table, linker script, `main`, clock tree (64 MHz intent), build system | **Absent** | Required before anything can be linked or flashed |
| Safe PWM startup | Core starts at command 0 and ramps only after valid knob+thermal. No GPIO/TIM3 init sequence sets CTRL to a defined low before timer enable | Must keep the hardware default-OFF (CTRL pull-down) as the primary guarantee; firmware adds ordering: pin analog/low → timer configured at 0 % → enable → ramp |
| Thermal control | Gain hook plus latch only | Needs an NTC (NCP18XH103) curve, ADC code thresholds from `board-l.mdx`, a derating policy, and a sensor open/short fault decision |
| Current control / #52 | None (no current sensing on Board L) | A firmware duty ceiling is a mitigation only if CTRL behaves as filtered analog. Peak current at full CTRL is set by hardware |
| Calibration | Knob endpoint calibration structure only | Storage (flash/option bytes), the procedure and per-unit values are undefined |
| Fault handling | Sensor faults latch until explicit qualified reinit; I/O faults hold | Brownout/BOR level, watchdog, reset-cause handling, and PA5/PA7 as analog/unused per the #145 B-plan are not implemented |
| ADC cadence, knob window N, ramp increment | Not chosen | Engineering choices, to be recomputed against the response budget in V71 |
| Programming state of the two delivered Board Ls | Unknown | User reported no personal programming. Factory programming and option bytes (#46 boot mode) are not established. SWD was never reachable because Board P never switched on (#144) |

Recommended next step (not started): import the V72 source tree as-is into
`firmware/` with provenance, then add the minimal target skeleton (startup, linker,
clock, GPIO/TIM3 safe init) as a reviewed change. Physical flashing stays a separate
permission.
