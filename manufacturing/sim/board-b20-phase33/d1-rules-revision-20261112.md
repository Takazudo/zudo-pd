# Rules 6 and 9 revised for future pre-registrations; L2 unchanged; no recorded verdict changes

**Adopted 2026-11-12 by owner decision:** Takazudo, "ok go with that", answering the proposal below. The revision
applies only to pre-registrations made from now on. Every pre-registration already made, and every verdict already
recorded, stands as recorded. The contract values are unchanged.

## The revised rules, as adopted
- **Rule 6 (enable edge), two parts. Both must hold.**
  - **(a) Contract screens, absolute.** In the enable window (40–110 ms):
    - +5 V stays below the recorded 0.8 V conjunction quantity;
    - each analog rail's magnitude stays below 1.5 V.

    Both numbers are from the canonical OSC interface `433c88b` (`execution-20261110.md`).
  - **(b) Difference from baseline.** The excursion beyond the baseline's enable-window extreme, of either
    polarity, is at most reltol·|v_baseline| + vntol. With the decks' 1e-3 and 1e-5 V, that is 107 µV at the −12 V
    enable floor.
- **Rule 9 (disable edge).** The after-disable excursion beyond the pre-edge extreme is at most reltol·|v_pre| +
  vntol, which is 12.15 mV at −12.14 V. The reverse-direction part (not passing the baseline disabled level) uses
  the same tolerance at that level.
- **L2 is unchanged.** It already uses reltol·|v| + vntol.
- **All other rules are unchanged.** That includes rule 1's contract ceilings and rule 7's 5 mA conduction
  criterion.

## Why
Rules 6 and 9 were pre-registered in `d1-gap-criteria.md` (PR #261) as "indistinguishable from baseline" at the
decks' vntol, 1e-5 V. They do not trace to a PD20 contract number.

SPICE accepts a node voltage at reltol·|v| + vntol. The old rule 6 therefore asked for 1/11 of the convergence
tolerance at the −12 V enable floor, and the old rule 9 asked for about 1/1200 of it at −12.14 V. At that level,
the inert loading of any added element (4.2 µV for T2) used up most of the budget.

The full origin, contract context and proposal are kept below, unchanged from the paper that was adopted.

---

# Rules 6, 9 and L2: none traces to a PD20 contract number; rules 6 and 9 sit at or below the solver's own convergence tolerance

*(The proposal as written before adoption. Its "not in force" status ended with the owner decision above, for future pre-registrations only.)*

## Where each bound came from
| Rule | Introduced | What it protects | Bound | Contract number? | Relation to vntol |
| --- | --- | --- | --- | --- | --- |
| 6. Enable edge: the enable-window (40–110 ms) output extremes stay within the baseline's, either polarity | `d1-gap-criteria.md`, pre-registered 2026-11-11 in PR #261 (C1 gap sensitivity); carried into `d1-t2-criteria.md` (PR #268) | A correction must not move the output during the enable transient. That is where a pedestal or early output would show | Baseline extremes, resolved to 1e-5 V | **No.** Chosen as "indistinguishable from baseline". The criteria report the nearest contract quantity beside the verdict and say it does not change the verdict. For −12 V, "None recorded" | Threshold = vntol (1e-5 V) |
| 9. Disable edge: after 240 ms the output does not exceed its pre-edge extreme, nor pass the baseline disabled level in reverse | Same, PR #261 | A correction must not push the output at disconnect (the disconnect-before-discharge order) | Pre-edge extreme, resolved to 1e-5 V | **No.** The contract states the order, not an amplitude | Threshold = vntol |
| L2. Loaded: outputs within reltol·\|v\| + vntol of the loaded baseline, per 2 µs bin | `d1-t2-criteria.md`, PR #268 | The candidate is inert under full load at startup and re-enable | 1e-3·\|v\| + 1e-5 V | **No.** Taken from the decks' own `.options` | Equals SPICE's convergence tolerance at that voltage |

**What the solver actually resolves.** SPICE accepts a node voltage when successive iterations differ by no more
than reltol·|v| + vntol. The decks use reltol 1e-3 and vntol 1e-5 V, so:
- at the −12 V enable floor (|v| ≈ 97 mV), the solver resolves **107 µV**, and rule 6 asks for 10 µV;
- at −12.14 V, it resolves **12.15 mV**, and rule 9 asks for 10 µV, about 1/1200 of the convergence tolerance;
- L2 already uses this tolerance.

## The contract at those points, and what T2 attempt 1 measured against it
| Contract quantity (source) | Limit | T2 attempt 1 (t2/adv unless stated) | Size of the failing difference against it |
| --- | --- | --- | --- |
| −12 V no-load exception slope, adopted 2 µs refinement | ≤ 1.47 V/ms | 1.064 V/ms (baseline 1.475, recorded failure) | — (rule 1 passes) |
| −12 V no-load exception current | ≤ 265 mA | 191.5 mA | — |
| −12 V exception voltage region | magnitude ≤ 0.75 V | enable-window minimum −97.29 mV | Rule 6's 135 µV is 0.018 % of 0.75 V |
| Analog-rail presence threshold, canonical OSC interface `433c88b` (`execution-20261110.md`) | 1.5 V | −12 V magnitude 97.3 mV in the enable window | 135 µV is 0.009 % of 1.5 V |
| +5 V hazard conjunction (+5 V above 0.8 V while one analog rail is below 1.5 V and the other at least 8 V) | 0.8 V | Not tested on +5 V by T2. +5 V passes its screen (rule 2) | — |
| Disconnect before discharge (contract order, no amplitude) | Order holds | Rule 8 passes (gate held off, Vgs −0.51 V); rule 9's kick is 10.026 µV at −12.14 V | 0.8 ppm of the rail. The inert control is identical |
| L2, reR6 / reR20 startup and re-enable | No contract amplitude | 0.32 mV at an output near −33 mV, during the edge | L1 passes. 0.32 mV is 0.02 % of the 1.5 V threshold |

## Proposed replacements (a proposal, not in force)
Each bound comes from SPICE's own convergence tolerance or from a contract number, not from the candidate's
result.

- **Rule 6, two parts.**
  - **(a) Contract screens, absolute.** In the enable window, +5 V stays below the recorded 0.8 V conjunction
    quantity, and each analog rail's magnitude stays below 1.5 V. These are the existing contract numbers.
  - **(b) Difference from baseline.** The excursion beyond the baseline extreme is at most reltol·|v_baseline| +
    vntol, the same tolerance L2 uses. At the −12 V floor that is 107 µV.
- **Rule 9.** The after-disable excursion beyond the pre-edge extreme is at most reltol·|v_pre| + vntol, which is
  12.15 mV at −12.14 V. The reverse-direction part (not passing the baseline disabled level) keeps the same
  tolerance at that level.
- **L2.** No change. It is already the convergence tolerance.
- **Not proposed:** a fixed multiple of vntol. At a 12 V rail it would still be about 1000× below what the solver
  resolves.
- **How it would apply.** Only to pre-registrations made after adoption. Recorded verdicts stay as recorded. Any
  re-evaluation of old runs is labelled as such.

## What would and would not change in the recorded verdicts
| Record | Recorded | Under the proposal | Why |
| --- | --- | --- | --- |
| D1 failures (+5 V 0.954850860 V/ms / 114.510041 mA; −12 V 1.474778000 V/ms / 265.259332 mA) | FAIL | **Unchanged: FAIL** | Rule 1 / contract ceilings, not touched |
| C1 gap attempt 2, −12 V g20 | FAIL (rule 6 by 12.2 µV) | **Would pass all rules** | 12.2 µV < 107 µV |
| C1 gap attempt 2, −12 V g16 | FAIL (rule 6 by 55.6 µV) | **Would pass all rules** | 55.6 µV < 107 µV |
| C1 gap attempt 2, g12 / +5 V | ABORTED / not evaluated | Unchanged | — |
| C1 as a design | REJECTED by owner decision | **Unchanged: REJECTED** | It was rejected on threshold dependence (no fixed floor fits the 1.5–2.7 V window). The record says its microvolt rule 6 results are not the reason |
| C2 minimum-load bleeder | REJECTED | **Unchanged** | DC infeasibility, or defeating disconnection |
| T1 integrator leak | REJECTED by construction | **Unchanged** | DC balance, threshold-dependent pedestal |
| T2 attempt 1, rule 6 | FAIL (135.4 µV) | **Still FAIL** | 135.4 µV > 107.2 µV, over by 28 µV |
| T2 attempt 1, rule 9 | FAIL (by 26 nV) | Would pass | 10.026 µV ≪ 12.15 mV |
| T2 attempt 1, L2 | FAIL (0.32 / 0.31 mV) | **Still FAIL** | L2 is unchanged |
| T2 attempt 1, overall | FAILED | **Still FAILED.** Even with every rule passing, it would be NOT EVALUATED | Four of its no-load cases aborted (t2/nom, t2lo, t2hi, t2load/nomR) |
| T2 on +5 V | REJECTED by construction (RG2P) | Unchanged | Not a rule question |

**The proposal rescues no candidate that is still in play.** T2 stays failed, and the only verdicts that flip are
two C1 cases on a design already rejected for another reason. It would, however, make a T2 revision admissible in
principle.
- **Rule 6 budget:** 107 − 4.2 µV of loading = 103 µV, or 51 µV with 2× margin.
- **Clamp diode limits that follow,** with the requirements note's 2 : 1 split between coupling and leakage:
  - with option 1, 34 µV for coupling: 2.1 pC, an average Cd of about 0.36 pF or less over 0–5 V;
  - 17 µV for leakage: a guaranteed IR of about 0.4 nA or less at 5 V, over temperature.
- **Whether a sourced part meets that is open.** That would be the next question, after the user's decision.
