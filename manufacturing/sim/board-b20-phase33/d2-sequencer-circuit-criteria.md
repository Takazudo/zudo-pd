# D2 discrete −12 V sequencer: what is simulated and how it is read, stated before the dispatch

**This is a candidate evaluation, not a design adoption.** It tests the drafted discrete sequencer
([design draft](d2-sequencer-design.md)) in place of the behavioural clamp that passed in
[the sequenced run](d2-sequenced-20261114.md). Nothing in the schematic, PCB, BOM or inventory changes.
electrical_acceptance stays **NOT ESTABLISHED** and D2 stays a pre-order hold.

## The deck
The deck is the [sequenced deck](d2-sequenced-criteria.md) unchanged, except that `BHOLD` is replaced by the drafted
network:
- QR, QP, QH and QN;
- RSQ1–RSQ4;
- the 10k / 1M QR gate network;
- the zener DZS with a 4.7k bias.

QP takes its supply from the behavioural `dis` node, which is 0 V before the EN_N rise and 4.9 V after it. That
matches DIS_C only being driven during discharge.

**The small parts are generic models set to corner values. They are not vendor models.**

| Part | Model | Corner values |
| --- | --- | --- |
| QN, QR | level-1 NMOS, KP 0.1 | VTO 0.5 V (project PA minimum) or 1.5 V (sourced maximum) |
| QH | level-1 NMOS | VTO 1.5 V |
| QP | level-1 PMOS | VTO −2.5 V (sourced DMP3036SFG-7 maximum) |
| DZS | diode | BV at IBV 0.2 mA, the switching-point current: 3.0 V (PA, below the 5 mA guarantee) or 4.1 V (DS18004 maximum at 5 mA) |

**Corner combinations, each over all 243 bank and load corners (972 decks, `d2sc/<combo>-<bank>-<loads>`):**

| Combo | QN VTO | VZ | QR VTO | H | Release |
| --- | --- | --- | --- | --- | --- |
| `hlrl` | 0.5 V | 3.0 V | 0.5 V | about 3.5 V | 0.5 V |
| `hlrh` | 0.5 V | 3.0 V | 1.5 V | about 3.5 V | 1.5 V |
| `hhrl` | 1.5 V | 4.1 V | 0.5 V | about 5.6 V | 0.5 V |
| `hhrh` | 1.5 V | 4.1 V | 1.5 V | about 5.6 V | 1.5 V |

The solver settings, the run rule (an abort is recorded and not retried), the EN_N edge and the timing origin are
unchanged.

## Reading rule (fixed now, before any result)
The rows are the same five, read by `d2_fast_discharge.read`.
- **PASS (SIM):** every row holds in all 972 decks, and all are COMPLETE.
- **FAIL (SIM):** any row fails in any COMPLETE deck. The failing count is listed per combo.
- **NOT FORMED:** no row fails, but at least one deck did not complete.

## Expectation (stated before the run, not a criterion)
PASS. In the ideal-switch calculation, `hlrh` fails 18 of 10,935 cases, at the high-+12 V / low-−12 V banks with
−12 V at maximum load. A local smoke test with a stand-in power FET (not evidence) passed those decks: −12 V stayed at
or above 1.52 V while +12 V was present. The calculation's sharp threshold does not model the clamp's gradual
turn-off.

## What a PASS supports and what stays open
A PASS supports the drafted topology at the threshold and zener corners stated, with generic models. These stay open:
- the BZT52C3V9-7-F candidate identity (LCSC number) and its audit;
- a sourced low-current VZ bound;
- vendor models for the small FETs;
- the schematic, layout and bench check.
