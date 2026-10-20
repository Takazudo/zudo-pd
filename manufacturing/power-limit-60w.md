# 60 W-class input with a usage limit (screen)

**Status: screening analysis only. Nothing here is adopted.** No schematic, PCB, BOM, NVM or part selection changes. Every schematic and PCB stays an unvalidated draft. **Nothing on this page is measured.** A usage limit is a product rule. It is not a measurement, not a safety certification, and not a change to any existing budget or OSC contract value. A measurement plan is included, but it has **not** been run and needs owner approval.

Figures come from [`../scripts/pcb/calculate-power-limit-60w.py`](../scripts/pcb/calculate-power-limit-60w.py) (sections 1–11). It reuses, unchanged:
- from [`../scripts/pcb/calculate-supply-alternatives.py`](../scripts/pcb/calculate-supply-alternatives.py): the efficiency sets, ancillary currents, PTC terms and input-power method;
- from [`../scripts/pcb/calculate-product-lineup.py`](../scripts/pcb/calculate-product-lineup.py): the source-band voltages, board-input points and hold-up integration.

Context: [`supply-alternatives.md`](supply-alternatives.md), [`b1-gates.md`](b1-gates.md) (R3, R7), [`product-lineup.md`](product-lineup.md), [`design-gaps-20v.md`](design-gaps-20v.md) (GAP-5, -6, -7, -9).

**Evidence class** (where a number comes from): **G** guaranteed manufacturer limit · **G-U** guaranteed, read only through a mirror or summarizing fetch · **DP** design point · **TYP** typical · **PA** project assumption · **S** secondary source, never a pass · **CP** catalog price · **UNAV** unavailable.

**Basis** (how the number was obtained), on every table: **calc** = screen arithmetic from the cited inputs · **unver** = a source value, assumption or judgment not checked on hardware · **meas** = retained measurement. **No number on this page is meas.** Every calc number inherits PA efficiencies, so it is also unverified.

## Scope and owner direction

- Evaluate a **20 V / 3 A contract (60 W PDP)** as a formal candidate, with a product usage limit instead of guaranteeing all OSC maxima at once.
- A caution note alone never makes droop, oscillation, thermal stress or missing protection safe, and "low probability" is never a PASS. A safe limit needs a defined mechanism: all-rail refusal or trip, state indication, and startup control where needed.
- Three powers are kept separate: charger W (at the USB-C port), board-input W and rail-output W. The charger's AC input power is a fourth quantity and is not modeled.
- The OSC owner owns OSC demand. Its decomposition is used [below](#osc-demand-decomposition-against-the-envelope) unchanged. This page invents no OSC circuit numbers.
- The existing OSC values stay unchanged as the **verification record**:

  | OSC record point | +12 / −12 / +5 V |
  |---|---|
  | Canonical | 1.535 / 1.436 / 0.224 A |
  | Continuous | 1.7 / 1.6 / 0.3 A |
  | 20 ms transient | 2.0 / 1.9 / 0.4 A |
  | Startup envelope | 1.759 / 1.658 / 0.287 A |
  | Interface maximum | 2.1 / 2.0 / 0.5 A |

  Any lower figure below is a **new candidate operating range** and is labeled as one.
- Option names: **C1-L** is the fixed 20 V / 3 A contract with a usage limit and a safe trip. **C2** is the fixed full-OSC contract, 20 V at 3.5 A or more.

## 1. Input chain: charger to rails

Board B is the switcher-direct candidate (3× TPS54560) with MF-MSMF250 rail PTCs, as in the B1 screen. Output power is taken at the OSC source-band upper voltages, 12.3 / 12.2 / 5.1 V.

| Stage | Value | Class | Basis |
|---|---|---|---|
| Charger port, 20 V / 3 A fixed PDO | 60.0 W | S: USB PD power rules via the Renesas tutorial; primary text UNAV | unver |
| Board input at the PA derate point (18.67 V) / extra cable-drop point (18.4 V), 3.0 A | 56.0 / 55.2 W | PA | calc |
| Power not available at the board input under the PA derate rule (14.0/15 scaling: Q1, cable and connector; whether it also covers source tolerance is PA) | 4.0 / 4.8 W | PA | calc |
| of which Q1 at 3 A: AO3401A fitted / AOD4185L B1 candidate (25 °C max RDS(on) at −4.5 V) | 0.585 / 0.180 W | G | calc |
| Board P input PTC | none fitted (the Board P spec has Q1 and D5 only) | — | — |
| Input W per rail-output W, base / −3 pt / −5 pt, +12 V | 1.087 / 1.124 / 1.149 | PA | calc |
| same, −12 V inverter | 1.176 / 1.220 / 1.250 | PA | calc |
| same, +5 V | 1.205 / 1.250 / 1.333 | PA | calc |
| Rail PTC I²R and ancillary currents (14 / 13.9 / 6.6 mA) | included per rail | G / calc | calc |

Whether a sink-side trip exists sets the usable input current. A trip's guaranteed **maximum** must stay at or below 3.0 A. Legitimate demand must therefore stay below its guaranteed **minimum**, which is 3.0 A ÷ (max/min ratio).

| Input trip candidate | Max/min ratio (class) | Legitimate maximum | Board input W (18.67 / 18.4 V) | Basis |
|---|---:|---:|---|---|
| None (the charger's OCP decides) | — | 3.000 A | 56.0 / 55.2 W | calc |
| INA301 + reference-driven LIMIT (external drive permitted, G-U; ILIMIT × source impedance UNAV) | 1.035, ±1.73 % (G-U + PA) | 2.899 A | 54.1 / 53.3 W | calc |
| INA301 + resistor-set LIMIT | 1.059, ±2.88 % (G-U + PA) | 2.833 A | 52.9 / 52.1 W | calc |
| LTC4282 hot-swap limiter with fault timer | 1.077 (G + PA shunt) | 2.786 A | 52.0 / 51.2 W | calc |

The INA301 ratios come from GAP-5 in `design-gaps-20v.md`, where they were computed for a 20.5 mV / 2.05 V rail sense signal. They are reused unchanged. The reuse is conservative only if the input shunt × gain gives at least that signal (≥ 6.9 mΩ at 3 A, PA); no shunt is chosen.

The contract limits **current**, so the trip must sense current. A power trip adds a multiplier and its error, and it does not match the contract.

INA301 is a trip comparator, not a limiter: it switches the rails off but does not limit current.

### Rail-output envelope (OSC continuous shape, all rails scaled together)

| Envelope | No trip | INA301 ref | INA301 res | LTC4282 | Basis |
|---|---|---|---|---|---|
| **Continuous**, scale of 1.7 / 1.6 / 0.3 A | 1.066–1.148 | 1.031–1.110 | 1.007–1.085 | 0.991–1.067 | calc |
| Continuous rail output | 44.8–48.2 W | 43.2–46.6 W | 42.3–45.5 W | **41.6–44.8 W** | calc |
| Worst-case currents at that scale | 1.81 / 1.71 / 0.32 A | 1.75 / 1.65 / 0.31 A | 1.71 / 1.61 / 0.30 A | 1.68 / 1.59 / 0.30 A | calc |
| **20 ms peak**, no hold-up | same as continuous; source overload is UNPROVEN and gets no credit | 43.2–46.5 W | 42.2–45.5 W | 41.5–44.7 W | calc |
| 20 ms peak with hold-up | not creditable without a limiter | n/a (see note) | n/a (see note) | table below | calc |

**Note on the INA301 hold-up cells.** A comparator does not limit, so it gets no hold-up credit. Hold-up needs a limiter whose maximum sits below the trip minimum. Stacked under the INA301 reference path (ratio 1.077 × 1.035 = 1.115, limit 2.691 A), 4.7 mF is EDGE and 10 mF covers the transient. Neither recharges at continuous load (calc).

**Hold-up behind a limiter (droop to the PA 14.0 V floor, OSC transient shape):**

| Limiter (limit minimum) | Continuous, no hold-up | 2.2 mF | 4.7 mF | 10 mF | Recharge at canonical / continuous, 4.7 mF | Basis |
|---|---|---|---|---|---|---|
| LTC4282 (2.786 A) | 41.5–44.7 W | 44.3–47.9 W, short | 50.9–55.4 W, covers | 65.6–72.1 W, covers | 0.07 s / **never** | calc |
| LTC4282-class under an INA301 reference trip (2.691 A) | 40.2–43.2 W | 43.0–46.5 W, short | 49.6–54.0 W, **EDGE** | 64.4–70.7 W, covers | 0.10 s / **never** | calc |

Assumptions and limits of this table:
- Ranges span the three PA efficiency sets and both board-input points.
- The bulk is assumed to start full at the board-input voltage, and the limiter to hold its minimum (b1-gates R3 integration).
- 2.2, 4.7 and 10 mF are grid points. The minimum capacitance between 2.2 and 4.7 mF was not computed.
- The capacitors must be rated above the 28 V TVS2200 clamp; their surge rating is UNAV.
- Inrush, fault timer and FET SOA are open (R3). LTC4282 fold-back must stay disengaged down to the 14.0 V floor; that needs an FB divider, which is UNAV.

**One rail raised alone, the other two at canonical planning (calc):**

| Trip | +12 V | −12 V | +5 V |
|---|---|---|---|
| None | 2.15–2.43 A | 2.00–2.27 A | 1.49–2.14 A |
| LTC4282-class | 1.88–2.15 A | 1.76–2.01 A | 0.94–1.54 A |

A single rail is also bounded separately by the MF-MSMF250 hold of 2.50 A at 23 °C (G), which is lower when warm, and by the OSC interface maximum.

### OSC record points against the envelope

| OSC point (record; not changed) | Rail output | Board input current | No trip | INA301 ref | INA301 res | LTC4282 | Basis |
|---|---:|---|---|---|---|---|---|
| Canonical 1.535 / 1.436 / 0.224 A | 37.5 W | 2.33–2.51 A | PASS +0.49 A | PASS +0.39 A | PASS +0.32 A | PASS +0.27 A | calc |
| Continuous 1.7 / 1.6 / 0.3 A | 42.0 W | 2.61–2.81 A | PASS +0.19 A | PASS +0.09 A | PASS +0.02 A | **EDGE −0.03 A** | calc |
| Startup envelope 1.759 / 1.658 / 0.287 A | 43.3 W | 2.70–2.90 A | PASS +0.10 A | **EDGE −0.01 A** | **EDGE −0.07 A** | **EDGE −0.12 A** | calc |
| 20 ms transient 2.0 / 1.9 / 0.4 A | 49.8 W | 3.11–3.35 A | **FAIL −0.35 A** | **FAIL −0.45 A** | **FAIL −0.51 A** | **FAIL −0.56 A** | calc |

- Margins are at the worst efficiency set and board-input point. PASS needs a strictly positive worst-case margin. A zero or negative worst case with a passing best case is EDGE.
- The "No trip" PASS rows are input arithmetic only. They leave the behavior above 3.0 A to the charger, which section 2 classes as undefined.

**Reading.**
- **Transient.** On a 60 W contract the OSC transient needs 3.5–11.5 % more board-input current than the contract allows (3.11–3.35 A against 3.0 A). With a safe trip it misses by 0.45–0.56 A.
- **Continuous and startup.** Both sit at the trip edge.
- **Hold-up.** The transient fits only with ≥ 4.7 mF behind an LTC4282-class limiter with a fault timer, or ≥ 10 mF behind a limiter stacked under an INA301 trip. In both cases the bulk never recharges at continuous load.
- **The owner's "64 W assumed, 60 W supplied" example** compares load watts with charger watts. At the OSC shape a 60 W charger yields about **42–48 W of rail output** (41.6–48.2 W; 41.6–46.6 W with a safe trip), not 60 W.

## OSC demand decomposition against the envelope

Source: OSC integration owner, [zudo-osc-hole-field#288 comment](https://github.com/Takazudo/zudo-osc-hole-field/issues/288#issuecomment-6285046629), record PR #289 at commit `17fd7469dd6dd191fc0e71f84bf44e9b9f19a5bd`. Every OSC value is **OSC-owned, calculated and unverified; none is measured**, and none is changed here.

The decomposition (mA at +12 / −12 / +5 V):

| Component | mA | Note |
|---|---|---|
| Fixed / quiescent | 1327 / 1228 / 184 | 86 / 86 / 82 % of planning |
| Patch- or indicator-dependent | 174 / 174 / 0 | |
| Internal signal paths | 28 / 28 / 0 | |
| Knob / operation | 6 / 6 / 41 | |

OSC notes that only 3.3 mA on +5 V is removable as double counting. It also notes that the transient excess comes from the startup capacitance ramp, which a usage notice cannot reduce.

Comparison method:
- Worst-case board-input current over the efficiency sets and board-input points, against a safe trip minimum less the 5 % guard (PA): 2.646 A for LTC4282-class, 2.754 A for the INA301 reference path.
- Per-rail currents against the [R60 caps](#candidate-operating-range-r60-new-not-adopted-user-terms).
- W at the user-terms voltages 12 / 12 / 5 V.

| OSC row | A at +12 / −12 / +5 | W (12/12/5 V) | Board input | vs 3.0 A, no trip | vs LTC4282 + guard | vs INA301 ref + guard | Within R60 caps (LTC4282 basis) | Basis |
|---|---|---:|---|---|---|---|---|---|
| Normal typical | 0.882 / 0.822 / 0.109 | 21.0 | 1.33–1.44 A | PASS +1.56 | PASS +1.21 | PASS +1.32 | Yes | calc |
| OSC usage-limit candidate | 1.386 / 1.287 / 0.203 | 33.1 | 2.10–2.26 A | PASS +0.74 | PASS +0.39 | PASS +0.49 | Yes | calc |
| Heavy realistic patch (realistic simultaneous max) | 1.535 / 1.436 / 0.221 | 36.8 | 2.33–2.51 A | PASS +0.49 | PASS +0.14 | PASS +0.24 | Yes | calc |
| OSC ×1.1 rule on the candidate: 1.6 / 1.5 / 0.3 (PWR-D5 candidate only) | 1.6 / 1.5 / 0.3 | 38.7 | 2.46–2.65 A | PASS +0.35 | **EDGE −0.001** | PASS +0.11 | **No** (+5 V 0.3 > 0.28) | calc |
| Continuous requirement | 1.7 / 1.6 / 0.3 | 41.1 | 2.61–2.81 A | PASS +0.19 | **EDGE −0.17** | **EDGE −0.06** | **No** | calc |
| Startup worst envelope | 1.759 / 1.658 / 0.287 | 42.4 | 2.70–2.90 A | PASS +0.10 | **FAIL −0.26** | **EDGE −0.15** | **No** | calc |
| 20 ms transient requirement | 2.0 / 1.9 / 0.4 | 48.8 | 3.11–3.35 A | **FAIL −0.35** | **FAIL −0.70** | **FAIL −0.59** | **No** | calc |

The W column uses 12 / 12 / 5 V. The section 1 tables use the source-band maxima, which gives 37.5, 42.0, 43.3 and 49.8 W for the same points.

**What a usage limit can cover (screen only).** Normal typical (21 W), the OSC usage-limit candidate (33 W) and the heavy realistic patch (36.8 W) fit R60 on input current and per-rail caps, with a safe trip and a 5 % guard. The heavy realistic patch has 0.14 A (LTC4282) or 0.24 A (INA301 reference) margin. That margin rests on PA efficiencies and on OSC values that are themselves unverified.

**What a usage limit cannot cover.**
- **Startup envelope (42.4–43.3 W).** It exceeds every safe trip with the guard. It is set by OSC's capacitance ramp at power-on, so no user rule changes it. It needs a supply-side startup control that keeps the ramp inside the trip (slower common soft start or inrush limiting; the OSC contract's 10 ms soft start is a minimum, so a slower ramp is within contract, and the open question is only whether OSC circuits tolerate it) or a contract change (C2).
- **20 ms transient (48.8–49.8 W).** It exceeds the contract itself. OSC attributes it to the same startup ramp, so the same two remedies apply: startup control, or C2. Hold-up of 4.7–10 mF behind a limiter is the only screened in-contract path, and it never recharges at continuous load.
- **The continuous requirement and the OSC ×1.1 point.** Both are at or over the edge. They would need the INA301 reference path with its UNAV terms closed, and even then the margin is zero to 0.11 A.

## 2. Above the envelope with no added protection

| Event | Possible physical behavior | Determined by | Class |
|---|---|---|---|
| Board input exceeds 3.0 A | The charger continues, folds back (constant current, VBUS sags), enters hiccup, issues a hard reset, or latches off | The charger's design. USB PD does not require continuous overload support (TI SLVAFR4 §4.3, G-U). The Peak Current overload profile is UNPROVEN (S only) | **Undefined**: source-dependent and not characterized (charger matrix NOT RUN) |
| VBUS sags but stays above the sink window | Board B input falls; the switchers draw more current, which deepens the sag (a constant-power load on a current-limited source) | Converter behavior at low input; efficiency and UVLO limits UNAV | **Unsafe**: positive-feedback collapse with an undefined outcome |
| VBUS leaves the STUSB4500 monitor window (default −15 % for PDO2, about 17.0 V, G-U) | The sink reaction (flag, hard reset or path off) is not established | ST behavior on undervoltage and VBUS_EN_SNK timing UNAV | **Undefined** |
| Rails sag unequally | The −12 V inverter and the +12 V / +5 V bucks drop out at different input voltages, so one rail can collapse while the others remain | No input UVLO or common enable today (GAP-6) | **Unsafe for OSC**: violates all-on / all-off. Effects of a partial rail loss on OSC circuits are UNAV (OSC owner) |
| Hard reset or charger hiccup cycles | Rails cycle on and off repeatedly, and each restart adds startup inrush | Charger retry timing UNAV | **Unsafe**: repeated partial brownouts |
| OSC bulk back-feeds a collapsing Board B | Reverse current through converter body diodes toward VBUS | GAP-7 open | **Unsafe / undefined** |
| Rails leave the OSC bands during the event | Violations of 12.00–12.30 / 12.00–12.20 / 5.05–5.10 V | Nothing above guarantees the bands | **Fail** of the OSC contract |

None of these is acceptable as the intended behavior of a usage-limited product. A usage limit is admissible only with a mechanism that turns "over the limit" into a defined all-rail-off state before any of these occur.

## 3. Safe-limit mechanisms

### Requirements (implementation-neutral, not adopted)

| ID | Requirement |
|---|---|
| L1 | Board input current never exceeds 3.0 A for longer than the shortest source reaction time in the qualified charger set (UNAV until M5). |
| L2 | Any limit event ends with **all three rails off together**, latched (GAP-6 R6.2–R6.4). Input-side limiting into hold-up is allowed only while every rail stays in band, and the limiter's fault timer must end in this all-off state. Rail-side limiting or sag is never allowed. LTC4282 fold-back must stay disengaged down to the 14.0 V floor (FB divider UNAV). |
| L3 | No trip at any demand inside the published usage limit, including its startup and peaks. A trip on a legitimate transient is a **functional failure**. |
| L4 | The user can tell the states apart: normal, near limit, tripped, insufficient source. |
| L5 | Restart only by a defined user action on a valid 20 V / 3 A contract. No automatic retry into a sag. |
| L6 | Startup input current stays below the trip minimum. Rails ramp no faster than the OSC 10 ms minimum soft start and stay within the load-capacitance ceiling; any slower ramp must be accepted by OSC. |

### Alternatives compared

**Trip mechanisms**

| Mechanism | What it guarantees | Required accuracy | False-trip risk vs legitimate peaks | Added cost driver | Test burden |
|---|---|---|---|---|---|
| **M-a** Input current monitor + latching all-rail shutdown below 3.0 A | L1 and L2 for any load mix, with one threshold | Max/min ≤ 3.0 A ÷ realistic peak draw. No ratio works at the OSC transient (3.35 A). At the continuous point (2.81 A) the ratio must be ≤ 1.067: the INA301 paths meet that on paper; LTC4282 (1.077) misses | High, unless the published limit leaves the trip window plus a guard. Blanking must cover realistic spikes yet act before the charger does (M5) | Shunt, comparator or controller, reference and latch; a MOSFET if it is a limiter; calibration if trimmed | Per-unit trip ramp at temperature; blanking against the charger matrix |
| **M-b** Per-rail limits; any trip turns all rails off | Each interface current; L2 | Per GAP-5, the ±12 V windows need ±2.4–2.6 %. Only the INA301 reference path fits on paper | Same as M-a, per rail | Three sense chains, one floated for −12 V | Three trip ramps per unit |

**Per-rail limits alone (M-b) do not guarantee L1** (calc):
- Trips at the interface maxima allow 3.29–3.55 A of board input.
- To keep the sum ≤ 3.0 A, the per-rail trip maxima must fall to 0.847 × interface max = 1.78 / 1.69 / 0.42 A.
- To keep it under an LTC4282-class input minimum, they must fall to 0.787 × interface max = 1.65 / 1.57 / 0.39 A.

Legitimate demand must sit lower again, by the per-rail ratio. Both sets are below the OSC transient, and the second is below the OSC continuous requirement.

**Startup, indication, reset and hold-up**

| Mechanism | What it guarantees | Required accuracy | False-trip risk | Added cost driver | Test burden |
|---|---|---|---|---|---|
| **M-c** Startup control: common hold-off until the contract is valid (and any hold-up is charged), then one common soft start | No start before a valid contract; Board B and hold-up bulk charged before the rails rise. **It cannot lower OSC's startup envelope**, which is EDGE against every safe trip (calc) | Enable thresholds per GAP-6 (TPS54560 EN 1.1–1.3 V, G) | The startup envelope (2.70–2.90 A) already sits at the trip edge, so a cold start can trip without a slower ramp accepted by OSC | Supervisor or comparator, latch, soft-start network | Cold-start capture at line, load and temperature corners |
| Sequenced soft start (rails one after another) | A lower startup peak, but it conflicts with the OSC all-rails-together rule (R6.6), so OSC must accept the skew | Sequence timing | Lower | Sequencer | As M-c |
| **M-d** State indication: off / insufficient source / normal / near limit / tripped | L4 | The near-limit threshold must sit below the trip minimum by more than the sense error. It is advisory only | None (indication only) | LEDs on Board P (fed from VBUS_IN, GAP-9) and Board B; reuses the M-a sense chain | Indicator truth table across the event matrix |
| **M-e** Reset policy | L5 | — | — | Latch reset path | Event matrix |
| — re-plug only | Simple; never retries into a fault | | | | |
| — user button with a forced off time | Convenient | | | Button and timer | |
| — auto-retry | **Not admissible**: it cycles into repeated brownouts | | | | |
| Hold-up bulk behind an input limiter (not behind a comparator) | Lets 20 ms peaks exceed the continuous envelope | Limiter accuracy as above | Recharge needs spare power, and there is none at continuous load | 4.7–10 mF rated above the 28 V TVS2200 clamp (surge rating UNAV); inrush control; FET SOA | Peak repetition tests |

**Plain finding.** A 60 W product can be made to fail safe with M-a, M-c, M-d and M-e. It can carry OSC's realistic patch rows on this screen. It cannot carry the recorded startup envelope or the 20 ms transient through a usage notice: those need supply-side startup control accepted by OSC, or C2. Every trip threshold also depends on OSC realistic peak data, which does not exist yet. A trip during a performance is a functional failure.

## 4. Options: rough cost ratios, complexity and user constraints

Ratios are relative to **C2 = 1.0** and follow `product-lineup.md`. All of them are rough judgments (**PA, unver**), not calculations; most underlying prices are UNAV. The two ratio columns are separate measures and are not combined: the first is the manufacturing cost of one unit; the second is the one-off design, verification and test effort.

| Option | Per-unit manufacturing cost (1 unit) | Design and test effort (one-off) | Main drivers (UNAV unless noted) |
|---|---|---|---|
| **C2** fixed full-OSC, 20 V ≥ 3.5 A, 5 A e-marked cable | 1.0× | 1.0× | No input trip or hold-up. The shared gates remain: UVLO / common enable, indicator, servo |
| **C1-L** 20 V / 3 A + R60 + input trip, latch, common start and 4-state indicator | about 1.05–1.15× | about 1.3–1.6× | Input trip chain and calibration; charger-OCP matrix; startup control work with OSC |
| **A1** general adaptive PD | about 1.1–1.3× | ≥ 2× | MCU and firmware; three sense chains (one floated); class lines and a header change; firmware × charger × cable matrix |
| **B-common** (lineup definition: one PCB, low image 15 V / 3 A) | ≈ 1.0× | 1.0–1.1× | Two NVM images and labels |
| **B-common-pop** | 0.95–1.0× | 1.1–1.3× | Two BOM/CPL variants. A low variant on a 20 V image overstresses SMAJ16A. A 20 V / 3 A low SKU would need the 20 V parts set |
| **B-separate** | ≈ 1.0× | 1.5–2× | Two layouts and two ERC/DRC/parity sets. A 20 V / 3 A low board would need the 20 V parts set |
| **B-common-L** (both SKUs carry the C1-L trip hardware; low image 20 V / 3 A) | 1.05–1.15× | 1.4–1.8× | One PCB. The NVM image and the trip-threshold population differ per SKU (or a class-selected threshold, UNAV). Misprogramming a high image onto a low threshold trips under OSC |

Retrieved IC deltas from the lineup screen are small (CP, 2026-10-20): the MCU is about $0.9–1.2 and the 20 V Board P set about $0.4–0.9 per set. The prices of the trip chain, hold-up capacitors, chargers and cables are UNAV. Qualitatively, a charger of 70–100 W or more with a 5 A e-marked cable is a higher tier than 60 W with a 3 A cable.

| Option | Charger and cable | Usage limit | What the indicator means |
|---|---|---|---|
| C1-L | A 20 V / 3 A PD charger (60 W PDP or more) and a cable rated ≥ 3 A | R60, below | Insufficient source: outputs stay off. Near limit: advisory, close to the trip. Tripped: all outputs off until re-plug |
| C2 | 20 V at the chosen PDO2 current (≥ 70–100 W) and a 5 A e-marked cable | None beyond the OSC record values | Insufficient source: outputs stay off |
| A1 | Any PD charger; the rating follows the negotiated class | Per class (lineup class table); OSC requires the top class | The class is shown. Below the configured minimum class, outputs stay off |
| B-common-L | Low SKU as C1-L; high SKU as C2 | Low: R60; high: none | As C1-L / C2 |

### Candidate operating range R60 (NEW; not adopted; user terms)

R60 is stated only so the owner can judge it. It does not replace any OSC value and is not verified.

How the caps were derived (section 9 of the script):
- Take the OSC continuous shape (1.7 : 1.6 : 0.3).
- Scale it until the worst-case board input (worst efficiency set, cable point, source-band voltages) equals 95 % of the trip minimum.
- Round each rail down to 10 mA.

| Rule (user terms) | Candidate value | Basis |
|---|---|---|
| Power source | A USB-C PD charger that offers **20 V at 3 A**, and a cable rated at least 3 A. With any other charger the outputs stay off | unver (S: PD rules) |
| Load limit, all rails at once, including the power-on surge and short peaks | **+12 V ≤ 1.60 A, −12 V ≤ 1.50 A, +5 V ≤ 0.28 A** (about 38.6 W at 12 / 12 / 5 V). Derived at the worst efficiency set and cable point, with an LTC4282-class trip and a 5 % guard (PA); these caps draw 2.640 A worst case against 2.646 A. With the INA301 reference path and a 5 % guard the caps are 1.66 / 1.56 / 0.29 A (40.1 W), pending its UNAV terms. The trip and indicator supply currents are not yet designed (UNAV) and are excluded | calc |
| Peaks | No peak above these limits. Hold-up is not part of R60 | unver |
| Startup | The rails start together after the contract is valid. The power-on surge counts against the load limit, and OSC's startup envelope does not fit it (see above) | calc / unver |
| Exceeding the limit | All outputs switch off together and stay off; unplug the charger to restart. This protects the charger and the rails. It does not make overload a supported condition | unver (mechanism not designed) |
| Not allowed | Full OSC as recorded: continuous 1.7 / 1.6 / 0.3 A (42.0 W), the startup envelope (43.3 W) and the 20 ms transient (49.8 W) all exceed R60 | calc |

**R60 and OSC.** R60 cannot serve OSC through a usage notice alone. Its +5 V cap (0.28 A) does not cover the OSC ×1.1-rule candidate (0.3 A), and on ±12 V it leaves only about 4 % above the heavy realistic patch (1.60 / 1.50 A against 1.535 / 1.436 A) where the OSC rule asks for 10 %. Using R60 for OSC would require changing the OSC reserve and rounding rule, which is an OSC PWR-D5 decision. OSC's new fitted-capacitance startup row, 1.610 / 1.498 / 0.240 A (39.3 W; OSC #288 integration review W1–W7, PR #289 at `195b3f5`; calculated, unverified), is **EDGE** against the LTC4282-basis R60 caps: +12 V is about 10 mA over.

### Slower common startup ramp (W60-D3 candidate; calculated only, not adopted)

The OSC contract's 10 ms soft start is a minimum, so a slower supply-side common ramp is **contract-compatible**. Its benefit below is **calculated only**. OSC has no evidence yet that its circuits behave correctly on a slow ramp: the reset RC timing, VEE5 brownout behavior, rail-order tolerance and absolute-maximum facts are open on the OSC side. Before the ramp can be relied on, a local measurement campaign is needed: 6 rail orders × 10 / 20 / 50 ms ramps, checking VEE5, injection currents, reset timing and latch-up.

**A paper fit at startup is not acceptance.** A slower ramp addresses only the startup capacitance charge. It does not change the contract's 20 ms transient requirement (2.0 / 1.9 / 0.4 A), the accuracy windows, or the OSC reserve and rounding rule (PWR-D5). Each of those is judged separately, and none passes because the ramp fits.

Script section 11 scales the fitted startup row (1.610 / 1.498 / 0.240 A at 10 ms) as follows (PA): the steady part is the heavy realistic patch (1.535 / 1.436 / 0.221 A) and the capacitance-charging excess scales as 10 ms ÷ ramp time. Margins are worst-case board input against the limit, over the efficiency sets and board points.

| Case | 10 ms | 12 ms | 20 ms | 50 ms | Ramp needed for the R60 per-rail caps |
|---|---|---|---|---|---|
| 60 W, LTC4282 + 5 % guard (2.646 A) | +0.015 A | +0.035 A | +0.075 A | +0.111 A | ≥ 11.5 ms (+12 V: 1.610 A at 10 ms vs 1.60 A cap; 1.573 A at 20 ms) |
| 60 W, INA301 reference + 5 % guard (2.754 A; UNAV terms open) | +0.123 A | +0.143 A | +0.182 A | +0.218 A | 10 ms (caps 1.66 / 1.56 / 0.29 A) |
| 70 W, 20 V / 3.5 A, no trip | +0.862 A | +0.882 A | +0.922 A | +0.958 A | No R60 caps; no slower ramp needed |

Status: calc, unverified. The scaling law is an assumption. OSC owns its startup demand and whether a slower ramp is acceptable; the question is with the OSC owner.

## 5. Measurement plan (not executed; requires owner approval)

No step below has been run. Running any of it is an outward hardware action that needs the owner's explicit approval. It also needs a built prototype, which does not exist.

| ID | What | Method | Acceptance criterion (candidate) |
|---|---|---|---|
| M1 | OSC realistic-patch power | Log each OSC rail current and voltage at ≥ 10 kS/s for ≥ 1 h per patch, over an owner-defined set of worst realistic patches | The maximum 20 ms moving-average total, converted to board input, is ≤ trip minimum − guard (guard PA 5 %), and each rail is ≤ its R60 cap. In addition, the instantaneous peak board-input current (at the trip's blanking bandwidth) stays ≤ trip minimum − guard, and the peak per-rail current stays ≤ its R60 cap. Report P50 / P99.9 / max |
| M2 | Startup peak | 50 cold starts per corner (input 18.4–21 V; ambient range UNAV) with OSC attached | Input current stays ≤ trip minimum − guard throughout; rails ramp no faster than the OSC 10 ms minimum and reach their bands within the ramp time OSC accepts; no trip |
| M3 | Transient duration and repetition | From M1 and scripted patch changes: the duration, amplitude and spacing of every event above the continuous envelope | No event exceeds the R60 limits |
| M4 | Trip threshold | Per unit: slow ramp of board input until trip, at the temperature extremes | Trip within [min, max], with max ≤ 3.0 A and min ≥ M1 max + guard. All rails off together, skew ≤ t_skew (OSC to set), latched until re-plug |
| M5 | Source OCP behavior | A PD trigger plus an electronic load (not the product): step to 3.05 / 3.2 / 3.5 A for 20 ms, 100 ms and 1 s on each charger × cable | Record the mode (continue / foldback / hiccup / hard reset / latch) and the time to act. The M4 trip time must be shorter than the shortest source reaction in the qualified set |
| M6 | All-rail behavior | Detach, hard reset, charger swap, re-contract and overload, all at full load | No rail out of band while another is on; all off within t_skew; no back-feed (GAP-7) |
| M7 | Thermal at the envelope | Continuous R60 load for 1 h at the highest intended ambient | Component temperatures within their limits (limits per owner bundles); PTC hold not reached |

Equipment (candidates only; nothing purchased or requested):
- USB PD protocol analyzer or trigger board;
- programmable electronic loads with a 20 ms dynamic mode, one floated for −12 V;
- 4-channel oscilloscope with two DC current probes;
- logging power analyzer, or a shunt plus DAQ at ≥ 10 kS/s;
- USB-C cable e-marker reader;
- thermocouples or a thermal camera;
- a charger matrix: several 60 W-class models from different makers, plus 65 / 100 W models behind 3 A cables;
- 3 A and 5 A e-marked cables of several lengths.

## 6. Owner choices (minimal; recommendation marked, not adopted)

1. **W60-D1.** Keep C1-L (60 W class, R60 and a safe trip) as a formal candidate? Yes or no.
2. **W60-D2.** If yes, choose the mechanism set: input trip with latching all-rail off (M-a), common startup hold-off (M-c), 4-state indicator (M-d) and re-plug reset (M-e).
3. **W60-D3.** Ask OSC whether its startup ramp can be slowed under supply-side control to fit the trip. Without that, the startup envelope blocks C1-L for OSC.
4. **W60-D4.** Approve the measurement plan later, when hardware exists.

**Recommendation (marked; not adopted).**
- Keep **C2** as the full-OSC supply basis.
- Treat C1-L as a candidate for a light or general SKU (B-common-L low image) under R60. On this screen it would carry OSC's normal typical, usage-limit candidate and heavy realistic patch rows. It should not be offered for OSC until two things hold: the startup envelope fits through a supply-side startup control accepted by OSC, and M1–M3 data confirm the realistic peaks.
- If C1-L proceeds: an input current trip on the INA301 reference path, after closing its UNAV terms; a common startup hold-off; a 4-state indicator; and re-plug reset. No hold-up at first: 4.7–10 mF adds inrush, SOA and rating problems and never recharges at continuous load.

### Open gates

| Gate | Status |
|---|---|
| OSC realistic data (the decomposition is calc and unverified); acceptance of a slower startup ramp | **OPEN** (OSC owner) |
| Source OCP behavior across chargers | **NOT RUN** (M5) |
| Trip accuracy: INA301 ILIMIT × divider/buffer source impedance, comparator offset over temperature, shunt TCR, floated −12 V | **UNRESOLVED** (GAP-5) |
| UVLO, common enable and latch timing; VBUS_EN_SNK timing on hard reset | **UNRESOLVED** (GAP-6) |
| Reverse blocking | **UNRESOLVED** (GAP-7) |
| Indicator on Board P | **UNRESOLVED** (GAP-9) |
| Hold-up inrush, fault timer, FET SOA, repetition, capacitor surge rating; LTC4282 fold-back FB divider | **UNRESOLVED** (R3) |
| Efficiency, thermal, ripple and source bands | **NOT RUN** (all options) |
| TVS vs STUSB4500 28 V; CC 22 V | **UNRESOLVED / OPEN** (GAP-1, GAP-2) |
