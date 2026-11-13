# D1 OSC-bank and ceiling-corners artifacts: both verified intact; the pinned cross-check was never formed

Audit and disposition of two completed diagnostic runs, 2026-11-13 UTC (2026-11-14 JST), [#289](https://github.com/Takazudo/zudo-pd/issues/289)
under [#235](https://github.com/Takazudo/zudo-pd/issues/235). Completed evidence was reused: nothing was rerun or
dispatched. Both diagnostics measure only. They judge no candidate and change no contract ceiling.
electrical_acceptance stays **NOT ESTABLISHED**. The proposed 350 / 160 mA current-form exception is **not adopted**.
The recorded D1 failures stay failures, and D1 stays a pre-order hold.

Records in this directory:
- `d1-osc-bank-20261112.json`: the run's `osc-bank.json`, byte for byte.
- `d1-ceiling-corners-20261112.json`: the run's `ceiling-corners.json`, byte for byte.
- `d1-osc-bank-audit-20261113.json` and `d1-ceiling-corners-audit-20261113.json`: the audit receipts.
- `audit_d1_bundle.py` writes the receipts from a downloaded archive. Its `check` command re-verifies them offline.
  `test_audit_d1_bundle.py` covers it with synthetic negative controls.

The archives (1.15 GB and 569 MB), waveforms and vendor models are not in the repository. The artifacts expire on
2026-12-12.

## Runs audited

| | OSC bank ([criteria](osc-bank-criteria.md)) | Ceiling corners ([criteria](ceiling-corners-criteria.md)) |
| --- | --- | --- |
| Workflow run, attempt | [43221578569](https://github.com/Takazudo/zudo-pd/actions/runs/43221578569), attempt 1, success | [43232694170](https://github.com/Takazudo/zudo-pd/actions/runs/43232694170), attempt 1, success |
| Execution revision | `8daa87f988d99abb02270827b47a4bb905177df9` | `391992840046121554320a4c58d3a5cbf2474c89` |
| Artifact | 13947214643 `phase33-d1-reference`, 1,146,786,597 bytes | 13953060177 `phase33-d1-reference`, 569,372,615 bytes |
| Archive SHA-256 (download = recorded digest) | `c26999933ee8bcae4aee79220846a1a24e9f627be58ac22860c76f8f42d173e7` | `026602ed06555b1191accf1e4042c3c515cfc9e6f79df825127013cc4c3fd3fd` |
| Bundle members against its `hashes.json` | 328 members, 327 listed, all match | 148 members, 147 listed, all match |
| Result file SHA-256 | `osc-bank.json` `5dcadb34…ffb5` | `ceiling-corners.json` `10a7e7f0…dd47` |

The criteria were read at each execution revision and on main at `e868593`:
- `osc-bank-criteria.md`, `osc_bank.py` and `run_ladder.py` are unchanged since `8daa87f`.
- Between `8daa87f` and `3919928`, the workflow and `extract_reference.py` gained only the ceiling-corners step and its
  collect glob. The other phase33 changes in that span are the #282 interface-diagnostics regeneration and tests. `ceiling-corners-criteria.md` and `ceiling_corners.py` did not exist at `8daa87f`; that run was the
  OSC dispatch alone.
- Nothing in the phase33 directory or the workflow changed between `3919928` and `e868593`.

## Integrity: VERIFIED for both runs

- **Archive.** Each download matches the digest and size GitHub recorded. Every member matches the run's own
  `hashes.json`, in both directions. No member holds vendor model bytes (no `lib/` path, no `.lib`/`.zip`).
- **Identity control.** REPRODUCED at the execution revision. The nom/adv decks and the main and supplemental
  waveforms are byte-identical to the retained refinement, and the solver identity matches.
- **Solver and models.** Every deck receipt names the same items:
  - image `kicad/kicad@sha256:18693567…`, `linux/amd64`, ngspice-44.2;
  - `.spiceinit` `65514f56…`;
  - the two model hashes in the run manifest;
  - the `original-only` policy, on a clean source.
- **Decks.** Every executed deck equals the deck that the run's own `derive_cases()` re-derives at the execution
  revision (18 / 18 OSC labels, 9 / 9 ceiling labels). Each variant deck differs from its recorded deck only by
  `abstol=1e-9` → `abstol=1e-8`.
- **Re-analysis.** The executed revision's analyzer was rerun offline on the extracted bundle (CPython 3.12.3).
  - It reproduces `osc-bank.json` byte for byte.
  - For `ceiling-corners.json`, every deck row, measurement, largest value, flag, hot-minus-cold difference and
    cross-check is identical. Only `model_temperature_terms` cannot be re-derived: it counts keywords in the vendor
    model files, which the bundle omits by design. The retained value is the run's own.
- **Per-deck receipts.** They record no source revision of their own; the per-deck `source_revision` is null. The
  binding to the revision comes from the run head, the identity control and the run manifest, which all agree.

## Pinned and variant rows: most measured rows are matched-variant, and they stay labelled

| Run | Pinned COMPLETE (measured pinned) | Pinned ABORTED, measured under matched variant abstol | Variant ladder by design |
| --- | --- | --- | --- |
| OSC bank, 18 labels | nom-adv, hi-adv | the other 16 | none |
| Ceiling corners, 9 labels | hot-adv | nom, adv, hot-nom, hot-e12hi, hot-e5hi | e5lo, e5hi, e12hi (pinned aborts recorded in run 43187732133) |

- No label is unknown in either run, and the rshunt step was never needed.
- Every variant row in both result files says `matched variant abstol (labelled, not pinned)`. No variant row is
  presented as a pinned waveform.

## The criteria's pinned-versus-variant cross-check was not formed in either run

Both criteria rerun `nom` under each variant step and report the pinned-minus-variant difference. The OSC criteria
call `nom-nom` "pinned COMPLETE"; the ceiling criteria say `nom` was "pinned COMPLETE in every earlier run". In both
runs the pinned `nom` **aborted**, so `variant_cross_check` holds only `{pinned: ABORTED, variant: COMPLETE}` with no
difference.
- OSC `nom-nom` aborted at 2.000 ms.
- Ceiling `nom` aborted at 247.65 ms, at `p5_g`, after the 40–234.5 ms measurement window. Under the criteria it is
  still ABORTED. It is not reinterpreted here.

**Consequence.** No in-run evidence shows that the abstol variant rows are comparable with pinned rows.

**Observation, not a substitute.** The ceiling variant rows `nom` (+5 V) and `adv` (−12 V) lie within 3.1e-6 V/ms
and 0.0005 mA of the recorded pinned D1 failures. Those are +5 V 0.954850860 V/ms / 114.510041 mA and −12 V
1.474778000 V/ms / 265.259332 mA. The variant rows give 0.954847995 V/ms / 114.510205 mA and 1.474774912 V/ms /
265.258874 mA. That comparison crosses runs and decks: the ceiling decks carry the T2 rev 2 no-load additions. It is
not the pre-registered cross-check.

## Results as recorded, unjudged

Recorded diagnostic measurements; none is a margin or a verdict.

- **Ceiling bank (180 / 120 / 180 µF).** No flag.
  - Largest in-region currents: −12 V 276.49 mA (e12hi, variant) and +5 V 132.99 mA (e5hi, variant).
  - The owner's flag lines are 300 / 140 mA.
  - The single pinned hot row, hot-adv at 82.1 °C uniform, gives −12 V 231.42 mA.
  - Temperature-keyword counts: the CSD18543Q3A model has `tnom` 2 and one each of `tc1`, `tc2`, `xti`, `kt1`, `kt2`
    and `ute`; the OPA2187 macro has one `temp`. Counts show reach, not effect.
- **OSC fitted bank (49.9 / 24.5 / 42.2 µF ±20 %).**
  - Largest in-region currents: −12 V 79.43 mA (hi-e12hi, variant) and +5 V 19.72 mA (hi-adv, pinned).
  - Largest in-region slopes: −12 V 1.5725 V/ms (lo-e12hi, variant) and +5 V 0.6707 V/ms (hi-adv, pinned).

## Disposition

- **Accepted as integrity-verified diagnostic evidence** for the measured quantities, at their recorded settings.
  The pinned and variant labels stay as recorded.
- **Remaining evidence gaps, open in [#235](https://github.com/Takazudo/zudo-pd/issues/235):**
  - no in-run pinned cross-check of the abstol variant;
  - most corner and hot rows exist only under the variant;
  - the vendor macros' temperature reach is unknown;
  - the hot case is a uniform-temperature sensitivity, not a hot-start result.
- **Unchanged:**
  - no candidate is judged, and no ceiling or exception is changed or adopted;
  - the earlier failed and aborted cases stand;
  - the rejected Miller approach stays rejected, and T2 rev 3 stays parked;
  - D1 stays a pre-order hold.
