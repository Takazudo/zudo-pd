# Startup slope refinement — 2026-11-09

**PRE-ORDER HOLD: the available model does not establish compliance with the
adopted no-load exception ceilings.** This is a model finding, not a measured
physical violation. No exception, excess-current charge/time budget or component
substitution is adopted by this report.

The six complete 5 us startup waveforms at baseline
`fda0667df503aa7cdc8ec0d45920dd4c731dc56c` pass the strengthened waveform-integrity
checks. Adjacent-sample analysis exposes peaks hidden by the retained 50–100 us
windowed metrics: nominal +5 V reaches 0.954752161 V/ms and adverse -12 V reaches
1.474624628 V/ms. Their recorded no-load exceptions are 0.95 V/ms below 0.45 V
and 1.47 V/ms below 0.75 V respectively. Loaded startup cases have no
adjacent-sample slope exceedances in these model runs; that is not full interface
acceptance.

Only `nom` and `adv` were refined, keeping circuit, models, tolerances and solver
method unchanged while reducing maximum step from 5 us to 2 us. Separate
output-only ESR-node vectors leave the strict 22-column primary waveforms
unchanged. The refinement starts from each baseline's **accepted executed
deck**: `nom` retains original `rshunt=1e10`, while `adv` retains the baseline's
selected `rshunt` fallback (`rshunt=1e9`). Both refined runs completed without
any further fallback. Thus `--original-only` means the supplied accepted deck,
not a claim that the adverse baseline used its original solver settings:

| Case / rail | Adjacent peak at 2 us | Recorded ceiling | OSC capacitor branch peak in exception voltage region | Recorded current ceiling |
| --- | ---: | ---: | ---: | ---: |
| nom / +5 V | 0.954850860 V/ms | 0.95 V/ms | 0.114510041 A | 0.114 A |
| adv / -12 V magnitude | 1.474778000 V/ms | 1.47 V/ms | 0.265259332 A | 0.265 A |

The small excess persists across these two timestep settings. This does not
bound continuous-time behavior, establish macromodel accuracy, or prove physical
failure. Further design/model disposition is required before claiming the
adopted exceptions are satisfied. Source-current peaks are not substituted for
OSC capacitor current: the latter comes from the same-run voltages across the
explicit 50 mOhm ESR branches. These are model capacitor currents, not maximum
fault-delivered-current qualification. Small negative voltage increments remain
visible; no numerical monotonicity tolerance is silently introduced.

`startup-refinement-20261109.json` contains exact source/deck/model/tool/output
hashes, solver identity, supplemental waveform hashes, sample counts, time and
voltage endpoints, and the preparation receipt. Large raw waveforms remain local
under `tmp/startup-refinement/`. The original 14-case baseline is untouched.

To reproduce into a fresh destination after recovering the baseline inputs:

```sh
python3 manufacturing/sim/board-b20-phase33/prepare_refinement.py \
  /absolute/path/to/baseline/phase33-execution tmp/startup-refinement-new
bash "$HOME/.codex/scripts/heavy-guard.sh" -- \
  bash manufacturing/sim/board-b20-phase33/run_ladder.sh \
  "$PWD/tmp/startup-refinement-new/tracking" nom --original-only
bash "$HOME/.codex/scripts/heavy-guard.sh" -- \
  bash manufacturing/sim/board-b20-phase33/run_ladder.sh \
  "$PWD/tmp/startup-refinement-new/tracking" adv --original-only
python3 manufacturing/sim/board-b20-phase33/analyze_refinement.py \
  tmp/startup-refinement-new --output tmp/startup-refinement-new/analysis.json
```

A failed/incomplete run is not accepted; retain and disposition it rather than
mixing its outputs with another run. The audit requires exactly one complete
original-only run per requested case and validates supplemental/main time grids.
Since 2026-11-11 it also binds the copies the solver actually mounted for the
selected attempt (`<run>/<case>/0/lib/**` and `<run>/<case>/0/tracking/.spiceinit`)
to the runner `inputs/` snapshot and the preparation receipt: a missing,
extra, symlinked or altered executed copy is rejected by name. Failed attempts
are retained but not analyzed. Receipts written before this check are not
rewritten; the 2026-11-09 figures above came from an independent review of the
executed copies, and a fresh committed-tool audit of those runs requires their
original raw directories, which are not in Git.
