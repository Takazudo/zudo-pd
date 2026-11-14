# D2 sequenced −12 V discharge: PASS (SIM) in all 243 decks, with the sequencer still behavioural

This reads the pre-registered [criteria](d2-sequenced-criteria.md) against the run. A PASS shows that the sequenced
function meets the voltage-form discharge rows with the vendor switch model. It does not qualify a circuit, because the
sequencer is a behavioural clamp whose discrete circuit is not yet drawn. D2 stays a PRE-ORDER HOLD and
electrical_acceptance stays **NOT ESTABLISHED**. Nothing in the schematic, PCB, BOM or inventory changed.

## The run is the pre-registered one and reproduces offline

- Run [43551917268](https://github.com/Takazudo/zudo-pd/actions/runs/43551917268) at `8d2d6c9`, artifact
  14097115267, digest `sha256:1b1354d2635f13113bd55a648e3d1ae2c3442e57b8bc133e11208e338508b510` (the downloaded zip
  matches).
- All 1,234 entries of `hashes.json` match. The identity control is REPRODUCED.
- Re-running `d2_sequenced.py analyze` offline on the artifact gives the published result byte for byte:
  [`d2-sequenced-20261114.json`](d2-sequenced-20261114.json), sha256
  `94784f1fd176b34b6fb45a4b7c77c0f17f7e6345d24b0ebd3bb7c5c48a12f2fa`.

## Reading: PASS (SIM), every row holds and every deck completed

All 243 decks are COMPLETE, so the smoothed Q54 removed the aborts. No row fails in any deck: disconnect before
discharge, disconnect skew, the discharge levels within 100 ms, R-VEE in both directions, and the R-SW direct hazard.

| Measure | Worst deck | Value | Limit |
| --- | --- | --- | --- |
| \|−12 V\| once +12 V is absent | `ceil-mzp` | 3.035 V | ≤ 6 V |
| \|−12 V\| while +12 V is present (after EN_N) | `phnlfl-zmz` | 0.858 V | > 0.6 V |
| Slowest rail reaching its discharge level | | 1.224 ms | ≤ 100 ms |

−12 V reaches its level 0.07–0.64 ms after +12 V in every deck, which is the intended order.

## Reported, not read

- Discharge onset: 0.040–0.048 ms after the EN_N crossing, now led by the −12 V switch.
- Largest peak discharge current: +12 V 13.40 A, −12 V 7.57 A, +5 V 5.72 A.
- Largest energy per discharge resistor: +12 V 8.96 mJ, −12 V 12.95 mJ, +5 V 1.04 mJ.

## The calculation shows how much room the sequencer thresholds have

In the same calculation as the criteria (ideal switches, 10,935 bank, load and timing cases), these hold and release
thresholds have no failing case:

| Hold below \|−12 V\| | Release when +12 V ≤ |
| --- | --- |
| 3 V | 1.0 V |
| 4 V | 1.5 V |
| 5 V | 2.0 V |

A 2 V hold fails from a 0.8 V release. So a discrete sequencer does not need a precision comparator: a transistor
threshold for the release, with a hold of about 4 V, has room for VGS(th) spread. This sweep is CALCULATED, not
simulated.

## What this leaves open

- The discrete sequencer circuit, its parts through the component audit, and its own pre-registered simulation.
- The resistive-load ASSUMPTION.
- Pulse-rated discharge parts. The peaks above are several amps for about 1 ms.
- The schematic change, layout, and the bench check.
