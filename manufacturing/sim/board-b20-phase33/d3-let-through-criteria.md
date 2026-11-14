# D3 let-through: what is simulated and how it is read, stated before the dispatch

**This is an envelope report, not a design adoption and not a pass/fail against the literal maxima.** It runs the drawn
trip chain traced in the [D3 plan](d3-let-through-plan.md) against three fault classes per rail. It produces the
per-rail peak, duration above the maximum, I²t and detection-to-off that OSC E22 asks for. Nothing in the schematic,
PCB, BOM or inventory changes. electrical_acceptance stays **NOT ESTABLISHED** and D3 stays a PRE-ORDER HOLD.

## The deck (`d3_let_through.py`, 36 decks, `d3lt/<rail>-<fault>-<q31><q39>`)

| Part of the deck | How it is modelled | Basis |
| --- | --- | --- |
| Converters | 20 mΩ small-signal source with a smooth saturation at 8.3 A, behind 57 µF PRE | TPS54560 SLVSBN0C current-limit maximum (VIN 12 V row). ASSUMPTION: the limit acts as a DC output-current limit |
| Shunts and pass pairs | As drawn: 10 / 20 / 10 mΩ, vendor CSD18543Q3A pairs, behavioural 3.5 Ω gate pulldowns keyed on EN_N | Attempt-2 shutdown decks |
| Alert | Comparator on the delivered current at the design trip point (2.085 / 0.461 / 1.996 A), RC delay, open-drain sink of 100 Ω | Delay: INA301 tp maximum 1 µs (SBOS713A); U9A 10 µs (OPA2187 typical recovery and slew, PA). Sink: VOL 300 mV at 3 mA, extrapolated (PA) |
| FAULT_N, fault latch, enable latch | RF1 / CF1, Q30, Q31, RF2 / RF3 / CF3, Q39, Q33 / Q34, RE1 / RE2 and REN as drawn in `board_b20_spec.py`; 1 nF on EN_N for the gate loads (PA) | Generic level-1 FETs |
| Start | Both latches held in the enabled state until 50 µs, then released, and the alert armed | Modelling initial condition in place of the POR and RDY paths. Not a drawn part |
| OSC side | Fitted bank with 50 mΩ ESR; the two unfaulted rails at planning load | OSC owner-reported bank (ASSUMPTION for ESR and loads) |
| Fault, at 0.5 ms on one rail | `x12`: resistor drawing 1.2 × maximum at nominal voltage. `x20`: 2 × maximum. `sht`: 100 nH plus 20 mΩ to ground | Cable values are an ASSUMPTION (E22: cable and inlet not selected) |

**Corners:** Q31 VTO −1.0 V (`f`) or −2.5 V (`s`), and Q39 VTO 0.5 V (`f`) or 1.5 V (`s`). The 0.5 V Q39 minimum is a
PA; the other bounds follow the plan. Solver: gear, `.tran 0.1u 1.5m 0 0.1u`. The run rule is unchanged: each deck
runs once, and an abort is recorded and not retried.

## Readouts (per deck, from the delivered current after the fault)
- **peak_a:** the largest delivered current.
- **duration_above_max_ms:** total time above the contract maximum (2.1 / 0.5 / 2.0 A).
- **i2t_a2s:** ∫ i² dt from the fault to the end. **excess_i2t_a2s:** ∫ (i − maximum)² dt over the time above it.
- **detect_ms:** first crossing of the trip point. **off_ms:** when the delivered current last falls to 10 mA.
- **detection_to_off_ms:** off minus detect.
- **enabled_before_fault:** EN_N below 0.5 V and the current below the trip point, 10 µs before the fault.

The envelope per rail and fault class is the maximum of each readout over the four corners.

## Reading rule (fixed now, before any result)
- **ENVELOPE FORMED (SIM):** all 36 decks are COMPLETE, every deck was enabled before the fault, and every deck opened.
  The envelope is then sent to OSC as SIMULATED, with the assumptions above.
- **NOT FORMED:** any deck is not COMPLETE, was not enabled before the fault, or did not open. No envelope is sent.

Neither reading judges the maxima. Whether the envelope is acceptable is OSC's call under E22, and the route that follows
is the owner's choice (see the plan).

## Expectation (stated before the run, not a criterion)
ENVELOPE FORMED, with every rail above its maximum. A local smoke test with a stand-in power FET (not evidence) gave a
detection-to-off of about 0.07–0.21 ms, set by the Q39 corner. The overload peaks were 1.2 or 2 × maximum. The short
peaked at about 130 A on ±12 V and 60 A on +5 V, with an I²t of about 0.1 A²s on ±12 V.
