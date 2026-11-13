# T1 (integrator leak during RAMP reset): REJECTED by construction (owner decision 2026-11-11)

This is a pre-dispatch DC analysis of the deck topology. Nothing was built or run. The T1 proposal was wrong,
and this corrects it.

## With a leak, the driver's DC operating point is set by offset currents, not by conduction
A resistor R from the driver output to the amplifier's inverting input turns the integrator into an inverting
amplifier. While RAMP is held at zero, each driver then settles where the currents into the summing node
balance.

**+5 V (U13B; TRK5 virtual node at RAMP_P5, about 0 V during reset).**
- Current balance: out/23.2k + (−12.14 V)/10M + DRV/R = 0, so DRV = R·(1.214 µA − out/23.2 kΩ).
- With R = 1 MΩ: DRV = 1.214 V − 43.1·out.
- Reaching the edge (about 2.31 V at P5_G, with P5_CS about 0 V) would need out = −25 mV. The pair can only
  source current, so that cannot happen.
- At the 52 mV floor, DRV = −1.0 V, so the driver sits at its 0 V rail.
- **Result: the same windup as today. T1 does nothing on +5 V.**

**−12 V (U9B; TRK12N_FB = TRK12N = 0.1104·out).**
- Current balance: DRV ≈ 213·TRK12N_FB + 1.214 V = 23.5·out + 1.214 V.
- The edge needs DRV ≈ M12_CS + 2.34 V ≈ −9.78 V, which requires out ≈ −0.47 V.
- The leak therefore drives the pair on and pulls −12 V from its −97 mV floor to about −0.47 V during the
  reset window: a pedestal, the excluded change.
- That level also moves about 26 mV per 0.6 V of threshold, so it is threshold-dependent.
- **Result: an enable-edge excursion far beyond the baseline. It would fail rule 6 by construction.**

**Changing R does not help.** A different R only rescales the same balance. The operating point is set by the
10 MΩ offset currents and the output, never by the conduction edge. Any finite-gain leak referenced to the
summing node has this property.

## T2 does not have this defect
- **How it acts.** The peak-hold clamp does not change the loop's DC law. It only stops the driver's downward
  retreat below the edge the loop itself found. The clamp supplies the small summing-node current, about
  1 µA, that the integrator would otherwise integrate.
- **Output.** It is unchanged: the pair idles just below its own edge, about Δ plus 8–133 mV from onset.
- **Dead zone.** When RAMP moves, the slew to conduction shrinks from about 2.3 V to about 0.1–0.25 V, whatever
  the threshold.
- **Status.** It is the remaining threshold-independent candidate.

## +12 V shows the same windup and passes its screen
- **Enable edge.** In the baseline, P12_G peaks at 2.543 V at 64.9 ms, with 0.48 mA supply current and the
  output at 91 mV.
- **After the enable edge.** The gate parks at 5 mV, the 0 V rail, from 110 ms until the ramp, the same pattern
  as the failed rails.
- **Screen.** +12 V stays within its 1.23 V/ms limit, so it does not need a correction for D1. A correction
  applied to +5 V and −12 V would naturally extend to +12 V for uniformity. That is a design choice, not a need
  shown by the screen.
