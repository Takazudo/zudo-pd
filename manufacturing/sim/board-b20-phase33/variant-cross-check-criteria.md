# D1 pinned-versus-variant cross-check: what is measured and how it is read, stated before the dispatch

**This is a diagnostic, not a verdict run.** It judges no candidate, changes no ceiling and adopts no exception.
electrical_acceptance stays **NOT ESTABLISHED**, the recorded D1 failures stay failures, and D1 stays a pre-order
hold. The proposed 350 / 160 mA current-form exception is not adopted. The rejected Miller approach stays rejected,
and T2 rev 3 stays parked.

## The gap it closes
The OSC-bank and ceiling-corners criteria both meant to rerun one pinned-COMPLETE deck under each matched-variant
step and report the pinned-minus-variant difference. In both runs that deck's pinned run aborted, so the cross-check
was never formed ([audit](d1-diagnostic-audit-20261113.md)). Most of those runs' rows were measured only under the
matched variant, so no in-run evidence shows that variant rows can be read like pinned rows.

## What runs
The two decks of the identity pair, exactly as `extract_reference.derive_decks()` builds them (`executed`): the 2 µs
refined `nom` and `adv` with the two output-only lines. They complete pinned in every dispatch, because the workflow's
identity control requires them to reproduce the retained 2026-11-09 refinement byte for byte before any later step
runs. They carry no T2 rev 2 no-load additions and use the contract ceiling bank (180 / 120 / 180 µF).

Each deck is rerun once under each matched-variant step that applies to it, with `--original-only`. The edit is the
same single-option substitution as `osc_bank.VARIANTS`, and nothing else changes; itl4 stays pinned.

| Label | Deck | Edit |
| --- | --- | --- |
| `abstol-nom` | `nom` | `abstol=1e-9` → `abstol=1e-8` |
| `abstol-adv` | `adv` | `abstol=1e-9` → `abstol=1e-8` |
| `rshunt-nom` | `nom` | `rshunt=1e10` → `rshunt=1e9` |

`adv` already runs at `rshunt=1e9` (its accepted baseline variant), so it has no rshunt row. That is recorded as not
applicable, not as unknown.

The pinned side of every pair is the identity run of the same dispatch, so both sides share the image, solver,
`.spiceinit`, model hashes and execution revision. A variant deck that aborts is recorded with its parsed abort line
and is not retried.

## Measured
For both sides of every pair, on every rail: the `osc_bank.rail_metrics` quantities over the refinement window
(40–234.5 ms), unchanged from [`osc-bank-criteria.md`](osc-bank-criteria.md). That includes the peak slope inside
and above the exception region, the peak ESR-branch current in the region and over the window, the charge in the
region and the current half-width. Each pair reports the difference variant − pinned, and its size relative to the
pinned value.

## Reading rule (fixed now, before any result)
Each pair is read on the two exception rails only (+5 V region ≤ 0.45 V, −12 V region |V| ≤ 0.75 V), using the two D1
quantities: the peak slope inside the region and the peak ESR-branch current inside the region.

- **COMPARABLE.** Both sides COMPLETE, and on both rails both quantities differ by at most **0.01 %** of the pinned
  value.
- **NOT COMPARABLE.** Both sides COMPLETE, and any of the four differences is larger than 0.01 %.
- **NOT FORMED.** Either side is not COMPLETE.

**Why 0.01 %.** The smallest recorded D1 exceedance is the −12 V current, 265.259332 mA against 265 mA, which is
0.10 %. A solver-setting difference must be at least ten times smaller than that before a variant row can be read on
the same side of a ceiling as its pinned twin.

**What a COMPARABLE reading supports.** On these two decks, the matched-variant step moves the D1 quantities by less
than the reading bound. That makes the labelled variant rows of the OSC-bank and ceiling-corners runs more readable,
but does not prove them. Those decks differ: they carry the T2 rev 2 no-load additions, other banks, enable-edge
corners or a `.temp` line. A variant row stays labelled as a variant row, and no variant row becomes a pinned
waveform.

**What a NOT COMPARABLE or NOT FORMED reading means.** The variant rows of those runs stay unconfirmed. The +12 V
rail and the other quantities are reported but are outside the reading.

The reading compares two solver settings. It says nothing about the circuit's margin to any ceiling.

## Expectation (stated before the run, not a criterion)
- **All three pairs COMPARABLE.** The ceiling run's variant `nom` (+5 V) and `adv` (−12 V) rows lay within
  3.1e-6 V/ms and 0.0005 mA of the recorded pinned D1 failures. That is about 0.0003 % and 0.0002 %, across runs and
  decks.
- **No variant deck aborts.** Every variant step completed where it was tried on these deck families.
