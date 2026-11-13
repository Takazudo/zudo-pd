# D1 −12 V `adv` without the rshunt step: the failure is not an rshunt artefact

Run on 2026-11-13 UTC under [#235](https://github.com/Takazudo/zudo-pd/issues/235). Criteria:
[`adv-rshunt-free-criteria.md`](adv-rshunt-free-criteria.md), committed in `7bbe316` before the dispatch.
- This is a diagnostic: it judges no ceiling.
- electrical_acceptance stays **NOT ESTABLISHED**, and the recorded −12 V D1 failure stands.
- Record: `d1-adv-rshunt-free-20261113.json` is the run's `adv-rshunt-free.json`, byte for byte, with SHA-256
  `a493988ae56c4f1a90b438ba3154ad3357e110a9d9e381b83ac1cfddbe30171d`.

## Run and integrity: VERIFIED

| Item | Value |
| --- | --- |
| Workflow run | [43486530273](https://github.com/Takazudo/zudo-pd/actions/runs/43486530273), attempt 1, success; input `adv_rshunt_free` only |
| Execution revision | `7bbe3162ce828d1dc1240d2c26fa3f42bd2890f5` (PR #291) |
| Artifact | 14066564438, 101,769,283 bytes, SHA-256 `7fb2db0a8fb4d9c680e505891fd43858580fb14d4982582157d5f829e33b5af9` (download matches GitHub's digest and size) |
| Bundle against its `hashes.json` | 35 files listed, all match, none unlisted or missing, no vendor model bytes |

- **Identity control: REPRODUCED.** It is byte-identical to the retained refinement for both `nom` and `adv`.
- **Decks.** Both executed decks equal what `derive_cases()` re-derives at `7bbe316`.
- **Re-analysis.** The analyzer was rerun offline at `7bbe316` and reproduces the result file byte for byte.

## Result

| Label | Setting | Status | −12 V slope in region | −12 V current in region |
| --- | --- | --- | --- | --- |
| identity `adv` (recorded failure) | pinned, rshunt 1e9 | COMPLETE | 1.474778000 V/ms | 265.259332 mA |
| `r10-adv` | pinned, rshunt 1e10 | **ABORTED** at 3.068 ms, timestep 2.5e-18 s, node `xq1.xcds.g1_int1` | — | — |
| `abstol-r10-adv` | matched variant abstol, rshunt 1e10 (labelled, not pinned) | COMPLETE | 1.474662784 V/ms | 265.237680 mA |

- **The −12 V figures barely move.** Removing the rshunt step changes them by −0.0078 % (slope) and −0.0082 % (current).
  Both stay above the 1.47 V/ms and 265 mA ceilings. This is reported, not judged.
- **+5 V on this deck moves by +0.137 %.** That is 0.858231 → 0.859409 V/ms and 102.931 → 103.071 mA. +5 V is not the
  recorded failing rail on `adv`.
- **The pinned abort repeats.** `r10-adv` aborted in the CSD18543Q3A model (`xq1`), as on 2026-11-09. That abort is
  why the baseline uses rshunt 1e9.

## Correction to the cross-check record's observation
[`d1-variant-cross-check-20261113.md`](d1-variant-cross-check-20261113.md) extrapolated from `nom` to `adv`. Because the
rshunt step moved `nom`'s −12 V figures by about 0.39 %, it suggested `adv` at rshunt 1e10 might sit near
1.469 V/ms and 264.2 mA.

This run refutes that extrapolation. On `adv` the shift is about 0.008 %, so the recorded −12 V failure is not an
artefact of the adopted rshunt setting. The rshunt step is still not a neutral setting in general (see `nom`).

## Unchanged
No ceiling, contract, threshold, component or candidate changed. The current-form proposal is not adopted by zudo-pd. Its
2026-11-12 draft asks for 350 / 180 mA; the repository records name the earlier 350 / 160 mA. On 2026-11-14 JST the owner chose the OSC contract route; any ceiling change waits for OSC's recorded
acceptance.
