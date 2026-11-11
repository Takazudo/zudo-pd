# D1 C1 gate-to-threshold gap sensitivity — pre-registered 2026-11-11

**This is a model sensitivity only.** It makes no claim about any real CSD18543Q3A part, threshold or
temperature. electrical_acceptance stays NOT ESTABLISHED, and the recorded 2 us failures stay failures.
No ceiling, tolerance, probe, RAMP, spec or schematic changes. `gap_sensitivity.py` implements exactly
these rules, and a test keeps the numbers in step.

## Question

C1 is gate pre-bias while enabled. Its question is how the peak slope depends on the **gap**: the gate's
resting Vgs while the driver is parked, measured against the Vgs at which the pass pair starts to conduct.
The manager decides from the answer:
- If the largest passing gap is comfortably above what a sourced threshold window would leave, C1 goes forward.
- Otherwise the next step is a threshold-independent loop.

## Gap definition (from the baseline servo record, run 43099431981)

The gap is the Vgs at conduction onset (the first 2 us bin with |rail supply current| ≥ 5 mA) minus the
resting Vgs (the mean over 110–115 ms, while the drivers are parked and before the reference moves).
- +5 V (nom): rest −0.0000459 V, onset 2.443369 V, so the gap is **2.4434 V**.
- −12 V (adv): rest −0.514498 V, onset 2.352273 V, so the gap is **2.8668 V**.

Each variant's realized gap is measured the same way from saved internal gate and source nodes. It is
reported next to the target.

## Cases (eight variant cases plus the unmodified baseline pair, one dispatch)

| Label | +5 V on nom | −12 V on adv |
| --- | --- | --- |
| g20 | target gap 2.0 V (shift +0.4434 V) | target gap 2.0 V (shift +0.8668 V) |
| g16 | target gap 1.6 V (shift +0.8434 V) | target gap 1.6 V (shift +1.2668 V) |
| g12 | target gap 1.2 V (shift +1.2434 V) | target gap 1.2 V (shift +1.6668 V) |
| worst | gap baseline + 0.3 V (threshold raised 0.3 V, no correction) | same |

### How each case is built

- **Where the change sits.** The resting level moves at the existing gate-offset position, which is
  closest to how a gate floor would be built.
  - g20, g16 and g12 replace `VO2 p5_g p5_gi 0` (nom) or `VO3 m12_g m12_gi 0.5` (adv) with a behavioural
    source of the same nodes. Its value is base − shift × `0.5*(1+tanh((2.5-v(enn))*4))`.
  - That factor is the decks' own enable shape, so the raise applies only while enabled. With EN low it
    collapses to the baseline value, and the existing pulldown (B11/B25) still holds the gate.
- **The worst case** changes the constant offset instead: VO2 becomes 0.3, VO3 becomes 0.8. This is how the
  existing adv deck already emulates a threshold shift.
- **Every variant deck also adds:**
  - a disable at 240 ms (`VDIS dis 0 PWL(0 0 240m 0 240.05m 5)`), after the screened window;
  - one output-only line: `wrdata {case}-gap.txt v(p12_gi) v(p12_cs) v(p5_gi) v(p5_cs) v(m12_gi) v(m12_cs)`.
- Each nom variant leaves +12 and −12 unchanged, and each adv variant leaves +12 and +5 unchanged.
- The baseline nom/adv decks run unmodified in the same dispatch. They must reproduce byte for byte first.
  If identity is NOT REPRODUCED, no variant is run or evaluated.

## Measurements

| Quantity | How it is measured |
| --- | --- |
| Peak slope and screen | The refinement's adjacent-sample screen, unchanged: window 40–234.5 ms, normal limits 1.23 / 0.51 / 1.22 V/ms, no-load exception (+5: ≤ 0.45 V, ≤ 0.95 V/ms, ≤ 114 mA; −12: magnitude ≤ 0.75 V, ≤ 1.47 V/ms, ≤ 265 mA). The peak inside the exception voltage region is reported with its margin to the ceiling. |
| Capacitor current | ESR-branch current from the OSC capacitor probe (`-osc-cap.txt`), as in the refinement. |
| Floor | Mean output over 110–115 ms. |
| Overshoot | Over 2 us bin means in the screened window: the maximum of the output in its tracking direction, minus the last bin. |
| Monotonicity | Over 2 us bin means in the screened window: the largest step against the tracking direction. |
| Disabled state | Output extremes over 2–40 ms, in 2 us bin means. |
| Enable edge | Output extremes over 40–110 ms, in 2 us bin means. |
| Disable edge | Internal Vgs over 245 ms to the end, and output extremes from 240 ms to the end against 238–240 ms. |
| Enable transient | Over 40–110 ms: the maximum internal Vgs and its minimum distance to that case's conduction-onset Vgs, and the peak 2 us bin |supply current|. |
| Resolution | Comparisons with the baseline resolve to the decks' own vntol, 1e-5 V. A smaller difference is not resolved. |

## Pass rules (all must hold on the varied rail)

1. Failed-rail slope, current and voltage-region ceilings hold. The screen shows no recorded-bound exceedance
   and no boundary straddle, and the capacitor current stays at or below its ceiling. These are the
   no-load exception ceilings and the normal limits elsewhere.
2. Other rails are no worse than baseline. A rail that passed in the baseline case still passes.
3. No new overshoot beyond baseline.
4. No non-monotonic step beyond baseline.
5. Disabled state unchanged: the disabled-window output extremes stay within the baseline's.
6. Enable edge: the enable-window output extremes stay within the baseline's, for either polarity.
7. No conduction during the enable transient: no 2 us bin over 40–110 ms reaches |supply current| ≥ 5 mA. A
   conduction event fails the case even if the slope rule passes (manager, 2026-11-11).
8. Disable edge, gate held off: after 245 ms the internal Vgs stays at or below that case's own
   disabled-state maximum.
9. Disable edge, no excursion of either polarity: after 240 ms the output does not exceed its pre-edge
   extreme, and does not pass the baseline disabled level in the reverse direction.

Two parts of the manager's list are reported rather than used as rules:
- **"Servo not parked at a rail at reference start".** This was written for C2. C1 by design leaves the
  integrator at its rail and moves the gate instead, so the rule fails every C1 case by construction. The
  driver's resting voltage is reported instead.
- **Bias current through the shunt.** The modeled offset draws none. A real gate-floor network draws from its
  bias supply, not through the rail shunts.

## Outputs

For each rail, against the gap (baseline, the three targets, worst): peak slope, capacitor current, floor,
overshoot and monotonicity, plus every rule. Also reported:
- the enable-transient minimum Vgs distance to conduction and the peak current;
- each case's output excursion of either polarity at the disabled state and the enable edge, against baseline;
- the disable-edge extremes. Also the largest passing target gap, with its slope and current
margins. +12 V is not varied; its baseline screen and its own gap are reported from the same run.

## Predictions (stated before the run)

1. **Peak slope falls as the gap shrinks.** The existing adv deck already shows this, because its gate offsets
   bracket the threshold by ±0.5 V:
   - +5 with VO2 = −0.5 (gap about 1.94 V) peaks at 0.858 V/ms and passes;
   - −12 in nom (gap about 2.37 V) peaks at 0.843 V/ms and passes.

   So slope and current are predicted to pass at g20, g16 and g12 on both rails, and the worst case is
   predicted to fail beyond the recorded failure.
2. **The enable edge is uncertain.** In the baseline, the integrator's enable transient already lifts Vgs to
   2.3097 V at 66.30 ms (+5) and 2.3430 V at 71.94 ms (−12). That is within 0.13 V and 0.01 V of
   conduction onset, so a raise could make the pair conduct during the enable transient.

   However, the loop is active then. The adv deck's constant +0.5 V raise on +5 leaves the +5 enable-edge
   output extremes at 3.882 to 51.711 mV, against 3.882 to 51.870 mV in nom. That suggests the floor is the
   loop's own setpoint rather than an uncontrolled charge.

   Predicted: the enable edge holds at g20 (a raise below the 0.5 V already seen) and is unresolved at g16
   and g12. If the enable edge fails at a gap that passes slope and current, a fixed enabled-state pre-bias
   cannot be separated from the enable transient. That would point to the threshold-independent loop.
