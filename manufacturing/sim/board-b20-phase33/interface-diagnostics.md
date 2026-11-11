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
| Designed common RAMP slope too steep | **Refuted** for the designed common RAMP (calculated) and for the recorded `v(ramp)` | Ideal tracking slope ≤ 0.3137 V/ms (+5) and 0.7611 V/ms (−12) at −10 % RAMP C; recorded peaks are 3.04× and 1.94× the ideal, only inside the exception voltage regions. Extracted `v(ramp)` between 2 µs bin averages peaks at 0.1192 V/ms (+5) and 0.3529 V/ms (−12), run 43087070975 ([D1 reference record](d1-reference-20261111.md)) |
| Start-order clamp release (U15/U16 on RAMP_P5/RAMP_M12 behind RCP1 1 kΩ) gives a fast reference edge | **Refuted** for a reference-side edge and for clamp-diode release | Scaled per-rail reference peaks between 2 µs bin averages are 0.1192 V/ms (+5, ideal 0.3137) and 0.3557 V/ms (−12, ideal 0.7611); the clamp diodes stay reverse-biased (−4.850 to −4.843 V; −4.893 to −4.041 V). The excursions lie downstream of the reference |
| Adjacent-sample reference rule fired on a solver-timestep artefact | **Supported** for −12 (not applicable to +5) | The −12 adjacent-sample peak of 3730.2 V/ms is 0.977 mV over 2.11 ns in a 21-sample cluster (minimum step 0.235 ns) where `ramp_m12` rings 1.398 mV peak to peak with 18 sign reversals as the XU16A clamp output reaches 4.962 V. The analysis now uses 2 µs bin averages; the in-job adjacent-sample result is retained as superseded |
| Maximum-step artefact | **Refuted** for step; other solver settings and macromodel fidelity unresolved | 5 → 2 µs changes the peak by +0.01034 % (+5) and +0.01040 % (−12) |
| Slope and current are one constraint | **Supported** for the modeled pure C + ESR load | Recorded ESR-branch currents equal C·dV/dt (114.58 vs 114.51 mA; 265.46 vs 265.26 mA); 114 mA/120 µF = 0.95 V/ms equals the +5 slope ceiling, and 265 mA/180 µF = 1.4722 V/ms makes the 1.47 V/ms −12 slope ceiling slightly tighter. A fix must lower slope; a resistive or nonlinear load part would separate the two |
| No-load overshoot of the pre-bias target near conduction | **Unresolved** | Consistent with no-load-only, low-voltage location. Distinguish with one paired nom/adv run changing only the pre-bias target (RT12O/RT5O/RT12NO) or CT, after design review. Not run |
| Servo wound up during the dead zone and its recovery sets the peak | Windup **supported**; peak coincides with recovery **no**; dead zone set by the **conduction threshold after windup** (both rails) | The driver left its supply 11.942 ms (+5) and 10.858 ms (−12) before the pass pair conducted; Vgs climbed −0.000 → 2.443 V and −0.515 → 2.352 V; conduction began 368 µs and 604 µs before the failed segment, run 43099431981 ([D1 servo record](d1-servo-20261111.md)) |
| Strict monotonicity | **Unresolved** | Small negative adjacent increments remain; no tolerance adopted |

The failed conditions are preserved: +5 V 0.954850860 V/ms / 114.510041 mA and −12 V
magnitude 1.474778000 V/ms / 265.259332 mA exceed the 0.95 / 114 mA and 1.47 / 265 mA
exception ceilings in the model.

## D1 correction candidates (owner decisions; nothing adopted)

The CSD18543Q3A pair on each rail is both the servo pass device and the output disconnect, so a
passive bleeder cannot keep it conducting at the floor (+0.0513 V on +5, −0.0969 V on −12)
without defeating disconnection. **C2 minimum-load bleeder: rejected by owner decision.**

| Placement | R for ≥ 5 mA at the floor | Result |
| --- | ---: | --- |
| +5 output to GND | ≤ 10.3 Ω | Infeasible: 0.49 A at 5 V, above trip_min 0.43694 A |
| +5 common source to GND | ≤ 1.0 Ω | Infeasible |
| +5 common source or output to −12 V | ≤ 2428.4 Ω | Defeats disconnection: with the gate at GND only the 11 V Zener limits Vgs; a disabled output is pulled toward −12 V |
| −12 output to GND | ≤ 19.4 Ω | Infeasible: 0.62 A at 12 V leaves 1.32 A before trip_min against the 1.9 A transient minimum |
| −12 common source to GND | ≤ 2424.0 Ω | Does not test C2: current flows through XQ5 only; XQ6, the threshold-limited blocker, is untouched |
| −12 output to +5 V | ≤ 996.0 Ω | Defeats disconnection: a disabled output is pulled toward +5 V |

An EN-gated opposite-rail sink is also **rejected**: it needs the disconnect and AGND-return
rules reinterpreted. **C1, a fixed gate pre-bias while enabled, is rejected** by owner decision.
No fixed floor fits the threshold window: a floor that leaves 2.0 V on a 2.7 V part leaves
about 0.8 V on a 1.5 V part. On −12 V the enable transient already brings Vgs within 8.1–9.7 mV
of the model onset. In the [gap sensitivity](d1-gap-attempt2-20261111.md) no evaluated −12 V gap
passed and no +5 V gap was evaluated. Its microvolt rule 6 results are not the reason for rejection. C3, a slower gate path, remains an
unevaluated fallback.

T1, an integrator leak switched in while RAMP is held in reset, is **rejected by construction**
(owner decision; not evaluated in transient). At the summing node the DC balance sets the driver
by offset currents, not by conduction. On +5 V, DRV = 1.214 V − 43.1 × out, so the loop stays wound
to its rail. On −12 V, DRV = 23.5 × out + 1.214 V, which gives a threshold-dependent −0.47 V
pedestal ([analysis](d1-t1-leak-rejected-20261111.md)).

T2, a peak-hold anti-windup clamp, is **rejected by construction on +5 V** (owner decision; not
evaluated in transient). RG2P carries Vgs / 100 kΩ, and with the pair off that current leaves P5_CS
only through Q4's body diode into P5_OUT. A gate held near the edge therefore injects 8–20 µA against
the 1.6 µA divider drain, which is an output pedestal. This sets a constraint on any future +5 V or
+12 V gate-hold scheme: it must idle at Vgs of about 0.16 V or less at no load, unless the gate
pull-down return is changed ([paper check](d1-t2-paper-check-20261111.md)). On −12 V, T2 is under
evaluation against pre-registered rules ([criteria](d1-t2-criteria.md)). A −12 V only result does not
close D1.

Bias or bleeder current is sensed, because the limiter shunts sit upstream of each pair. It
therefore enlarges the maximum-delivered margin (15.15 / 4.56 / 39.16 mA, +12 / −12 / +5) and
consumes the transient-minimum margin (41.59 / 42.16 / 36.94 mA) and the startup-into-full-load
margin (8.94 / 13.29 / 29.09 mA).

## D1 enable-edge conduction: a recorded negative, with no order hold

The question was whether a part at typical 2.0 V or minimum 1.5 V VGS(th) would conduct at the
enable edge and produce an output excursion. Inference from a single-threshold model (baseline
waveforms of run 43109786353) says it would not: the enable transient is the designed pre-bias.
The loop drives each gate only until its own pair conducts, then the output sits at its floor.
The adv deck's constant gate offsets emulate a ±0.5 V threshold shift, and across that shift the
distance to onset barely moves:

| Rail, threshold vs model | Peak Vgs | 5 mA onset Vgs | Distance | Peak current | Output extreme |
| --- | ---: | ---: | ---: | ---: | ---: |
| +5, model | 2.3097 V | 2.4428 V | 133.1 mV | 1.26 mA | 51.9 mV |
| +5, −0.5 V | 2.3146 V | 2.4430 V | 128.4 mV | 1.32 mA | 51.7 mV |
| −12, model | 2.3426 V | 2.3504 V | 7.8 mV | 4.63 mA | −97.0 mV |
| −12, +0.5 V | 2.3430 V | 2.3527 V | 9.7 mV | 4.65 mA | −97.2 mV |

+5 V stays far inside its 0.8 V hold screen, and −12 V and +12 V (144 mV) stay below the 1.5 V
analog threshold. The open check is four constant-offset corners, mapped from the model's 250 µA
point (2.163 V): VO2 −0.66 / +0.54 V on +5 and VO3 −0.66 / +0.54 V on −12. These cover −12 below
the model threshold and +5 beyond −0.5 V, which are untested today, and ride on the next dispatch.

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

1. D1: the reference side is refuted and the dead zone is set by the pass-pair conduction
   threshold on both failed rails. A minimum-load bleeder (C2) and a fixed gate pre-bias
   while enabled (C1) are rejected by owner decision. A threshold-independent correction is
   the next proposal. Nothing is adopted.
2. D2: OSC per-rail load current versus voltage during shutdown (or an agreed bound), a
   numeric definition of "absent", and switching data for the disconnect/discharge edge.
   Without them, only a design that couples the rails (or an agreed contract reading)
   could guarantee the skew rows; that is a design decision, not proposed here.
3. D3: a guaranteed detection-to-switch-off time and a load-side di/dt bound, or an
   explicitly agreed regulating current-limit change. No excess-current budget is adopted.
