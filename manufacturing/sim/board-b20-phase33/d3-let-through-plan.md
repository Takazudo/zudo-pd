# D3 let-through: the trip chain's first-order detection-to-off is about 0.1–0.3 ms, so a hard short will exceed the literal maxima

OSC E22 keeps the 2.1 / 2.0 / 0.5 A maxima literal, with let-through included. It asks the PD side for a worst-case
envelope per rail: peak, duration above the maximum, I²t, and detection-to-off. This note traces the drawn trip chain,
gives first-order CALCULATED figures, and states the simulation that would bound them. It changes no design.
electrical_acceptance stays **NOT ESTABLISHED** and D3 stays a PRE-ORDER HOLD.

## The drawn chain from detection to off (`board_b20_spec.py`)

| Step | Parts | Time | Basis |
| --- | --- | --- | --- |
| 1. Detect | U11/U12 INA301A3 alert; U9A for −12 V | ≤ 1 µs (1 mV overdrive), ≤ 1.5 µs slew-limited | SBOS713A tp MAX, the source already hash-locked in the limiter owner (`src-c2861552-primary`); not yet a recorded fact |
| 2. FAULT_N falls | RF1 10k pull-up, **CF1 100 nF** to P5_SUP; Q31 turns on after a 1.0–2.5 V drop | about 20–50 µs at an assumed 5–10 mA alert sink | Alert sink current UNSOURCED |
| 3. Latch | Q31 → RF2 4.7k → FLT_L, **CF3 100 nF**, RF3 100k; Q39 trips at VGS(th) 0.5–1.5 V | 49–171 µs | CALCULATED, τ ≈ 448 µs to the 4.76 V final value |
| 4. Enable falls | Q39 pulls EN_E; Q33 releases; EN_N rises through REN 10k into the gate loads | about 10–20 µs | Gate charge is a PA |
| 5. Pass pairs open | Q10/Q11 (+12 / +5) and Q24/Q25 (−12) pull the CSD18543Q3A gates | about 25 µs | Attempt-2 shutdown decks (behavioural pulldowns) |

The first-order detection-to-off is therefore about **0.1–0.3 ms**. It is set mostly by the two 100 nF latch filter
capacitors. Nothing in the chain limits current while it runs.

## What flows in that time
- **Overload just above the trip** (for example 1.2 × maximum): the rail delivers its overload current until the pass
  pair opens. The excess above the maximum lasts about 0.1–0.3 ms.
- **Hard short at the terminal:** the 57 µF PRE capacitors discharge through the shunt, the pass pair and the cable.
  The first microseconds reach the order of a hundred amps, and the I²t from that dump alone is of order 0.1 A²s. The
  converter's own current limit then holds until the pass pair opens. OSC's bank also discharges into the short, but
  that is OSC-side current.

These figures are order-of-magnitude CALCULATED. The cable and inlet are not selected (E22), and several chain values
are unsourced. They show that a trip-only limiter cannot hold the literal maximum under a fast fault: the delivered
current exceeds it for the whole detection-to-off time.

## Proposed next step (no design change)
Pre-register a fault-chain simulation that extends the shutdown deck with:
- the drawn FAULT_N / latch / enable network, with Q31 and Q39 at their threshold corners;
- the INA301 alert as a 1 µs delay with a PA sink current;
- three fault classes per rail:
  - a step to 1.2 × maximum;
  - a step to 2 × maximum;
  - a terminal short through an assumed 20 mΩ / 100 nH cable, flagged ASSUMPTION.

It would report peak, duration above the maximum, I²t and detection-to-off for each class, rail and corner. That is the
envelope E22 asks for, and it would be sent to OSC as SIMULATED.

## The decision that will follow
If the envelope exceeds the maximum, which the arithmetic above says it will, the owner chooses one of three paths:
- ask OSC for a let-through amendment, checked against the inlet connector and cable once selected (E22's stated
  route);
- shorten the chain, for example by reducing CF1 and CF3, which trades away noise immunity;
- add a regulating current limit, which is a design change with a thermal cost in the pass pairs.
