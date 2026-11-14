# D2 fast matched discharge: what is simulated and how it is read, stated before the dispatch

**This is a candidate evaluation, not a design adoption.** The owner chose this D2 route on 2026-11-14 JST: disconnect
first, then a fast matched discharge. Nothing in the schematic, PCB, BOM or inventory changes with this run.
electrical_acceptance stays **NOT ESTABLISHED**, D2 stays a pre-order hold, and no OSC contract row changes.

## The candidate
After the existing disconnect, low-value discharge loads switch onto all three rails at once.
- **Loads:** 0.5 Ω on +12 V, 1.5 Ω on −12 V and 0.5 Ω on +5 V.
- **Switches:** each load is switched by a CSD18543Q3A, the part already owned in the inventory.
- **Firing:** the switches fire from the existing hold-up drive (DIS_P / DIS_C, 4.9 V), through a gate delay network
  that holds them off until the pass pairs are open.
  - +12 V and +5 V: 10 kΩ and 22 nF from DIS_P.
  - −12 V: 4.7 kΩ from DIS_C (through Q54, modelled as a switch) and 47 kΩ to M12_OUT, with 180 nF across gate and
    source and an 11 V gate clamp.

The values are PROPOSED. This run tests whether they meet the contract rows. It does not select them.

The [calculation](d2_fast_discharge.py) (`calc`) (closed-form decay, ideal switches)
passes all 18 load corners at every bank below. This run adds the real pass-pair turn-off, the switch models and the
firing delay.

## The deck (one per corner, `d2fd/<label>/tracking/nomR.cir`)
A compact shutdown deck, not the full startup deck. It is built by `d2_fast_discharge.py` from:
- **Converters:** stiff sources behind 20 mΩ, set at the load-band maxima (12.48 / 5.2 / −12.37 V). The drawn shunts
  and pass pairs use the vendor CSD18543Q3A model.
- **Pass gates:** at the start, each is held fully on from its amplifier's supply rail through RG 10 kΩ, with the drawn
  11 V clamp. That is the slowest case for turn-off. EN_N rises at 1.000 ms, with a 1 µs edge, and pulls the gates
  through the drawn behavioural pulldowns (1/3.5 S).
- **OSC side:** the bank, with 50 mΩ ESR, and resistive loads at nominal voltage (an ASSUMPTION).
- **Solver:** pinned settings (`method=gear reltol=1e-3 abstol=1e-9 vntol=1e-5 itl4=200 rshunt=1e10`), `.tran 1u 6m 0
  1u` from the DC operating point, `--original-only`. An aborted deck is recorded as ABORTED and is not retried.

**Corners: 9 banks × 18 loads = 162 decks.**
- **Banks:**
  - the contract ceiling, 180 / 120 / 180 µF (+12 / +5 / −12 V);
  - each corner of OSC's fitted bank at ±20 % (49.9 / 24.5 / 42.2 µF), on each rail independently.
- **Loads:**
  - 0 / planning / maximum on +12 V and −12 V (planning 1.5348 / 1.4356 A);
  - 0 / maximum on +5 V;
  - maximum is the contract's 2.1 / 2.0 / 0.5 A at nominal voltage.

## Reading rule (fixed now, before any result)
Every row is read on every sample from the EN_N rise to the end of the run.

| Row | Rule | Source |
| --- | --- | --- |
| Disconnect before discharge | The first sample where any discharge-switch current exceeds 10 mA comes after the last pass-pair current falls below 10 mA and stays there | CONTRACT §3 action order |
| Disconnect skew | The last pass-pair current falls below 10 mA within 1 ms of the first | §3, PROPOSED |
| Discharge level and time | +12 V ≤ 0.5 V, and −12 V and +5 V ≤ 0.6 V in magnitude, within 100 ms of the EN_N rise | §3 |
| R-VEE | No sample with +12 V > 0.5 V while \|−12 V\| ≤ 0.6 V, and none with \|−12 V\| > 6 V while +12 V ≤ 0.5 V | §3, using OSC's recommended absent levels (Q7, not yet recorded by OSC) |
| R-SW direct hazard | No sample with +5 V > 0.8 V while one analog rail is absent and the other is ≥ 8 V | §3 |

- **PASS (SIM)** means every row holds in all 162 decks, and all of them are COMPLETE.
- **FAIL (SIM)** means any row fails in any COMPLETE deck. The failing corners are listed.
- **NOT FORMED** means no row fails, but at least one deck did not complete.

**Reported, not read:**
- per rail, the peak discharge current, the energy into each discharge resistor, and the switch's peak current and
  peak power;
- the firing time, measured from the EN_N rise;
- the times of disconnect, discharge onset and reaching the discharge level.

These inform part selection. No pulse rating is judged here.

## What a PASS supports and what stays open
A PASS says the candidate meets the voltage-form discharge rows in this model, across OSC's committed per-rail load
range and bank tolerance. These stay open:
- the resistive-load ASSUMPTION;
- pulse-rated part selection and its owner records;
- the schematic change;
- layout for the pulse current paths;
- the bench check.

Converter shutdown on unplug is outside this deck. The pass pairs are open before any discharge, so the converter side
does not reach the OSC rails.

## Expectation (stated before the run, not a criterion)
- **All corners PASS.** The calculation passes every corner with ideal switches. The firing delay should keep the
  discharge after the disconnect, which was measured at 20–24 µs in phase 7.
- **The firing delays may not be matched across rails.** The −12 V switch's firing time differs from +12 V's. If
  the R-VEE row fails, it will be at the high-+12 V / low-−12 V bank corner, the margin edge in the calculation.
