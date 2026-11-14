# D3 let-through attempt 1: NOT FORMED, every one of the 36 decks aborted as the pass pairs began to turn off

This reads the pre-registered [criteria](d3-let-through-criteria.md) against the first run. No envelope is formed and
nothing goes to OSC from it. Nothing in the schematic, PCB, BOM or inventory changed. electrical_acceptance stays
**NOT ESTABLISHED** and D3 stays a PRE-ORDER HOLD.

## The run is the pre-registered one and reproduces offline
- Run [43572211823](https://github.com/Takazudo/zudo-pd/actions/runs/43572211823) at `227e5b2`, artifact 14104682944,
  digest `sha256:27b0f7c7e07cc59c8de77e0ef9d7a57484a79359073f837bd05809916f8e05c1` (the downloaded zip matches).
- All 199 entries of `hashes.json` match. The identity control is REPRODUCED.
- Re-running `d3_let_through.py analyze` offline on the artifact gives the published result byte for byte:
  [`d3-let-through-attempt1-20261114.json`](d3-let-through-attempt1-20261114.json), sha256
  `54e6c544836c104d55432277fbadf27822715cecf9dfe1758600167c8cc92df0`.

## Reading: NOT FORMED, 36 of 36 ABORTED
Every deck stopped with "timestep too small" inside a vendor CSD18543Q3A pass-pair subcircuit (`xq*.10` or
`xq*.xcgd.g1_int1`). Each stopped when EN_N had risen to 1.82–1.95 V, the onset of the gate pulldowns, 0.57–0.71 ms
into the run. The fault class did not matter. As the run rule requires, the aborts are recorded and not retried.

This is the same failure the D2 fast-discharge decks hit with a 1 µs EN_N edge. There, a 50 µs edge (D2 amendment 1)
ran. Here EN_N rose through REN 10k into the assumed 1 nF gate load, a 10 µs time constant. The local stand-in FET
does not show the problem, so the smoke test did not catch it.

## What follows
Amendment 1 is pre-registered in [the criteria](d3-let-through-criteria.md) before a second dispatch.
