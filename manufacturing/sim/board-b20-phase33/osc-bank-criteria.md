# OSC-bank baseline diagnostic: what is measured, stated before the dispatch

**This is a diagnostic, not a verdict run.** It judges nothing, changes no ceiling and admits no candidate. Its
output is input to a proposal to OSC that would restate the no-load start-up exception as a current limit with
margin. The owner authorised one dispatch on 2026-11-12 (D1 contract route). electrical_acceptance stays NOT
ESTABLISHED, and the recorded D1 failures stay failures. The D1 record at 180 / 120 µF is unchanged.

## Why the bank changes
- The D1 decks load each rail with the OSC contract's capacitance ceiling: 180 / 120 / 180 µF on +12 / +5 / −12 V.
- OSC's owner-reported fitted bank is much smaller: 49.9 / 24.5 / 42.2 µF, all MLCC. The source is
  `zudo-osc-hole-field` power-contract README L262/L273 Q6, read on 2026-11-12 at `05b1498`.
- The contract sets no minimum load capacitance.
- A catch-up step limited by transconductance may be steeper in V/ms into a smaller bank while drawing less current.

## What runs
- **The baseline only.** It is the unmodified circuit, with no T2 and no candidate.
- **Six cases.** nom and adv as executed in the identity pair, plus the four enable-edge corners e12lo, e12hi, e5lo
  and e5hi (VO shifts −0.66 / +0.54 V, as in T2 rev 2).
- **The edits.** Each case carries the T2 rev 2 no-load additions: the 240 ms disable and the gate/source output.
  The only other change is the three OSC bank capacitors, `CL12`, `CL5` and `CLN`.
- **Three bank scales.** The fitted value × 0.8, × 1.0 and × 1.2. That is the contract's 20 % capacitance tolerance
  applied both ways. The ESR stays at 50 mΩ, the deck's measuring branch.

| Scale | +12 V | +5 V | −12 V |
| --- | --- | --- | --- |
| lo | 39.92 µF | 19.6 µF | 33.76 µF |
| nom | 49.9 µF | 24.5 µF | 42.2 µF |
| hi | 59.88 µF | 29.4 µF | 50.64 µF |

That makes 18 decks, one per label. Each runs once at pinned settings with `--original-only`.

**Aborted decks.** A deck that aborts is recorded with its parsed abort line. It then enters the labelled
matched-variant ladder from T2 rev 2:
1. abstol 1e-9 → 1e-8;
2. if it still aborts, rshunt 1e10 → 1e9 (where the deck has that option; adv already uses 1e9).

A variant row is labelled as such and is never presented as a pinned waveform. No other solver option changes. In
particular the itl4 inertness result is reported beside this run but is not folded into it.

## Measured on every rail of every completed deck
All measurements use the refinement's window, 40–234.5 ms.

| Quantity | Definition |
| --- | --- |
| Peak slope inside the region | Largest adjacent-sample \|dV/dt\| over segments whose both ends lie inside the no-load exception voltage region: +5 V ≤ 0.45 V, \|−12 V\| ≤ 0.75 V. +12 V has no exception and is split at 0.75 V for reporting only |
| Peak slope above the region | The same over every other segment |
| Peak current in the region | Largest OSC ESR-branch current (v across the 50 mΩ / 0.05) at samples inside the region. This is the quantity OSC checks against its transient minima: 1900 mA (−12 V), 400 mA (+5 V) |
| Peak current | Largest ESR-branch current over the whole window |
| Charge in the region | Trapezoid integral of that current over sample pairs inside the region. For an ideal bank it is C × the region voltage |
| Current half-width | Width of the contiguous span around the in-region current peak where the current stays at or above half that peak |

Also reported: the worst value of each quantity across completed decks, with its deck; and the labels with no
completed run (**unknown**).

## Reproduction check of the measurement code (before the dispatch)
On the recorded refinement pair (run 43187732133), the measurement code reproduces the recorded D1 figures:
- −12 V adv: 1.474778 V/ms and 265.259 mA in the region;
- +5 V nom: 0.954851 V/ms and 114.510 mA.

## Expectation (stated before the run, not a criterion)
- **Current.** The in-region current should fall roughly with the bank, to about a third to a quarter of the
  180 / 120 µF figures.
- **Slope.** It should rise, but by less than the bank ratio, because the step is the pass FET catching up on its
  transconductance while the servo integrator ramps.
- **Region.** A step into a smaller bank may also run past the 0.75 / 0.45 V region. That would show up as a large
  above-region slope.
- **Corners.** The e5lo / e5hi corners aborted pinned at 180 / 120 µF, so I expect several aborts again.
