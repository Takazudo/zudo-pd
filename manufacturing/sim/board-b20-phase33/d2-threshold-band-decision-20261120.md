# D2 firing-network threshold spread: the reviewer's finding is valid; retime RDG12/RDG5 and CDG12/CDG5 (candidate C1)

Decision record, 2026-11-20. SIM and CALCULATED only; nothing is measured. Evidence: [criteria](d2-threshold-band-criteria.md), [record](d2-threshold-band-20261120.md),
[result](d2-threshold-band-20261120.json), `d2-threshold-band-results/`.

## The finding is valid, and the as-drawn network is worse than the reviewer showed

- **Arithmetic reproduced.** With RDG 10 kΩ / CDG 22 nF and R61 4.7 kΩ / R62 47.5 kΩ / 47 nF + 22 nF
  (`board_b20_spec.py` lines 585–618), the RC time to threshold is 120.0 µs (Q51/Q52) and 40.7 µs (Q55) at 2.0 V and
  4.9 V. The reviewer's 40.0–243.5 µs and 19.1–62.8 µs reproduce exactly, but they include his PA terms (hot −0.3 V,
  X7R class and DC-bias loss, drive 4.4–5.0 V). The guaranteed-only bands at 4.9 V are 74.8–205.0 µs and 27.7–60.8 µs.
- **Sourced rows.** `fact-c840100-vgs-th-min` 1.5 V, `-typ` 2.0 V, `-max` 2.7 V (ID 250 µA, 25 °C);
  `fact-c840100-ciss-typ` 885 pF, `-max` 1150 pF; `fact-c840100-vgs-th-hot-limit-unsourced` (no bound away from 25 °C).
- **The failing deck reproduces.** His `m2-hlrh-phnlfl-zmz-gtd-nomR` deck reruns byte-identical.
- **His timing emulation is approximate, and the result survives a stricter one.** He rescaled CDG12/CDGN by the
  calculated time ratio. The vendor model reads 2.204 V at 250 µA (2.545 V at 10 mA, 3.77 V at 25 A), so that maps a
  threshold ratio onto a capacitor. Shifting the model's gate instead, with the as-fitted parts at tolerance, gives
  0.497 V in `hlrh-phnlfl-zmz` (his 0.39 V): still an R-VEE failure. His `hhrh` failure (0.53 V) becomes a pass
  (0.726 V) without his resistor corners.
- **The corner is inside E22.** `zmz` is +12 V unloaded and −12 V at its 2.0 A maximum; `phnlfl` is the fitted bank at
  ±20 %. Both are in the pre-registered 243-deck grid, and E22 commits to 0..maximum per rail independently.
- **The 6.09 V deck is not a guaranteed-band failure.** It pairs a hot Q51 (1.2 V) with a 25 °C-maximum Q55 (2.7 V)
  on one board, plus the PA capacitor loss. The as-drawn high side holds 5.65 V across the guaranteed band here.
- **Understated: the decks' 4.9 V drive is unreachable.** EN_E is 4.756 V and CDH charges through the Q57 body diode;
  `calculate-board-b20-draft.py` itself uses 4.156 V. At 4.10–4.65 V the as-drawn network fails 72 of 576 control
  decks (down to 0.16 V, 20 of them also on the direct-hazard row), including decks with both ±12 V rails at maximum.

Mechanism: a 2.7 V part on a 4.1–4.9 V RC ramp both starts late and enhances slowly, so +12 V is still present when
OSC's −12 V load has drained the held −12 V bank.

## Decision: adopt C1, a value-only change in existing footprints

| Ref | Old | New | LCSC / inventory line |
| --- | --- | --- | --- |
| RDG12, RDG5 | 10 kΩ 1 % 0603, C25804 | **4.02 kΩ 0.1 % 0603**, RT0603BRD074K02L | C705781, `line-c705781` (spec key `RP4K02`) |
| CDG12, CDG5 | 22 nF X7R 10 % 0805, C1729 | **27 nF C0G 5 % 0805**, GRM2165C1H273JA01D | C3882413, `line-c3882413` (spec value `27nF C0G`) |
| R61, R62, C44, C45, Q51/Q52/Q55, loads, sequencer | | unchanged | |

- Both lines are already fitted on B20 (R6/R16/R17/R21/R23 and C9). No new part, no footprint or copper change.
- τ goes from 220 µs to 108.5 µs with a tighter, bias-free capacitor. The −12 V network is untouched, so the earliest
  discharge onset does not move (23.2 µs in both networks at the same corner).
- Shutdown and re-entry are unaffected: the slowest level is 1.43 ms against 100 ms and the 19 ms interlock, and the
  firing parts do not load the hold-up node.

## Pre-registered reading: five discharge rows PASS (SIM) in 2,808 of 2,808 decks; the added onset-floor row is NOT MET as worded

- G (verdict set, guaranteed 25 °C threshold band × part tolerances × drive 4.10–4.65 V): PASS on all five rows,
  0.742 V smallest \|−12 V\| while +12 V is present, 5.652 V largest once it is absent.
- The onset-floor row I added fails as worded by 0.2 µs (23.202 against 23.401 µs) because my control grid lacked
  the same-direction corners. Amendment 1, written before its 576 control decks ran, gives a 22.200 µs floor: MET.
  I adopt C1 on that amended reading and state the original wording's failure rather than hide it.
- Reported bands: PA-HOT PASS (576; 5.877 V at the 6 V side), **PA-COLD FAIL (8 of 576, 0.593–0.595 V)**, L49 at the
  published 4.9 V drive PASS (576; 1.317 V).
- Control: the as-drawn network FAILS the same grid (72 + 64 of 1,152).

## Residual risks

- **The window is narrow.** Slower (4.7 kΩ + 27 nF) fails the low side, faster (3.09 kΩ + 27 nF) fails the high side
  with the hot term. C1 holds 0.14 V on the low side, about 40 µs of timing, and the routed-parasitic corners take
  0.035 V of it (post-hoc, 8 decks).
- **Cold is not covered.** A typical +0.12 V shift on a 2.7 V part at a 4.10 V drive fails by 7 mV.
- **Drive level is unsourced** and is the strongest term: the low-side value moves from 0.742 V at 4.10 V to 1.317 V
  at 4.9 V. Measuring DIS_C on an enabled board belongs in T5.
- **The disconnect in the deck is ideal.** DIS_P and the −12 V disconnect follow EN_E directly, while the +12 V / +5 V
  disconnect waits for EN_N to rise through REN 10 kΩ. The real margin behind the 23 µs onset is not shown by any
  record. C1 does not change it.
- Q52 was not moved against Q51; the threshold corner is a rigid shift of the vendor curve; resistive loads; generic
  small-part models; D7's repetitive-pulse residual.
- D2's "no longer an order hold" rests on records that never moved the switch threshold. C1 should go through the
  spec, BOM/inventory, ERC and DRC parity before the order.

## If more margin is wanted, the minimal circuit change is a higher or stiffer firing drive

Not adopted and not simulated. The spread comes from a 1.5–2.7 V threshold on a ramp that ends near 4.1–4.6 V. A drive
that ends higher makes both edges nearly proportional to threshold and restores the slew. RE1 4.7 kΩ sets 0.22 V of
the loss, but it is part of the enable latch and would need that block's own re-verification. No part is proposed.

## Files

In `manufacturing/sim/board-b20-phase33/`: this decision, [`d2-threshold-band-criteria.md`](d2-threshold-band-criteria.md)
(pre-registered; amendment 1 included), [`d2-threshold-band-20261120.md`](d2-threshold-band-20261120.md),
`d2-threshold-band-20261120.json`, `d2_threshold_band.py`, `d2_threshold_sets.py`, `d2_threshold_posthoc.py` and
`d2-threshold-band-results/` (per-set case results gzipped, pre-registration and waveform hashes). The decks and
21 GB of waveforms were deleted after hashing; the tooling used was unedited repository code at the reviewed head.
