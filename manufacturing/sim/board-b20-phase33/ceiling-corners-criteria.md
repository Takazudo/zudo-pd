# Ceiling-bank corners diagnostic: what is measured, stated before the dispatch

**This is a diagnostic, not a verdict run.** It judges nothing, changes no ceiling and admits no candidate. It fills two
gaps behind the current-form no-load exception proposed to OSC (−12 V ≤ 350 mA below 0.75 V, +5 V ≤ 160 mA below
0.45 V, into any bank up to 180 / 120 µF). The owner authorised one dispatch on 2026-11-12. electrical_acceptance stays
NOT ESTABLISHED, and the recorded D1 failures stay failures.

## What runs
All decks use the contract ceiling bank, 180 / 120 / 180 µF on +12 / +5 / −12 V. Each is the unmodified no-load
baseline as built by `osc_bank.base_deck`: no T2 and no candidate.

| Label | Entry | Purpose |
| --- | --- | --- |
| nom, adv | pinned | cold anchors, and the cross-check deck (nom) |
| e5lo, e5hi | matched-variant ladder directly | the +5 V enable-edge corners (VO shifts as in T2 rev 2) |
| e12hi | matched-variant ladder directly | in-run anchor for hot-e12hi, and a repeat of the recorded variant row |
| hot-nom, hot-adv, hot-e12hi, hot-e5hi | pinned | the same deck plus one `.temp 82.1` line |

- **Why e5lo / e5hi / e12hi skip a pinned run.** They aborted pinned in run 43187732133. The owner authorised a variant
  run, with the same labelling as the recorded e12 rows.
- **The ladder.** Step 1 is abstol 1e-9 → 1e-8. Step 2 is rshunt 1e10 → 1e9, used only if step 1 still aborts. A hot deck
  that aborts pinned enters the same ladder.
- **Anchors and cross-check.** Every variant step that is used also reruns:
  - the cold anchor of each hot row in that step;
  - `nom` (pinned COMPLETE in every earlier run), so the pinned-minus-variant difference is measured in this run.
- **Labelling.** A variant row is labelled as such and is never presented as a pinned waveform. No other solver option
  changes, and itl4 stays pinned.

## The hot case is a uniform-temperature sensitivity, not a hot-start verdict
- **What changes.** Exactly one line, `.temp 82.1`, is added before the pinned `.options` line. 82.1 °C is `HOT_T_C`
  (owner decision, the −12 V stage TJ at continuous contract load and 40 °C ambient). TNOM and every option stay
  unchanged.
- **What it overstates.** The whole board is set to that temperature. A no-load start from cold is near ambient, so
  this bounds a warm restart. It is not a measured start-up temperature.
- **What it may not model.** Only models with temperature terms respond. The vendor FET and op-amp macros are never in
  the evidence by design, so the runner reports a count of temperature keywords per model file (`tnom`, `temp`, `tc1`,
  `tc2`, `xti`, `kt1`, `kt2`, `ute`, `eg`, `tcv`, `trs`), and never the bytes. A count of zero for a macro means a small
  hot-minus-cold difference says nothing about that part. Counts can include comments, so they show reach, not effect.
- **No leakage change.** The T2 hot-leakage rows do not apply: the baseline has no T2 elements.
- **How hot rows are compared.** Hot-minus-cold differences are formed only between rows measured under the same solver
  setting.

## Measured
These are the quantities and window of `osc-bank-criteria.md` (40–234.5 ms), per rail:
- peak slope inside and above the exception region;
- peak ESR-branch current in the region, and over the window;
- charge in the region;
- current half-width.

Also reported:
- the largest value of each quantity, with its deck;
- the labels with no completed run (**unknown**);
- the variant cross-check;
- hot minus cold.

**Flag (owner).** Any in-region current above **300 mA on −12 V** or **140 mA on +5 V** is listed under `flags`. Such a
result would use most of the proposed 350 / 160 mA margin. A flag is reported, not judged.

## Expectation (stated before the run, not a criterion)
- **Variant rows.** e5lo / e5hi complete under abstol, as every fitted-bank e5 row did.
- **+5 V current.** Below the e12hi row's 124 mA: e5hi raises the +5 V threshold, and the fitted-bank e5hi rows were
  smaller than adv.
- **−12 V.** e12hi repeats about 1.54 V/ms / 276.5 mA.
- **Hot rows.** No prediction of size or sign. Several hot decks may abort pinned.
