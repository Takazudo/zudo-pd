# D1 −12 V `adv` without the rshunt step: what runs and how it is reported, stated before the dispatch

**This is a diagnostic, not a verdict run.** It changes no ceiling, adopts no exception and does not replace the
recorded D1 failure. electrical_acceptance stays **NOT ESTABLISHED**, and D1 stays a pre-order hold.

## Why
The recorded −12 V D1 failure (1.474778000 V/ms and 265.259332 mA) comes from `adv`. On 2026-11-09 the pinned `adv` at
`rshunt=1e10` aborted, so its accepted baseline runs at `rshunt=1e9`. The
[pinned-versus-variant cross-check](d1-variant-cross-check-20261113.md) found:
- the rshunt step is NOT COMPARABLE: on `nom` it moved the −12 V quantities by about 0.39 %;
- the abstol step is COMPARABLE: within 0.0007 % on both decks.

This run asks what `adv` gives at `rshunt=1e10` when only the comparable abstol step is applied.

## What runs
Both decks start from the identity pair's executed `adv` deck. It is rebuilt by `extract_reference.derive_decks()`,
and the identity control requires it to reproduce byte for byte before this step runs.

| Label | Edit to the executed `adv` deck | Entry |
| --- | --- | --- |
| `r10-adv` | `rshunt=1e9` → `rshunt=1e10` only. This is the pre-fallback setting, with the 2 µs refinement and the two output lines | pinned settings, once |
| `abstol-r10-adv` | `rshunt=1e9` → `rshunt=1e10` and `abstol=1e-9` → `abstol=1e-8` | abstol variant, once |

Each runs once with `--original-only`. An abort is recorded with its parsed abort line, and nothing is retried. No
other option changes, and itl4 stays pinned.

## Reported
- **Measurements.** The `osc_bank.rail_metrics` quantities on all three rails over 40–234.5 ms, for each completed
  deck.
- **Comparison.** For each completed deck, the difference from the same dispatch's identity `adv` (`rshunt=1e9`).
- **The −12 V D1 pair.** The in-region peak slope and in-region peak current, with the setting each was measured under.

## How it is read (fixed now)
- **Labelling.** An `abstol-r10-adv` figure is a matched-variant row. It is labelled as such and is never presented as a
  pinned waveform.
- **No judgement against ceilings.** A figure below 1.47 V/ms or 265 mA is reported, never read as a pass. It does not
  replace or withdraw the recorded failure.
- **What it does inform.** How much of the −12 V exceedance the adopted rshunt setting could account for. That feeds
  the owner's D1 route decision and the OSC note.
- **Pinned completion.** If `r10-adv` completes pinned, that row is reported as pinned. The 2026-11-09 abort stays
  recorded, because the earlier ladder was a different run.

## Expectation (stated before the run, not a criterion)
- `r10-adv` aborts again, as on 2026-11-09.
- `abstol-r10-adv` completes, as every abstol row on this deck family did.
- Its −12 V in-region slope and current fall by roughly 0.4 % from the recorded figures, as on `nom`, but the sign
  and size on `adv` are not known.
