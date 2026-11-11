# C1 gap sensitivity, attempt 2: no −12 V gap passes, and +5 V is not evaluated

Model sensitivity only, under `d1-gap-criteria.md` Amendment 1. electrical_acceptance stays NOT ESTABLISHED,
and the recorded 2 us failures stay failures. Source: run 43109786353 on `0feee3c` (conclusion success),
artifact 13896581122, zip sha256 `bda29270cd93c0b837d839eec966308e381c402439e9c5037a5d56833d636370`. The
record is `d1-gap-attempt2-20261111.json`.

## Baseline identity reproduced, and the pre-enable decks are identical
- **Baseline:** the nom/adv decks and the primary and supplemental waveforms match byte for byte.
- **Pre-enable:** every completed PWL case has the baseline time grid and outputs before 40 ms (difference
  0.0 V, 21064 rows).

## +5 V stopped: g20 ABORTED at 101.275 ms
- **Abort:** "Timestep too small … trouble with node xq1.10", after enable and before conduction onset.
- **Before the abort:** the deck matches the baseline exactly up to enable: 20733 rows before 40 ms, the same time
  grid, 0.0 V output difference. The abort follows the scheduled shift, not a divergence before enable.
- **Not run:** g16, g12 and worst, with the rail stopped and no solver change.
- **Not evaluated:** no +5 V gap.

## −12 V: g20 and g16 fail rule 6, and g12 ABORTED at 247.685 ms
| Case | Realized gap | Peak slope (margin) | Cap current (margin) | Enable Vgs to onset, peak I | Rule 6 below baseline | Other rules |
| --- | --- | --- | --- | --- | --- | --- |
| baseline | 2.8672 V | 1.4748 V/ms (−0.0048) | 0.2653 A (−0.0003) | 9.7 mV, 4.65 mA | — | recorded failure |
| g20 | 1.9985 V | 0.6403 V/ms (0.8297) | 0.1152 A (0.1498) | 8.1 mV, 4.63 mA | 12.2 µV | all hold |
| g16 | 1.5988 V | 0.7668 V/ms (0.7032) | 0.1380 A (0.1270) | 8.4 mV, 4.63 mA | 55.6 µV | all hold |
| g12 | — | ABORTED | — | — | — | not evaluated |

- **g12:** aborted after the disable edge ("trouble with node xq5.10"). It is ABORTED: neither a pass nor a fail.
  Before 40 ms it matches the baseline exactly (21064 rows, 0.0 V).
- **worst:** not run, because the rail stopped.
- **Rule 6:** the resolution is 1e-5 V, and no −12 V enable-edge contract bound is recorded. Both completed cases
  stay below the 5 mA conduction criterion during enable.
- **Repeat:** g20 −12 repeats attempt 1 (behavioural source): peak slope 0.6403 V/ms in both, rule 6 12.2 µV in both.

## Prediction 1 is not met in its monotone form
- **Slope is not monotone in the gap.** Peak slope falls from 1.475 V/ms at the baseline gap (2.87 V) to
  0.640 V/ms at 2.0 V, then rises to 0.767 V/ms at 1.6 V.
- **What it does not show:** this dispatch does not show where a minimum lies or what happens below 1.6 V.

## Prediction 2 holds in direction: the enable edge is what fails
Slope and current pass at both evaluated gaps, while the enable-edge minimum moves below baseline as the gap
shrinks: 12.2 µV at 2.0 V and 55.6 µV at 1.6 V.

## A real threshold window is wider than the evaluated span, and no evaluated gap passes
- **Sourced threshold window:** VGS(th) is guaranteed 1.5–2.7 V at 250 µA and 25 °C only. This row is in the
  component owner's sources (`component-csd18543q3a`).
- **Typical temperature curve:** 2.222 V at −25 °C and 1.749 V at 75 °C, so 0.47 V over that range. This is
  relayed from #259 and is not yet in the owner. No guaranteed temperature limit is sourced.
- **Spread from a fixed floor:** a floor fixed against the gate drive would move the gap one-for-one with the
  threshold. That spread is 1.2 V across the guaranteed range at 25 °C alone, plus about 0.47 V of typical drift
  from −25 to 75 °C. A floor that leaves a 2.0 V gap on a 2.7 V part leaves about 0.8 V on a 1.5 V part. That is
  below the smallest evaluated gap (1.6 V on −12 V; both 1.2 V cases aborted), and that part conducts at a lower
  Vgs.
- **No passing gap to compare.** The model's 5 mA onset is not the datasheet's 250 µA threshold, so this is a
  span comparison only, not a pass claim.

## Owner decision (2026-11-11): C1 as a fixed gate pre-bias is rejected
- **Deciding fact:** the threshold window, not the rule 6 results. A floor that leaves 2.0 V on a 2.7 V part
  leaves about 0.8 V on a 1.5 V part. On −12 V the enable transient already brings Vgs within 8.1 and 8.4 mV of
  the model onset in the completed cases, and within 9.7 mV at baseline. On +5 V the baseline distance is 133 mV,
  and no +5 V case was evaluated.
- **Rule 6 significance:** the manager judges 12 to 56 µV far below any contract quantity. The rule verdicts
  above still stand as recorded.

