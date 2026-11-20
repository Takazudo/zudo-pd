# D2 firing-network threshold band: candidate C1 PASS (SIM) on the five discharge rows in all 2,808 decks; as-drawn network FAIL (SIM)

This reads the pre-registered [criteria](d2-threshold-band-criteria.md) against the run. Everything is SIM
(ngspice-44.2, pinned KiCad image `sha256:18693567…dd3ec`, vendor CSD18543Q3A model with a gate-shift threshold corner,
generic small-part corner models) or CALCULATED. Nothing is measured. Nothing in the repository changed.
electrical_acceptance stays **NOT ESTABLISHED**.

## The run is the pre-registered one

- Criteria, tool and deck-manifest hashes were recorded before the dispatch at 2026-11-20T10:50:58Z
  (`results/preregistration.sha256`); amendment 1 was hashed before set CTL-SAME ran.
- 5,688 formal decks, all COMPLETE, none retried. Wall time 47 min plus 5 min for CTL-SAME.
- Result: [`d2-threshold-band-20261120.json`](d2-threshold-band-20261120.json), sha256 `691c216d…e01a32`; per-set
  cases in `results/<set>.json`; every waveform hash in `results/waveform-hashes.sha256` (the 21 GB of waveforms were
  deleted; the decks and logs are kept under `work/`).

## Reading: G is PASS (SIM) on every fast-discharge row

| Set | Network | Reading | Decks | Smallest \|−12 V\| while +12 V present (> 0.6 V) | Largest \|−12 V\| once +12 V absent (≤ 6 V) | Slowest level |
| --- | --- | --- | --- | --- | --- | --- |
| **G** (verdict) | C1 | **PASS (SIM)** | 2,808 / 2,808 | 0.742 V (`hlrl-phnlfl-zmp`, Q51 late / Q55 early) | 5.652 V | 1.43 ms |
| CTL (control) | as drawn | **FAIL (SIM)** 72 | 576 | 0.162 V | 5.651 V | 1.69 ms |
| CTL-SAME (amendment 1) | as drawn | **FAIL (SIM)** 64 | 576 | 0.204 V | 5.651 V | 1.77 ms |
| PA-HOT (reported) | C1 | PASS (SIM) | 576 | 0.998 V | 5.877 V | 1.24 ms |
| PA-COLD (reported) | C1 | **FAIL (SIM)** 8 | 576 | 0.593 V | 5.652 V | 1.41 ms |
| L49 (reported) | C1 | PASS (SIM) | 576 | 1.317 V | 5.653 V | 1.20 ms |

- CTL fails R-VEE in 72 decks and the direct-hazard row in 20 of them; CTL-SAME fails R-VEE in 64 and the hazard row
  in 8. All are the late Q51 corner with −12 V at maximum load.
- PA-COLD's 8 failures are all 0.593–0.595 V, at the high-+12 V / low-−12 V banks with −12 V at maximum load, +12 V
  unloaded, the low-H sequencer combos and the late Q51 corner.
- In G the disconnect completes before the EN_N crossing in every deck (skew 0), and −12 V reaches its level
  0.04–0.78 ms after +12 V.

## The added onset-floor row is NOT MET as worded and MET under amendment 1

- As worded: G's earliest onset is 23.202 µs against a floor of 24.401 − 1 = 23.401 µs. **NOT MET, by 0.2 µs.**
- Cause: the control grid, not the candidate. CTL pairs the early Q55 corner only with the 4.10 V drive; G's
  same-direction corners pair it with 4.65 V. The −12 V network is identical in both.
- Amendment 1 (written after G was read, before CTL-SAME ran): the as-drawn network at the same-direction corners
  fires at 23.200 µs. Floor 22.200 µs. **MET.**

The verdict as originally worded is therefore not a clean PASS. The five contract rows pass; the row that failed was
this record's own addition and failed on a defect in its control.

## Reported, not read

- Earliest onset in G: 23.2 µs, the −12 V switch. At the early-Q51 / late-Q55 corner the +12 V switch now starts first
  (48.6 µs), and −12 V still reaches its hold before +12 V is absent.
- Largest peak discharge current in G: +12 V 17.19 A, −12 V 7.60 A, +5 V 7.25 A.
- Largest energy per discharge load: +12 V 10.77 mJ, −12 V 13.01 mJ, +5 V 1.25 mJ.
- PA-HOT earliest onset: 15.4 µs. That is the unchanged −12 V network at a 1.2 V threshold with the X7R loss.

## Exploratory and post-hoc runs (not criterion readings)

- **Before the criteria (940 decks):** `verify` reproduced the reviewer's finding with the gate-shift method;
  `explore1`–`explore3` picked C1. Neighbours fail: 4.7 kΩ + 22 nF X7R reaches 6.05 V at a 4.9 V drive, 3.09 kΩ + 27 nF
  reaches 6.13 V with the hot term, and 4.7 kΩ + 27 nF falls to 0.58 V at the drive band.
- **After the run (8 decks, `d2_threshold_posthoc.py`):** the reviewer's routed-parasitic resistance corners on the
  worst G decks. All pass; the smallest value falls from 0.742 V to 0.707 V and the largest is 5.575 V.

## What this leaves open

- The drive level (4.10–4.65 V here) and any threshold bound away from 25 °C are not sourced.
- The deck's disconnect is ideal, so the real disconnect-to-discharge margin is not shown.
- Q52 was not moved against Q51. Resistive loads and the rigid-shift ASSUMPTION stand.
- The schematic, BOM and inventory change, a fresh ERC/DRC parity run, and bench T5.
