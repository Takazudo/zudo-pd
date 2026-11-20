# Issue #52: LED peak-current margin, desk analysis (UNADOPTED proposal)

This is a desk calculation over primary evidence. It changes no hardware, and nothing in
it is measured. The calculation is in `led_margin.py` and its output in `led_margin.json`;
the sources are in `SOURCES.json`, and their hashes equal the retained ones.

## Verdict

Recommend **RS1 = 250 mΩ: TA-I RLP25FEER250**, a value-only change on the same 2512 land
and the same RLP25 series. The LCSC code is not verified.

- It is the only option that bounds the current through **guaranteed** parameters:
  VSENSE max and resistor tolerance/TCR.
- A firmware duty ceiling **cannot** give a guarantee. It relies on the AL8860's typical
  CTRL transfer curve, and on the firmware being correct and running. Keep it only as
  defence in depth for the as-built 200 mΩ boards.

## 1. The CTRL path is filtered-analog, not PWM dimming

PA6 (TIM3_CH1) → R20 10 k → CTRL, with R21 33 k and C21 100 nF to GND.

- Thevenin: R20 ∥ R21 = 7.67 kΩ with 100 nF gives f_c = **207 Hz**.
- At the proposed 20 kHz carrier, worst-case ripple on CTRL is **46.7 mV p-p**. That assumes
  a 50 % duty, rail 3.33 V, R20 −1 %, R21 +1 % and C21 −10 % (C21's tolerance is assumed).
  It is about 2 % of the 2.2 V dimming span.
- So the AL8860 sees a DC level plus a small 20 kHz ripple. It does not see on/off PWM.
- This is the design intent, not only an inference. The owner's 2026-10-06 bring-up firmware
  (`firmware/board-l-bringup-mac-20261006/`, `main.c` 5a152126…) drives exactly this:
  TIM3_CH1 at 20 kHz into the RC filter, floor 0.41 V, full 2.53 V.
  - That firmware has **no duty ceiling**. On an RS1 = 200 mΩ board at full knob, it
    produces the worst-case peaks in §3: 88.6 mA, or 96.9 mA at h = 30 %.
  - Do not run it at full knob on 200 mΩ boards. Its existing `.pio` build output is no
    evidence that any board was flashed.
- **Peak current = mean × (1 + VSENSE_HYS)**, where the mean is set by VSENSE × (CTRL
  fraction) / RS.

DS39014 Rev 8-2 guarantees only VSENSE: 96–104 mV, **at TA = 25 °C**. Everything else in
the stack-up is typical:

- the hysteresis (±20 %, no max);
- the CTRL linearity ("as shown in Figure 1");
- the 5 % current accuracy.

## 2. Method

Hot branch of the 8-branch ballast network:

- **Hot branch:** lowest string Vf and the lowest ballast resistance.
- **Other seven branches:** Vf higher by the locked 0.30 V spread, ballast at its highest
  resistance.
- **Ballast resistance spread:** ±1 % tolerance, or ±2 % with ±100 ppm/K over 100 K added.
- **RS1:** −1 % tolerance and −50 ppm/K × 100 K.
- **Hysteresis sensitivity:** 20, 25 and 30 %.
- **Limits:**
  - the LED IF absolute maximum, 90 mA, valid to TS ≈ 65 °C (graph-read);
  - the proposed design limit, **81 mA** (90 % of 90 mA).

The model reproduces the retained figures: 0.6303 A total peak and 88.19 mA hot branch at
200 mΩ, ±1 % ballast and 20 % hysteresis. It gives 88.59 mA once RS TCR is included.

## 3. Results: hottest branch peak

| RS1 | Nominal mean | h 20 %, ballast ±1 % | h 30 %, ballast ±2 % | ≤ 81 mA in all cases? |
| --- | --- | --- | --- | --- |
| 200 mΩ (as built) | 500 mA | 88.6 mA (98.4 %) | 96.9 mA (107.7 %) | no |
| 220 mΩ | 455 mA | 81.3 mA (90.3 %) | 88.8 mA (98.7 %) | no |
| 240 mΩ | 417 mA | 75.2 mA (83.5 %) | 82.1 mA (91.2 %) | no |
| **250 mΩ** | **400 mA** | **72.5 mA (80.5 %)** | **79.1 mA (87.9 %)** | **yes** |
| 270 mΩ | 370 mA | 67.7 mA (75.2 %) | 73.9 mA (82.1 %) | yes |

**Side effects of 250 mΩ**

- Nominal current is 20 % lower (400 mA instead of 500 mA), so per-branch mean is 50 mA
  instead of 62.5 mA. Light falls by roughly the same proportion; this is a product
  decision.
- AL8860 duty falls from about 77 % to **about 74 %**. That is back inside the 25–75 % DSW
  band (DS equations, V15 = 15 V, VD 0.45 V).
- RS1 dissipation is at most 45 mW of its 2 W rating.

**Firmware ceiling with RS1 = 200 mΩ** (typical transfer, bounded by I/I_FS = V/2.5 with
+5 % accuracy):

- Reaching 81 mA needs duty ≤ **83.1 %** at h = 20 % (ballast ±1 %), ≤ 76.6 % at h = 30 % (±1 %),
  or ≤ **75.2 %** at h = 30 % with ballast ±2 % (`ctrl_ceiling_rs200_hys30_rb2`). The last
  one is the firmware default, `CTRL_FULL_CCR` 2407.
- That costs about 18–25 % of the light at nominal, which is no better than the RS1 change.
- None of it is guaranteed. A stuck-high PA6, a corrupted image or a firmware bug removes it.

## 4. Residuals that only a bench can close

- **VSENSE over temperature:** not specified, only 25 °C is guaranteed. The 10 % margin is
  meant to absorb this; it is not proven to.
- **VSENSE_HYS maximum:** not published. Measure the LED_N or coil current ripple at
  min/max VIN.
- **Thermal derating:** the LED derating (graph-read) limits the 250 mΩ worst case
  (79.1 mA) to TS ≲ 76 °C. Firmware thermal derating must act before that, and the
  correlation between the NTC (RT1) and TS is unmeasured.
  The bring-up firmware's derate (NTC code 104, ≈65 °C, to hard off at 69, ≈80 °C) only
  meets this if the NTC reads TS within a few kelvin, which is unmeasured.
- **Pulsed rating:** no pulsed-current rating exists in the retained LED spec, so issue
  #52 option 3 closes negatively.
- **Sourcing:** the RLP25FEER250 orderable/LCSC binding and its exact-value evidence are
  missing (LCSC search returns 403).
