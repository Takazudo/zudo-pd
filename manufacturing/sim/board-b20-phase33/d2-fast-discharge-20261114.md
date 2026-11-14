# D2 fast matched discharge, attempt 2: FAIL (SIM) on R-VEE, the −12 V switch fires about 25 µs early

This reads the pre-registered [criteria](d2-fast-discharge-criteria.md) (with amendment 1) against attempt 2. The
candidate stays PROPOSED and D2 stays a PRE-ORDER HOLD. electrical_acceptance stays **NOT ESTABLISHED**. Nothing in the
schematic, PCB, BOM or inventory changed.

## The run is the pre-registered one and reproduces offline

- Run [43548307315](https://github.com/Takazudo/zudo-pd/actions/runs/43548307315) at `c130766`, artifact
  14095701608, digest `sha256:38c983e3ca8eab8ce60057a84b1cce2f32c884bd7e95c71ef68b91223dbb94e9` (the downloaded zip
  matches).
- All 829 entries of `hashes.json` match. The identity control is REPRODUCED.
- Re-running `d2_fast_discharge.py analyze` offline on the artifact gives the published result byte for byte:
  [`d2-fast-discharge-attempt2-20261114.json`](d2-fast-discharge-attempt2-20261114.json), sha256
  `7f72292495737013a64564488db12dd30bf749ed33de72aa8b92cfd6b4d388bb`.

## Reading: FAIL (SIM), 8 complete decks fail R-VEE

92 of 162 decks completed. The other 70 ABORTED at 1.026 ms, during the EN_N edge (EN_N 2.6 V, timestep 1.25e-18 s,
no node named), spread across every bank and load corner. Under the rule, an abort is recorded and not retried, and any
failing complete deck makes the reading FAIL (SIM).

Every failing deck has the +12 V bank high and the −12 V bank low, with +12 V unloaded. That is the margin edge named
in the expectation.

| Deck | Loads (+12 / −12 / +5) | Largest +12 V while −12 V is absent | Duration |
| --- | --- | --- | --- |
| `phnlfh-zmz` | 0 / max / 0 | 0.920 V | 20 µs |
| `phnlfh-zpm` | 0 / planning / max | 1.210 V | 29 µs |
| `phnlfh-zpz` | 0 / planning / 0 | 1.222 V | 30 µs |
| `phnlfl-zmz` | 0 / max / 0 | 0.918 V | 20 µs |
| `phnlfl-zpm` | 0 / planning / max | 1.220 V | 30 µs |
| `phnlfl-zpz` | 0 / planning / 0 | 1.233 V | 30 µs |
| `phnlfl-zzm` | 0 / 0 / max | 1.227 V | 30 µs |
| `phnlfl-zzz` | 0 / 0 / 0 | 1.207 V | 29 µs |

The limit is +12 V ≤ 0.5 V while |−12 V| ≤ 0.6 V. The passing decks in the same two banks reach the +12 V level only
2–23 µs before −12 V reaches its level, so the margin there is small too.

All other rows hold in every complete deck: disconnect before discharge, disconnect skew, the discharge levels within
100 ms (all reached by about 1.02 ms after the EN_N crossing), and the R-SW direct hazard.

## Why the calculation passed and the simulation does not

The calculation fires all three switches at once. In the deck the −12 V switch conducts earlier than the +12 V switch:
in `ceil-mzm` at 0.2 ms after the EN_N rise, the −12 V switch carries 3.6 A while the +12 V switch carries 62 mA. The
−12 V rail then reaches its absent level first at the low −12 V bank. The firing networks are not matched, as the
expectation warned.

## Reported, not read

- Largest peak discharge current: +12 V 13.40 A, −12 V 7.22 A, +5 V 5.72 A.
- Largest energy per discharge resistor: +12 V 8.96 mJ, −12 V 12.59 mJ, +5 V 1.04 mJ.
- Discharge onset: 0.131–0.164 ms after the EN_N crossing.
- The pass pairs stop conducting during the 50 µs EN_N edge, before EN_N crosses 2.5 V, so every disconnect time is
  reported as 0 ms. Discharge onset still follows it in every complete deck.

## What this leaves open

- The candidate as proposed does not meet R-VEE in this model. A revised candidate needs matched firing (for example,
  holding the −12 V switch off until the +12 V switch conducts, or slowing the −12 V gate network). That is a new
  candidate and needs new pre-registered criteria before any run.
- 70 decks did not complete. Any revised deck also needs the EN_N-edge convergence addressed before the run.
- E22 asks for the canonical +5 V planning load (224.3 mA). This grid has +5 V only at 0 and maximum, so a revision
  should add it.
