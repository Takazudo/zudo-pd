# T2 rev 2 paper check: RT2S fails, and no single value set with existing models clears rule 6 on paper

Paper only, from the attempt 1 waveforms (run 43122081181) and the decks. Nothing was pre-registered or
dispatched. This check was required before any rev 2 dispatch (owner decision 2026-11-12).

## RT2S 10 kΩ fails: it adds a DC path from the summing node
- **The path.** While BT2G is closed (v(ennd) > 1.0, which includes the whole disabled state and the enable
  window), RT2C + RT2S put 509 kΩ from trk12n_fb to GND. In rev 1, t2c had no DC path: DT2C is reverse-biased
  and RT2C ended there.
- **The divider change.** trk12n_fb's DC level is a passive balance on RT12NC (4.7 kΩ to GND). 509 kΩ in parallel
  changes it by 0.92 %.
  - Disabled (fb ≈ 0.192 V): about 1.8 mV on the integrator's initial state. That is the same size as the 1.9 mV
    offset RT2S was meant to remove.
  - Enable window (fb ≈ −0.5 mV): about 4.6 µV on fb. The trk12n divider (843.1 / 93.1 = 9.06) turns that into
    about 41 µV at the output. That fails rule 6's 10 µV resolution on its own.
- **The required checks therefore do not proceed for RT2S.** Hold droop, first power-up and stale-high are moot,
  and so is the 48 µA source and return.

## The coupling has two parts, and the second exists in attempt 1 too
DT2C (DBODY, CJO 20 pF) couples every swing of t2o into the summing node while BT2G is closed.

| Part | When | t2o swing | Coupled charge into trk12n_fb | DRV offset (T2 − control) |
| --- | --- | --- | --- | --- |
| Capture step | 41–45 ms, at every enable | +2.1 V (k × the 0.42 V capture diode drop) | about +20 pC (5.0–5.5 nA) | −1.9 mV, held to about 70 ms |
| Approach to engagement | 72–85 ms, as DRV leaves its peak | −5.7 V (4.85 to −0.86 V) | about −30 pC (−6.4 nA at 80 ms) | +3.3 mV at 80 ms |

- **The measured −135 µV is the net of both.** The output difference is +150 µV at 70 ms and +330 µV at 72 ms,
  while only the capture step acts. It then crosses to −100 µV at 76 ms and −135 µV by 80 ms, as the approach part
  takes over.
- **The approach part is not the clamp acting.** DT2C does not conduct until about 85 ms. The current before that
  is displacement current through its junction capacitance.

## Candidate fixes, none of which clears rule 6 on paper
1. **Delayed connection with GND parking (removes the capture step only).**
   - The parts: RT2D 100 kΩ from EN_N to t2d, and CT2D 47 nF (C0G) from t2d to GND, so τ = 4.7 ms.
   - BT2G closes only when t2d < 0.4 V (11.9 ms after enable) and v(ennd) > 1.0. A new BT2D parks t2g at GND when
     t2d > 0.6 V (from 0.6 ms after disable to 10.0 ms after enable). There is a break-before-make gap.
   - **What it leaves unchanged:** no DC path while connected; hold droop (τ 0.909 s); first power-up (DC
     operating point at EN_N high gives t2d = 5 V, so the clamp is parked); stale-high; and release, where t2g
     floats as in rev 1.
   - **Why it does not suffice:** the −30 pC approach part remains. It is the part that carried the net to −135 µV
     on attempt 1, so rule 6 is not expected to pass.
2. **A low-capacitance clamp diode (removes both parts at the source).**
   - The inventory holds no sourced small-signal diode, and the decks have only DBODY.
   - It needs a new model with component evidence, which the "existing models only" condition excludes.
3. **Rescale the difference stage (shrinks both parts about 10×).**
   - k = 0.499 with R_C = 49.9 kΩ keeps k / R_C, so the loop is unchanged. It needs V_R = 0.25 V, a new divider
     from ref25, to keep Δ.
   - The coupled charges fall to about 2 and 3 pC, a DRV offset of about 0.3 mV. Scaled from 135 µV, that is
     about 13 µV, which is still at or above the 10 µV resolution.
   - It also scales the op-amp offset into Δ 10× (still millivolts) and adds parts.
4. **Combine options 1 and 3.** That leaves only the approach part at about 3 pC, roughly 10–15 µV by the same
   scaling. That is marginal, not a pass on paper.

## Where this leaves rev 2
- **Not pre-registered.** Every candidate above changes more than RT2S, and none clears rule 6 on paper.
- **Owner decision needed.** The choice is between a low-Cj diode model, the 1 + 3 combination knowing it is
  marginal, or recording T2 −12 V as failed. A diode model would need a sourced part and an owner bundle, so it
  is the larger step.
- **Rule 9 is unaffected by any of these.** It is not the clamp's.
