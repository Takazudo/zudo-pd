# D2 discrete −12 V sequencer: PASS (SIM) in all 972 corner decks, with 0.35 V left to the 6 V limit at the high corner

This reads the pre-registered [criteria](d2-sequencer-circuit-criteria.md) against the run. The small FETs and the
zener are generic corner models, not vendor models. D2 stays a PRE-ORDER HOLD and electrical_acceptance stays
**NOT ESTABLISHED**. Nothing in the schematic, PCB, BOM or inventory changed.

## The run is the pre-registered one and reproduces offline

- Run [43567418750](https://github.com/Takazudo/zudo-pd/actions/runs/43567418750) at `215a286`, artifact
  14102624779, digest `sha256:1a2c194554f2d5bf70774d74ddc62a122895d076bd7716789f98a035346cd312` (the downloaded zip
  matches).
- All 4,879 entries of `hashes.json` match. The identity control is REPRODUCED.
- Re-running `d2_sequencer_circuit.py analyze` offline on the artifact gives the published result byte for byte:
  [`d2-sequencer-circuit-20261114.json`](d2-sequencer-circuit-20261114.json), sha256
  `3903bb2d5a4627b6b0ae7563f27174d1f8d0fd4a17df9ae91fe8c2bb890630ae`.

## Reading: PASS (SIM), every row holds in every combo

All 972 decks are COMPLETE, and no row fails in any of them. The calculation's 18 failing `hlrh` cases did not occur,
as the expectation stated.

| Combo (H, release) | Largest \|−12 V\| once +12 V is absent (≤ 6 V) | Smallest \|−12 V\| while +12 V is present (> 0.6 V) | Slowest level |
| --- | --- | --- | --- |
| `hlrl` (3.5 V, 0.5 V) | 3.52 V | 0.99 V | 1.21 ms |
| `hlrh` (3.5 V, 1.5 V) | 3.51 V | 0.99 V | 1.01 ms |
| `hhrl` (5.6 V, 0.5 V) | 5.65 V | 1.44 V | 1.31 ms |
| `hhrh` (5.6 V, 1.5 V) | 5.65 V | 1.44 V | 1.20 ms |

The high-H combos leave 0.35 V to the 6 V limit. The upper end of H is QN's VGS(th) maximum (1.5 V, sourced) plus the
zener's 4.1 V maximum at 5 mA, which DS18004 guarantees. At the 0.2 mA switching current the zener sits lower than
that, so this corner is conservative.

## What this leaves open

- The BZT52C3V9-7-F candidate record: the LCSC number is not yet retrieved. Its datasheet PDF goes in the private
  resources repository, under the project's new rule.
- A sourced low-current VZ bound, which would tighten the low corner, and vendor models for the small FETs.
- The component audit, the schematic and layout change, and the bench check.
