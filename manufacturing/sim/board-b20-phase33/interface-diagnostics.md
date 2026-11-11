# PD20 interface diagnostics (D1–D3) — 2026-11-11

Tracking: [#243](https://github.com/Takazudo/zudo-pd/issues/243) under [#235](https://github.com/Takazudo/zudo-pd/issues/235).
Tool: [`interface_diagnostics.py`](interface_diagnostics.py); retained output
[`interface-diagnostics.json`](interface-diagnostics.json), kept fresh by
`test_interface_diagnostics.py` in the component gate.

**This is arithmetic and source binding, not simulation or physical qualification.**
`electrical_acceptance` remains NOT ESTABLISHED. No contract value, exception, current
budget, component or tolerance is changed or adopted. Hard circuit decisions are held for
the repository's hard-decision review role; this record states hypotheses, evidence and the
exact missing inputs.

Inputs: generated `boards/board-b20-draft/board-b20-draft.kicad_sch` references, the
phase33 `tracking/nom.cir` deck, `scripts/pcb/calculate-board-b20-draft.py` constants and
functions, the recorded 2026-11-09 refinement peaks, and the canonical interface
`pd-interface-20v.md` at OSC `433c88b` (SHA-256 `8702890d…56a`, re-fetched and matched on
2026-11-11).

## Model scope

The tool fails if a listed reference leaves the schematic, a modeled element leaves the
deck, or an omitted subsystem appears in the deck (bare name or X-prefixed subcircuit
instance such as `XQ51` or `XU11`). The discharge resistances are read from the
schematic (RX12, RX5 and the annotated R76 for builder RXN) and must equal the calculator
constants; the recorded peaks are read from `startup-refinement-20261109.json` (2 µs) and
`execution-20261110.json` (5 µs).

| Subsystem | Phase33 deck | Omitted installed behavior |
| --- | --- | --- |
| Converters U1–U3, post-filters, servo U4/U5 | Stiff sources, 20 mΩ, 57 µF | Switching, current limit, servo dynamics, pre-node droop |
| Shunts RSH1–RSH3 | Drawn resistances | None at DC |
| Tracking U13/U9B, pre-bias, pairs Q1–Q6 | Vendor OPAx187/CSD18543Q3A models | BSS138 pre-bias physics; model accuracy unestablished |
| RAMP and start-order clamps U15/U16 | Drawn values; behavioral reset | Q12 device behavior |
| Disable pulldowns Q10/Q11, level shifter Q24/Q25 | Behavioral 3.5 Ω (35 Ω re-entry) switches | Switching delay and CSD gate-charge removal |
| Enable/minimum-off latch | Behavioral latch, shortest hold | Transistor-level timing |
| **Active discharge Q51/Q52/Q54–Q57, RX12/RX5/R76** | **Omitted** | All discharge switching, its order against disconnect, RC decay |
| **Limiters U11/U12/U9A, fault latch** | **Omitted** | Detection, latch and switch-off timing; overshoot |
| **Windows U6–U8** | **Omitted** | Trips during start, discharge, re-entry |
| OSC load | Contract-maximum C + 50 mΩ ESR; fixed resistors | Real load current versus voltage, asymmetry |

Phase33 therefore cannot answer D2 or D3; it only informs D1.

## D1 startup excursions and monotonicity

| Hypothesis | Conclusion | Evidence |
| --- | --- | --- |
| Designed common RAMP slope too steep | **Refuted** for the designed common RAMP (calculated); recorded `v(ramp)` not inspected | Ideal tracking slope ≤ 0.3137 V/ms (+5) and 0.7611 V/ms (−12) at −10 % RAMP C; recorded peaks are 3.04× and 1.94× the ideal, only inside the exception voltage regions |
| Start-order clamp release (U15/U16 on RAMP_P5/RAMP_M12 behind RCP1 1 kΩ) gives a fast reference edge | **Unresolved** | Not tested; the per-rail reference nodes were not extracted from the recorded runs |
| Maximum-step artefact | **Refuted** for step; other solver settings and macromodel fidelity unresolved | 5 → 2 µs changes the peak by +0.01034 % (+5) and +0.01040 % (−12) |
| Slope and current are one constraint | **Supported** for the modeled pure C + ESR load | Recorded ESR-branch currents equal C·dV/dt (114.58 vs 114.51 mA; 265.46 vs 265.26 mA); 114 mA/120 µF = 0.95 V/ms equals the +5 slope ceiling, and 265 mA/180 µF = 1.4722 V/ms makes the 1.47 V/ms −12 slope ceiling slightly tighter. A fix must lower slope; a resistive or nonlinear load part would separate the two |
| No-load overshoot of the pre-bias target near conduction | **Unresolved** | Consistent with no-load-only, low-voltage location. Distinguish with one paired nom/adv run changing only the pre-bias target (RT12O/RT5O/RT12NO) or CT, after design review. Not run |
| Strict monotonicity | **Unresolved** | Small negative adjacent increments remain; no tolerance adopted |

The failed conditions are preserved: +5 V 0.954850860 V/ms / 114.510041 mA and −12 V
magnitude 1.474778000 V/ms / 265.259332 mA exceed the 0.95 / 114 mA and 1.47 / 265 mA
exception ceilings in the model.

## D2 discharge and shutdown

Ideal simultaneous disconnect (zero skew; the contract allows up to 1 ms and the installed
skew is unbounded), closed-form per-rail decay through RX12 100 Ω, R76 (RXN) 150 Ω and RX5
33 Ω at contract-maximum capacitance from the load-band maxima. Switch on-resistance is
omitted (it only slows decay). "Absent" has no numeric contract definition; the cases use
the 0.5 V +12 V discharge level (CALCULATED A1) for both rails as a labelled assumption, plus
the contract's informal "about 1.5 V". One-rail-to-AGND loads are illustrative only: OSC
±12 V loads are largely rail-to-rail, which couples the rails.

| Case | Discharge-level times (+5 / +12 / −12) | R-VEE row | Direct R-ADG hazard | 1.5 V screen |
| --- | --- | --- | --- | --- |
| Zero load | 8.56 / 57.92 / 81.71 ms | none | none | none |
| Zero load, absent = 1.5 V | as zero load | at 56.97 ms, +12 at 0.527 V | none | none |
| Assumed +12 at 6 Ω only | 8.56 / 3.28 / 81.71 ms | at 3.28 ms, −12 at 10.96 V | same instant, +5 at 2.27 V | at 2.16 ms |
| Assumed −12 at 6.316 Ω only | 8.56 / 57.92 / 3.31 ms | at 3.51 ms, +12 at 10.27 V | same instant, +5 at 2.14 V | at 2.31 ms |
| Zero load, absence undefined | as zero load | OPEN | OPEN | none |

- **Zero-load level/time/voltage rows: supported only for absent ≤ 1.44 V with ideal
  simultaneous disconnect (calculated).** R-VEE first fails at an absent threshold of
  1.45 V (+12 V at 0.50 V while −12 V is at 1.45 V). Disconnect order is the separate
  unresolved row below.
- **Asymmetric load can reorder decay into forbidden states: supported under the stated
  resistive-load and absence assumptions; unresolved for the installed system.** Passive
  per-rail discharge does not couple the rails, so the contract's skew rows depend on OSC
  load behavior during shutdown.
- **Disconnect before discharge: unresolved.** Disconnect and discharge start from the
  same EN_E state with no designed ordering, through unequal paths: +12/+5 disconnect
  EN_E→Q33→EN_N (REN 10 kΩ pull-up)→Q10/Q11; −12 disconnect Q24→RG3A 56 kΩ→Q25; discharge
  from the CDH hold-up via Q56→DIS_P (R60 100 kΩ pulldown)→Q51/Q52 and Q54→R61 470 kΩ/R62
  1 MΩ divider→Q55. Overlap
  current is limited by the discharge resistors (0.125 / 0.082 / 0.158 A at the load-band
  maxima), which is a consequence, not compliance.

## D3 maximum delivered current

Trip maxima from the existing calculator are 2.08485 / 1.99544 / 0.46084 A against the
2.1 / 2.0 / 0.5 A maxima, leaving 15.15 / 4.56 / 39.16 mA. The limiter trips and opens; it does
not regulate, so delivered current keeps rising until switch-off. **The worst-case delivered
peak is at least the trip maximum; the trip threshold is not an upper bound (refuted as a
compliance argument).**
Compliance stays **unresolved**: INA301 tp ≤ 1 µs is the only guaranteed stage; U9A is
slew-limited (about 70 µs typical); latch, gate-pulldown and pair turn-off times and the
load-side di/dt are UNSOURCED. With 1 µs total response the −12 V margin allows only
4.56 mA/µs of growth.

## Next inputs (no correction adopted)

1. D1: extract the per-rail reference nodes (RAMP_P5/RAMP_M12) and `v(ramp)` against the
   excursion times, then a design review of one paired nom/adv run varying only the
   pre-bias target or integrator CT. Requires the hard-decision role before admission.
2. D2: OSC per-rail load current versus voltage during shutdown (or an agreed bound), a
   numeric definition of "absent", and switching data for the disconnect/discharge edge.
   Without them, only a design that couples the rails (or an agreed contract reading)
   could guarantee the skew rows; that is a design decision, not proposed here.
3. D3: a guaranteed detection-to-switch-off time and a load-side di/dt bound, or an
   explicitly agreed regulating current-limit change. No excess-current budget is adopted.
