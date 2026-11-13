# Phase 33 deck stiffness: the 11 aborts share one cause, timestep collapse inside vendor macros at a few deck-wide events

Diagnosis only, from the logs and waveforms already retained. Nothing was dispatched, and no solver option or
deck was changed. ABORTED stays not evaluated.

Sources:
- T2 attempt 1: run 43122081181, artifact 13902530334 ([record](d1-t2-attempt1-20261112.md)).
- Gap attempts 1 and 2 ([d1-gap-attempt2-20261111.md](d1-gap-attempt2-20261111.md)).
- The baseline identity run nom/adv, ladder-809hzsa1 in the same artifact.

## Every abort is in an unchanged vendor macro, never in an added element
| Case | Abort time | Node | Subcircuit | Event class |
| --- | --- | --- | --- | --- |
| t2load/nomR | 0.827 ms | unrecorded | — | A: supply ramp |
| e5lo | 1.994 ms | xu13a.n2992151 | OPA2187 (U13A) | A: supply ramp |
| t2lo/nom | 2.138 ms | unrecorded (the log prints xt2a.x_u36.3) | OPA2187 (T2 buffer) | A: supply ramp |
| t2hi/nom | 2.138 ms | xq1.xcgd.g1_int1 | CSD18543Q3A Q1, Cgd network | A: supply ramp |
| e12lo | 3.068 ms | xq1.xcds.g1_int1 | CSD18543Q3A Q1, Cds network | B: driver reaches its rail |
| e12hi | 3.068 ms | xu13b.n2992151 | OPA2187 (U13B) | B: driver reaches its rail |
| gap attempt 1, g20 | 3.068 ms | xu13a.n2992151 | OPA2187 (U13A) | B: driver reaches its rail |
| e5hi | 62.447 ms | xu13b.n2992151 | OPA2187 (U13B) | C: +12 / +5 enable edge |
| t2/nom | 101.275 ms | xq1.10 | CSD18543Q3A Q1 | D: gate drives snap off |
| gap attempt 2, +5 V g20 | 101.275 ms | xq1.10 | CSD18543Q3A Q1 | D: gate drives snap off |
| gap attempt 2, g12 | 247.685 ms | xq5.10 | CSD18543Q3A Q5 | D: after the 240 ms disable |

- **Only two macros are involved:** the CSD18543Q3A model, through its internal nonlinear-capacitance networks
  (xcgd/xcds g1_int1) and node 10, and the OPA2187 model's internal node n2992151.
- **Only one abort touches a T2 element at all.** t2lo prints xt2a, which is again the OPA2187 macro.
- **Three pairs abort at the same instant,** to within 0.1 µs, in different decks: 3.068 ms, 2.138 ms and
  101.275 ms. An abort time is a property of the deck, not of the perturbation.

## The unmodified baseline nearly fails at the same events
The baseline's smallest accepted steps already fall to about 1e-10 s at the same instants. The aborts collapse
further, to 2.5e-18 s.

| Run | Smallest steps (time, step) |
| --- | --- |
| Baseline nom | 1.032 ms (9.7e-11 s), 2.000 ms (9.8e-11 s), 95.94 ms (1.1e-10 s), 101.275 ms (8.9e-11 s), 188.21 ms (2.3e-11 s), 190.61 ms (1.0e-10 s) |
| Baseline adv | 1.035 ms (4.4e-11 s), 90.006 ms (4.4e-11 s), 190.47 ms (3.7e-11 s) |

The baseline log's progress prints cluster at 3.0675, 62.4458 and 101.274–101.275 ms.

## The events
- **A, 0.8–2.2 ms. All six supply PWLs reach full value at the same 2 ms corner.** These are VIN, VSUP, VREF and the
  three rail sources. The input-capacitor charging current collapses there, from −0.347 A to −7e-9 A on +12 V.
- **B, 3.07 ms. The −12 V driver output reaches its negative rail** (m12_drv −12.136 V). The OPA2187 macro's
  output-saturation node and Q1's capacitance networks switch region together.
- **C, 62.45 ms. The +12 V and +5 V gates pass about 2.1–2.4 V,** at their enable edge.
- **D, 101.27 ms and 247.7 ms. The gate drives snap off.** At 101.27 ms all three drivers collapse together
  (p12_g, p5_g and m12_g to their off levels). At 247.7 ms Q5 turns off after the disable.

## Conclusion: deck stiffness is its own item
**The aborts are not caused by the corners or by T2.** Any perturbation, even a VO threshold offset with no other
change (the corners), moves the step sequence onto a near-singular point. The baseline happens to step over that point
at about 1e-10 s.

**What this means for results.** A case that aborts says nothing about its candidate. A case that completes is
still a single solver path through the same events.

## Proposal, not admitted: a matched-variant ladder that keeps the identity control meaningful
- **Keep the hash-identity runs exactly as they are.** nom/adv and the loaded baselines on the recorded options stay
  the only identity control. Nothing is re-hashed.
- **For a case that aborts, run it once under a pre-registered solver variant.** Run its own unmodified baseline
  under the same variant in the same dispatch.
- **Use the variants already accepted for this deck family, in a fixed order:**
  1. the reR6 abstol swap;
  2. the reR20 rshunt swap.
  
  The first variant whose matched baseline qualifies is used, and there is no further search.
- **A variant baseline qualifies only if it reproduces the recorded baseline** to within the L2 tolerance
  (1e-3·|v| + 1e-5 V on every rail, over the whole run), with the rule-1 slope and current equal to the record
  within a pre-registered relative bound. If it does not, the case stays ABORTED.
- **The candidate is then judged against its matched variant baseline,** not against the original. The identity
  chain is: the original hash, then the variant baseline matching the original within tolerance, then the
  candidate.
- **Rejected alternative.** Smoothing the 2 ms supply corners or slowing the gate snap would change the baseline
  deck itself, and so break the identity control.

This needs owner admission and its own pre-registration. The second T2 dispatch stays reserved.
