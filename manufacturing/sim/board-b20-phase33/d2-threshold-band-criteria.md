# D2 firing-network threshold and tolerance band: what is simulated and how it is read, stated before the dispatch

**This is a candidate evaluation, not a design adoption.** It follows the independent review finding of 2026-11-20
(`/tmp/claude-0/campaign/a1/d2-sensitivity.md`): the published D2 sweeps never moved the discharge-switch threshold, so
the firing spread of the as-drawn RC networks is not bounded by any record. Everything here is SIM (ngspice-44.2 in the
pinned KiCad image, vendor CSD18543Q3A model, generic small-part corner models) or CALCULATED. Nothing is measured.
Nothing in the repository changes with this run. electrical_acceptance stays **NOT ESTABLISHED**.

Written 2026-11-20, after three exploratory scans (`work/verify`, `work/explore1`–`explore3`, 940 decks, disclosed in
the record) that were used to pick the candidate, and before any deck of the sets below was run.

## The candidate (C1): only the +12 V / +5 V firing RC changes

| Ref | As drawn | Candidate C1 | Line (existing in `inventory.json`) |
| --- | --- | --- | --- |
| RDG12, RDG5 | 10 kΩ 1 % (C25804) | 4.02 kΩ 0.1 % | `line-c705781` RT0603BRD074K02L, R0603 |
| CDG12, CDG5 | 22 nF X7R 10 % (C1729) | 27 nF C0G 5 % | `line-c3882413` GRM2165C1H273JA01D, C0805 |
| R61, R62, C44, C45 (the −12 V network) | 4.7 kΩ, 47.5 kΩ, 47 nF C0G, 22 nF X7R | unchanged | |

Nominal τ falls from 220 µs to 108.5 µs. The −12 V network is deliberately untouched, so the earliest discharge onset
(the disconnect-before-discharge margin) does not move.

## Deck changes against the published `d2_sequencer_circuit` decks

`d2_threshold_band.py` edits the published deck text and nothing else in it:
1. **Threshold corners on the vendor model.** Each discharge switch gets a series gate source. The vendor model reads
   2.2036 V at VDS = VGS, ID 250 µA (`work/char/vth.cir`); the source shifts that to the corner value. The whole transfer
   curve shifts rigidly, which is an ASSUMPTION. Corners: 1.5 V and 2.7 V
   (`fact-c840100-vgs-th-min`, `fact-c840100-vgs-th-max`, 25 °C only), typical 2.0 V (`fact-c840100-vgs-th-typ`).
   Q51 and Q52 move together. Q55 moves independently.
2. **Part tolerances.** Early corner: R and C at their low tolerance. Late corner: R and C high, plus 265 pF
   (`fact-c840100-ciss-max` 1150 pF over the 885 pF typical). R62 moves the way that helps the corner.
3. **Drive level.** The published decks drive DIS_P / DIS_C at 4.9 V. The schematic cannot reach that: EN_E is
   P5_SUP × 100k / 104.7k = 4.756 V at 4.98 V, and CDH charges through the Q57 body diode. The band used here is
   4.10 V with the late Q51/Q52 corner, 4.65 V with the early corner and 4.40 V nominal (CALCULATED from P5_SUP ± 2 %
   and a 0.2–0.6 V diode drop, both PA; `calculate-board-b20-draft.py` already uses 4.156 V).
4. R62 is 47.5 kΩ and CDGN is 47 nF + 22 nF, as fitted.

Solver settings, the EN_N edge, the timing origin and the run rule are unchanged: a deck that does not complete is
recorded as ABORTED and is not retried.

## Sets (5,112 decks)

| Set | Network | Thresholds | Decks |
| --- | --- | --- | --- |
| **G** (verdict) | C1 | mixed corners (Q51/Q52 late + Q55 early; Q51/Q52 early + Q55 late) over all 4 sequencer combos × 9 banks × 27 load corners (1,944); same-direction corners (576) and nominal (288) over the 8 load corners with every rail at 0 or maximum | 2,808 |
| **CTL** (positive control) | as drawn | mixed corners, 4 combos × 9 banks × 8 extreme load corners | 576 |
| **PA-HOT** (reported band) | C1 | as CTL grid, all three thresholds −0.30 V (typical 85 °C shift from `fact-c840100-vgs-th-temperature-curve`, applied to the guaranteed corners; one board, one temperature), C45 at −15 % and −25 % DC bias (early) or +15 % (late) | 576 |
| **PA-COLD** (reported band) | C1 | as PA-HOT with +0.12 V (typical 0 °C) | 576 |
| **L49** (reported, comparability) | C1 | as CTL grid with the published 4.9 V drive in both corners | 576 |

## Reading rule (fixed now, before any result)

Rows are the five fast-discharge rows, read by the unchanged `d2_fast_discharge.read`: disconnect before discharge,
disconnect skew, the discharge levels within 100 ms, R-VEE in both directions, and the direct hazard. One row is
added for this candidate:
- **onset floor:** the earliest discharge onset in G is no earlier than the earliest onset in CTL minus 1 µs (the
  solver step).

Each set gets its own reading:
- **PASS (SIM):** every row holds in every deck of the set, and all are COMPLETE.
- **FAIL (SIM):** any row fails in any COMPLETE deck. The failing count and rows are listed.
- **NOT FORMED:** no row fails, but at least one deck did not complete.

The verdict on the candidate is the reading of **G** together with the onset floor. CTL, PA-HOT, PA-COLD and L49 are
reported with their own readings and do not change the verdict; a FAIL in a PA set is a recorded residual.

**Reported, not read:** smallest |−12 V| while +12 V is present, largest |−12 V| once +12 V is absent, onset and level
times, peak currents and resistor energies.

## Expectation (stated before the run, not a criterion)

- G: PASS. On 432 exploratory decks C1 held at least 0.742 V while +12 V was present and at most 5.652 V once it was
  absent, with the earliest onset at 24.3 µs.
- CTL: FAIL at the high-+12 V / low-−12 V banks with −12 V at maximum load (0.19 V on 16 exploratory decks).
- PA-HOT: PASS. PA-COLD: FAIL or within 0.03 V of the 0.6 V level. L49: PASS, but close to the 6 V side.

## What a PASS supports and what stays open

A PASS supports C1 across the guaranteed 25 °C threshold band and the part tolerances, at the stated drive band, with
generic small-part models. These stay open whatever the reading:
- the drive level and any threshold bound away from 25 °C are not sourced;
- the deck's disconnect is ideal (it completes before the EN_N crossing), so the real disconnect-to-discharge margin
  is not shown;
- Q52 is not moved against Q51;
- resistive loads, the rigid-shift ASSUMPTION, layout parasitics on top of this band, and the bench check.

## Amendment 1 (2026-11-20, after sets CTL and G were read, before set CTL-SAME was run)

The onset-floor row compares G with CTL, but CTL has only the mixed corners, where the early Q55 corner is always
paired with the 4.10 V drive. G also has the same-direction corners, where the early Q55 corner is paired with 4.65 V,
and a higher drive fires Q55 earlier in both networks. The row as worded therefore compares unlike corners.

- **As worded, the row is NOT MET:** G 23.202 µs against a floor of 24.401 − 1 = 23.401 µs. This is recorded and stands.
- **Amended control:** set **CTL-SAME** is the as-drawn network at the same-direction corners over the CTL grid
  (576 decks). The amended row reads: the earliest onset in G is no earlier than the earliest onset in CTL ∪ CTL-SAME
  minus 1 µs. CTL-SAME gets its own reading and does not change any other row.

Nothing else changes. Sets PA-HOT, PA-COLD and L49 were already dispatched under the original text.
