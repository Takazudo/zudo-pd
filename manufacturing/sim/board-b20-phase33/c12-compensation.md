# C12 initial-tolerance compensation sensitivity — 2026-11-09

This bounded experiment uses the recovered, unchanged TI TPS54560 averaged model
(SLVMCU2) and the historical phase7 inner-loop circuit. The generated
`c12-ac-sensitivity-20261109.json` records source, model, deck, log and waveform
hashes, all unity-gain crossings, phase crossings and actual DC load currents.
Raw outputs remain local under `tmp/c12-ac-review/`; they are not fabricated by
analysis tests. The separately retained first 12 approximate-load cases are
calibration evidence, not exact contract-current cases. The final 16 cases cover
19/21 V, C12 44.65/49.35 nF, and 0.05/1.6/1.9/2.0 A DC targets.

Recover the exact model using section 5 of
`manufacturing/board-b-20v-switcher-direct-draft.md`; the recipe checks its hash.
Prepare each mode into a new directory:

```sh
python3 manufacturing/sim/board-b20-phase33/c12_compensation.py prepare \
  --mode contract --model /absolute/path/TPS54560_AVG.LIB \
  --output tmp/c12-new-contract
```

Repeat with `light` or `approximate` only when that dataset is required. Inspect
`prepared.json` and execute its commands serially through the heavy guard,
retaining stdout/stderr as the corresponding `.log`, return code and actual
output hashes in a receipt. Preparation is NOT RUN and does not establish
simulation success. The retained audited experiment uses the historical receipt
schema in the local run directories. To independently regenerate its summary:

```sh
python3 manufacturing/sim/board-b20-phase33/c12_compensation.py summarize \
  --raw-root tmp/c12-ac-review \
  --output manufacturing/sim/board-b20-phase33/c12-ac-sensitivity-20261109.json
```

Descending-crossing phase margins span 57.041–93.645 degrees across the 16
endpoint cases. Multiple crossings are retained, including ascending crossings;
no global stability PASS or new phase-margin acceptance criterion is assigned.
The 50 mA averaged-model result does not qualify CCM/DCM transitions or no-load
operation. This is initial C12 tolerance only: RCCP remains nominal, effective
MLCC values/ESR/inductance remain existing assumptions, and temperature, outer
servo, switching ripple, tracking, full-stack and fault-current behavior are not
qualified. The 1e-5 A DC target check is numerical experiment control, not an
excess-current budget. The 1.9/2.0 A labels describe steady operating points,
not 20 ms performance or maximum-delivered-current compliance.
