# Open product decisions for the Board L target image

**Status:** OPEN. These are owner decisions. The current image takes the most conservative
choice for each one, listed as "Current image". Nothing here is approved product behaviour,
and none of it is measured. The options and recommendations are inputs to the owner's
decision, not a selection.

Already decided, and not reopened here: RS1 stays 200 mΩ and `CTRL_FULL_CCR` stays 2407
(75.2 %). The 250 mΩ alternative and a 3200 ceiling are not selected; the Makefile refuses a
non-default ceiling unless `ACCEPT_NONDEFAULT_CAP=1` is set (see `README.md`).

## D1. Noise (animation) configuration: currently NULL

`main.c` calls `lamp_app_initialize_with_thermal_gain(..., NULL, &gain)`. The NULL is the
V72 noise configuration, so the stage is disabled and the output is the steady knob level.
V72 `noise_stage` has no RNG, seed or physical defaults (`../src/noise_stage.h`); a noise
source (`struct noise_source`) does not exist in the target layer.

| Option | What it takes | Risk |
| --- | --- | --- |
| A. Keep NULL (steady light) | Nothing | None added; the lamp is not animated |
| B. Enable noise with an owner-chosen `noise_config` | A noise source implementation (PRNG and its seeding), owner values for `noise_min/max`, `slow/fast_alpha`, `slow/fast_depth`, then host tests that noise never exceeds the ceiling or bypasses OFF | New code on the CTRL path; needs its own review and bench observation |
| C. Defer to a later revision after the first bench session | Nothing now | None |

**Recommendation: A for the first bench image, then C.** The first bench goal is the
OFF/ceiling/thermal contract. Animation adds a moving input that makes those readings
harder to interpret. Choose B's values only after the steady image has passed the
`../BENCH-TEST-SHEETS.md` rows.

## D2. Brightness transfer (gamma): currently none

No `normalized_transfer` is configured; the knob maps linearly into [floor, ceiling]. V72
has no default gamma (`../src/normalized_transfer.h`). The owner's 2026-10-06 bring-up
firmware uses a 2.2 LUT, and `doc/src/content/docs/architecture/board-l.mdx` cites 2.2 as precedent.

| Option | What it takes | Risk |
| --- | --- | --- |
| A. None (linear) | Nothing | Knob feel bunched at the bright end |
| B. Piecewise-linear approximation of gamma 2.2 through `transfer_config` | Owner approval of the exponent and point count; generated points with a host test that it is monotone, zero-preserving and never above the ceiling | The transfer is applied after thermal attenuation; its interaction with the floor (16.2 %) needs a check |
| C. Another exponent (2.2–2.8) or CIE lightness | Owner choice | Same as B |

**Recommendation: A for the first bench image; B (2.2, matching the owner's bring-up) as
the first candidate after it.** Gamma only changes feel, and the ceiling is enforced after it
in `board_ctrl_write_ccr`, so it can be added without touching the safety rows.

## D3. Latches and tuning

| Item | Current image (proposal) | Options | Recommendation |
| --- | --- | --- | --- |
| Sensor-fault recovery | `LAMP_RECOVERY_LATCH`: OFF until reset | LATCH or V72 `LAMP_RECOVERY_AUTO` | Keep LATCH until the NTC and knob faults are characterized on the bench |
| Reset latch | 3 consecutive abnormal resets → OFF until a power cycle; cleared after 10 s healthy run | Count 2–5; healthy time | Keep 3 / 10 s; revisit only with bench reset data |
| Ramp | `LAMP_RAMP_INCREMENT` 26, about 2.5 s 0→full | Owner feel choice | Keep; it matches the bring-up timing |
| Knob window | 8 samples, max age 7 ticks | 1..32 | Keep 8 |
| Knob endpoints | 91..4000 placeholders | Calibrated per board | Calibrate on the bench; storage is undefined (a separate decision) |
| NTC thresholds | 104 → 69 linear gain, ≤ 69 OFF, ≥ 3500 open | Owner thermal policy | Keep until the NTC-to-LED-TS correlation is measured |
| Production RDP | Not set | 0 or 1 | Owner decision before any production image |

Each change above is a source edit in `board_l_proposal.h` or `board_samples.c`; the build
receipt records its effect, and `make check-incremental` proves the image is rebuilt.
