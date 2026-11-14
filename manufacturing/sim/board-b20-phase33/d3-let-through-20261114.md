# D3 let-through: ENVELOPE FORMED (SIM), and every rail exceeds its literal maximum for 0.09–0.23 ms under any fault

This reads the pre-registered [criteria](d3-let-through-criteria.md), with amendment 1, against the second run. The
envelope is SIMULATED, with the stated ASSUMPTIONS. It can go to OSC as the E22 answer. It judges no maximum. Nothing in
the schematic, PCB, BOM or inventory changed. electrical_acceptance stays **NOT ESTABLISHED** and D3 stays a PRE-ORDER
HOLD.

## The run is the pre-registered one and reproduces offline
- Run [43574394734](https://github.com/Takazudo/zudo-pd/actions/runs/43574394734) at `7903f70` (amendment 1),
  artifact 14105937117, digest `sha256:e1dcfc13a99691dafffcb08757505b1c4dd1842d1199016ee9165e9b69c51e10` (the
  downloaded zip matches).
- All 199 entries of `hashes.json` match. The identity control is REPRODUCED.
- Re-running `d3_let_through.py analyze` offline on the artifact gives the published result byte for byte:
  [`d3-let-through-20261114.json`](d3-let-through-20261114.json), sha256
  `a3d22c5d57479dd25ace77af925b36735cab4eaaed004f1d1c9fbe9aed7adf3d`.
- [Attempt 1](d3-let-through-attempt1-20261114.md) aborted in all 36 decks and is recorded separately.

## Reading: ENVELOPE FORMED (SIM), 36 of 36 decks complete, enabled before the fault, and opened

Worst case over the four Q31 / Q39 corners. Detection-to-off is shown as the range over the corners: the low end is the
0.5 V Q39 corner and the high end the 1.5 V corner.

| Rail (maximum) | Fault | Peak | Time above maximum | I²t | Excess I²t above maximum | Detection-to-off |
| --- | --- | --- | --- | --- | --- | --- |
| +12 V (2.1 A) | 1.2 × max | 2.59 A | 0.22 ms | 1.5 mA²s | 0.05 mA²s | 0.09–0.22 ms |
| +12 V | 2 × max | 4.29 A | 0.22 ms | 3.9 mA²s | 1.0 mA²s | 0.09–0.22 ms |
| +12 V | short | 119 A | 0.21 ms | 0.089 A²s | 0.079 A²s | 0.09–0.22 ms |
| +5 V (0.5 A) | 1.2 × max | 0.62 A | 0.22 ms | 0.08 mA²s | 0.003 mA²s | 0.09–0.22 ms |
| +5 V | 2 × max | 1.03 A | 0.22 ms | 0.23 mA²s | 0.06 mA²s | 0.09–0.22 ms |
| +5 V | short | 53.6 A | 0.22 ms | 0.029 A²s | 0.027 A²s | 0.09–0.22 ms |
| −12 V (2.0 A) | 1.2 × max | 2.45 A | 0.23 ms | 1.4 mA²s | 0.04 mA²s | 0.10–0.23 ms |
| −12 V | 2 × max | 4.06 A | 0.23 ms | 3.6 mA²s | 0.9 mA²s | 0.10–0.23 ms |
| −12 V | short | 123 A | 0.22 ms | 0.092 A²s | 0.083 A²s | 0.09–0.22 ms |

The overload peaks are the fault itself (1.2 or 2 × maximum at the rail's voltage), held until the pass pair opens. The
short's peak and most of its I²t come from the 57 µF PRE capacitor in the first microseconds. After that, the converter
limit (8.3 A assumed) holds until the pair opens.

## How far these figures hold
- **Conservative on time:** amendment 1 slows the EN_N edge to a 50 µs time constant. That lengthens time above the
  maximum, I²t and detection-to-off, by about 20 µs in the local smoke test (not evidence).
- **Model limits:** generic FETs in the latch; the alert sink and the U9A delay are PAs; the converter limit is treated
  as a DC output limit; the cable is an assumed 20 mΩ / 100 nH. The short's peak depends on the cable and the PRE
  capacitor ESR, which is not modelled.
- **Not measured:** a bench measurement of detection-to-off would replace the chain values above.

## What this leaves open (the owner's choice, from the plan)
A trip-only limiter exceeds every literal maximum for 0.09–0.23 ms under any fault above the trip point. The paths are:
- ask OSC to amend E22's let-through, sending this envelope;
- shorten the chain, for example smaller CF1 / CF3;
- add a regulating current limit.
