# D2 sequenced −12 V discharge: what is simulated and how it is read, stated before the dispatch

**This is a candidate evaluation, not a design adoption.** On 2026-11-14 JST the owner chose this route after the fast
matched discharge failed R-VEE in simulation ([attempt 2 record](d2-fast-discharge-20261114.md)). Nothing in the
schematic, PCB, BOM or inventory changes with this run. electrical_acceptance stays **NOT ESTABLISHED**, D2 stays a
pre-order hold, and no OSC contract row changes.

## The candidate: the fast matched discharge with the −12 V switch fired early and held at 3 V

Everything in the [fast matched discharge criteria](d2-fast-discharge-criteria.md) stands, with these changes:
1. **Sequencer.** The −12 V discharge switch is held off while |−12 V| ≤ 3.0 V and +12 V > 0.3 V. −12 V therefore drops
   below 6 V early, waits above its 0.6 V absent level until +12 V is gone, then finishes.
   - In the deck the sequencer is a behavioural clamp (`BHOLD`): 100 Ω from the switch gate to its source, with smooth
     thresholds. Its discrete circuit is **not yet drawn**. A PASS shows the function works with the vendor switch
     model. It does not qualify a circuit.
2. **Earlier −12 V firing.** CDGN becomes 68 nF (was 180 nF), so the −12 V switch fires near 50 µs instead of 131 µs,
   ahead of +12 V.
3. **Q54 model.** The ideal hysteretic switch becomes a smooth behavioural switch of the same 5 Ω on-resistance, in the
   form of the drawn gate pulldowns. In attempt 2, all 70 aborts were at EN_N 2.6 V, the switch's VT + VH.
4. **Loads.** +5 V adds the E22 canonical planning load (224.3 mA). This gives 27 load corners (0 / planning / maximum on
   each rail) × 9 banks = **243 decks**, labelled `d2sq/<bank>-<loads>`.

The values are PROPOSED. The resistors stay 0.5 / 1.5 / 0.5 Ω and the switches stay CSD18543Q3A.

## The calculation passes every corner with ideal switches

[`d2_sequenced.py calc`](d2_sequenced.py) gives the result in
[`d2-sequenced-calc-20261114.json`](d2-sequenced-calc-20261114.json). It uses exact exponential decay, ideal
switches and resistive loads.
- **The sweep:** switch-on times from the disconnect are +12 V 120 / 155 / 190 µs, +5 V 120 / 163 / 210 µs and −12 V
  0–100 µs. That is 243 corners × 45 timing cases.
- **Result:** 0 of 10,935 cases fail. Without the sequencer, 5,562 fail (the control).

## Deck, solver and run rule
These are unchanged from the fast-discharge criteria: the compact shutdown deck, the pinned solver settings,
`.tran 1u 6m 0 1u` from the DC operating point, `--original-only`, and an EN_N edge of 50 µs at 1.000 ms. An aborted
deck is recorded as ABORTED and is not retried.

## Reading rule (fixed now, before any result)
The rows, thresholds and verdict rule are the fast-discharge rows, read by the same `d2_fast_discharge.read`:
- disconnect before discharge;
- disconnect skew;
- the discharge levels within 100 ms;
- R-VEE in both directions;
- the R-SW direct hazard.

The verdict is one of these:
- **PASS (SIM)** means every row holds in all 243 decks, and all of them are COMPLETE.
- **FAIL (SIM)** means any row fails in any COMPLETE deck.
- **NOT FORMED** means no row fails, but at least one deck did not complete.

Rows are timed from EN_N crossing 2.5 V. A disconnect that completes before that crossing is reported as 0 ms, as in
attempt 2.

**Reported, not read:** the same peak currents, resistor energies, onset and level times.

## Expectation (stated before the run, not a criterion)
PASS. A local smoke test with a stand-in FET (not the vendor model, not evidence) completed five corners and passed
them, with −12 V reaching its level 0.16–0.45 ms after +12 V.

## What a PASS supports and what stays open
A PASS shows that the sequenced function meets the voltage-form discharge rows with the vendor switch model, across
OSC's committed load range and bank tolerance. These stay open:
- the discrete sequencer circuit and its own evaluation;
- the resistive-load ASSUMPTION;
- pulse-rated part selection;
- the schematic change;
- layout;
- the bench check.
