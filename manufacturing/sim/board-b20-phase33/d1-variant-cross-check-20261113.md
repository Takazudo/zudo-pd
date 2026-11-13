# D1 pinned-versus-variant cross-check: the abstol variant is COMPARABLE, the rshunt variant is NOT

Run on 2026-11-13 UTC under [#235](https://github.com/Takazudo/zudo-pd/issues/235). The criteria are in
[`variant-cross-check-criteria.md`](variant-cross-check-criteria.md), committed in `3419ace` before the dispatch.
This is a diagnostic: it reads solver-setting comparability only.
- electrical_acceptance stays **NOT ESTABLISHED**.
- The recorded D1 failures stay failures, and D1 stays a pre-order hold.
- No ceiling, contract, threshold, component or candidate changed. The 350 / 160 mA exception is not adopted.

Records in this directory:
- `d1-variant-cross-check-20261113.json` is the run's `variant-cross-check.json`, byte for byte.
- The archive itself (waveforms included) is not in the repository. The artifact expires on 2026-12-13.

## Run and integrity: VERIFIED

| Item | Value |
| --- | --- |
| Workflow run | [43484213339](https://github.com/Takazudo/zudo-pd/actions/runs/43484213339), attempt 1, success; input `variant_cross_check` only |
| Execution revision | `3419ace8a937597dbf515e61581f4caf7091f4e8` (branch `claude/project-thread-era0ms`, PR #291) |
| Artifact | 14066478668 `phase33-d1-reference`, 168,764,527 bytes |
| Archive SHA-256 | `cae41ce312d13ac044b35f3f08ef8d82e4827f693eacd667a430729327044657` (download matches GitHub's recorded digest and size) |
| Bundle members against its `hashes.json` | 44 members, 43 listed (plus `hashes.json` itself), all match; none unlisted or missing; no vendor model bytes |
| Result file SHA-256 | `variant-cross-check.json` `efecf7032ee50758a8ddaa2226f1f17f6cfbd5ed4faf1934e65230556bc380bb` |

- **Identity control: REPRODUCED.** The `nom`/`adv` executed decks and their main and supplemental waveforms are
  byte-identical to the retained 2026-11-09 refinement. The `.spiceinit` is `65514f56…`, and the model hashes are those
  of the earlier runs.
- **Decks.** Each executed variant deck equals the deck that `derive_cases()` re-derives at `3419ace`, and its hash is
  in the run's `xcheck-manifest.json`. Every variant run is COMPLETE on its first attempt.
- **Re-analysis.** The analyzer was rerun offline on the extracted bundle at `3419ace` (CPython 3.13.18). It reproduces
  `variant-cross-check.json` byte for byte.

## Readings under the pre-registered 0.01 % rule

The table gives the relative difference |variant − pinned| / pinned. The pinned side is the same dispatch's identity run.

| Pair | +5 V slope in region | +5 V current in region | −12 V slope in region | −12 V current in region | Reading |
| --- | --- | --- | --- | --- | --- |
| `abstol-nom` | 0.00030 % | 0.00014 % | 0.00024 % | 0.00013 % | **COMPARABLE** |
| `abstol-adv` | 0.00065 % | 0.00074 % | 0.00021 % | 0.00017 % | **COMPARABLE** |
| `rshunt-nom` | 0.108 % | 0.108 % | 0.390 % | 0.389 % | **NOT COMPARABLE** |
| `rshunt-adv` | — | — | — | — | not applicable: `adv` already runs at `rshunt=1e9` |

**The D1 values themselves.**
- `nom` +5 V, pinned: 0.954850860 V/ms and 114.510041 mA. Under abstol: 0.954847995 V/ms and 114.510205 mA.
- `adv` −12 V, pinned: 1.474778000 V/ms and 265.259332 mA. Under abstol: 1.474774912 V/ms and 265.258874 mA.

The pinned values are the recorded D1 failures exactly, so the abstol rows sit on the same side of every ceiling.

**Outside the reading (reported, not read).** Under abstol, the quantities that are not read move more than the read
ones:
- the above-region peak slope, by up to 0.38 % (+5 V on `adv`);
- the charge in the region, by up to 0.11 % (−12 V on `nom`).

Under rshunt, the window peak current moves by up to 0.39 %.

## What this supports
- **The abstol-labelled rows are readable.** On these two decks, the matched-variant abstol step moves the D1 peak slope
  and current by less than 0.001 %, about a hundredth of the reading bound. The OSC-bank and ceiling-corners variant
  rows are all abstol rows (see the [audit](d1-diagnostic-audit-20261113.md)), so this supports reading their in-region
  peaks as solver-equivalent. It does not prove it: those decks carry the T2 rev 2 no-load additions, other banks,
  enable-edge corners or a `.temp` line. They stay labelled as variant rows. The contract-route figures that rest on
  them gain this support, and nothing is adopted.
- **The rshunt step is not a neutral solver setting.** `rshunt` adds a conductance from every node to ground, so it
  changes the circuit. On `nom` it moves the D1 quantities by 0.1–0.4 %. That is the same size as the recorded D1
  exceedances: 0.10–0.51 %.

## Observation that needs owner attention (not a finding about `adv`)
The recorded −12 V D1 failure comes from `adv`, whose accepted baseline already runs at `rshunt=1e9`. Pinned `adv` at
`rshunt=1e10` aborted in the 2026-11-09 ladder.

On `nom`, moving rshunt 1e10 → 1e9 *raised* the −12 V in-region slope and current by about 0.39 %. If `adv` responded
the same way, its value at `rshunt=1e10` would be about 1.469 V/ms and 264.2 mA, under the 1.47 / 265 mA ceilings.

That is a cross-deck inference, not a result. No `adv` waveform at `rshunt=1e10` exists, and none is claimed. The
recorded failure stands. What this shows is that the −12 V D1 margin is smaller than the uncertainty that the adopted
`adv` solver setting brings in.
