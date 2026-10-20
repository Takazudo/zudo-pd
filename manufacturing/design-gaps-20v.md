# Design gaps for any 20 V input option

**Status: analysis and documentation only. Nothing here is adopted.** No schematic, PCB, BOM, NVM or part selection changes. Every schematic and PCB stays an unvalidated draft. Each "candidate" or "method" below is a direction to study, not a selection. No simulation, bench or measurement exists for anything on this page.

This list collects the gates that block adoption under **every** 20 V option (C1 20 V / 3 A, C2 20 V / 5 A, and the two-SKU high model). The input-contract decision does not close any of them. Sources:
- [`b1-gates.md`](b1-gates.md), rows R3, R4a–R4c, R6/TVS and R7;
- [`product-lineup.md`](product-lineup.md), "Behavior gates common to every option";
- the OSC integration reviews PWR-INT-03 and PWR-INT-05 (zudo-osc-hole-field#288, record in OSC PR #289 at `6491ff7`), which own demand and acceptance limits. PWR-INT-05 was not retrieved here; its content is taken from the pages above.

Status words: **OPEN** means no candidate has been screened to a result. **UNRESOLVED** means a candidate exists but its screen is incomplete. **NOT RUN** means the check needs simulation or measurement that does not exist.

Evidence classes: **G** guaranteed manufacturer limit · **G-U** guaranteed, but read only through a mirror or a summarizing fetch, no bytes retained · **DP** design point · **TYP** typical · **PA** project assumption · **S** secondary source · **CP(date, qty, currency)** catalog price · **UNAV** unavailable. All external parts new to this revision were read on 2026-10-20 through a summarizing fetch, so they are **G-U** or **S** at best; see [Sources](#sources-retrieved-2026-10-20). None of them has an owner bundle in this repository.

## Gap register

| ID | Gate | Requirement (not relaxed) | Current state | Status |
|---|---|---|---|---|
| GAP-1 | Input clamp vs STUSB4500 28 V absolute maximum | Every VBUS-side pin stays ≤ 28 V over the surge envelope and temperature | TVS2200 clamp 28.0 V (40 A, 27 °C) / 28.35 V (35 A, 125 °C), G: margin 0.00 / −0.35 V. Per-pin 470 Ω + BZX84-C24 candidate gives about 0.2–1.4 V hot at the table points (PA-dependent, not guaranteed). Fix proposal: [`input-clamp-fix.md`](input-clamp-fix.md) | **UNRESOLVED** |
| GAP-2 | CC pins vs 22 V absolute maximum | A CC-to-VBUS short at 20 V must not exceed 22 V on CC1/CC2 | 2 V nominal margin, about 1 V at 21 V ([`product-lineup.md`](product-lineup.md)); CC protector screen in [`input-clamp-fix.md`](input-clamp-fix.md) | **OPEN** |
| GAP-3 | Source voltage bands (PD-003-D5) | [R3.1–R3.4](#gap-3-source-voltage-bands-pd-003-d5) | DC: terminal sense plus precision reference reaches 8–20 mV setpoint error on paper. Dynamic: the B1 candidate filter exceeds the derived output-impedance ceiling on every rail without OSC capacitance and on −12 V and +5 V with it | **UNRESOLVED** |
| GAP-4 | Rail plus return loss (PD-003-D5) | [R4.1–R4.3](#gap-4-zero-added-drop-pd-003-d5) | Every series element must sit inside the regulation loop. In-loop drops 0.02–0.30 V per rail tabulated; loop stability with them NOT RUN | **UNRESOLVED** |
| GAP-5 | Output current upper limit (PD-003-D4) | [R5.1–R5.4](#gap-5-interface-current-upper-limit-pd-003-d4) | **No retrieved integrated limiter holds the ±12 V windows.** A shunt plus current-sense comparator with a reference-driven threshold reaches ±1.73 % worst case on paper (+12 V: 2.070 A max), with UNAV terms; −12 V needs a floated variant (NOT RUN). +5 V has a wide window | **UNRESOLVED** (±12 V: needs a decision, below) |
| GAP-6 | UVLO and simultaneous all-rail shutdown (PD-003-D4) | [R6.1–R6.6](#gap-6-input-uvlo-and-coordinated-all-rail-enable-pd-003-d4) | Supervisor or comparator with one common enable and a latch; candidates retrieved. VBUS_EN_SNK timing on hard reset and re-contract is not stated by ST | **UNRESOLVED** (bench needed) |
| GAP-7 | Reverse blocking per rail (PD-003-D4) | [R7.1–R7.3](#gap-7-reverse-blocking-per-rail-pd-003-d4) | Positive ideal-diode, eFuse and negative diode-OR controllers retrieved; reverse-current limit value not set by OSC | **UNRESOLVED** |
| GAP-8 | Ripple and noise (PD-003-D5) | [R8.1–R8.3](#gap-8-ripple-and-noise-pd-003-d5) | Arithmetic fundamental 0.02–0.05 mVpp (CCM). Post-LDO PSRR retrieved (TYP only; no guaranteed PSRR). Edges, ESL, +5 V DCM and pulse skipping not screened | **NOT RUN** |
| GAP-9 | Insufficient-source indication (PD-003-D4) | [R9.1–R9.4](#gap-9-insufficient-source-indication-pd-003-d4) | Four indicator methods compared; all need a Board P change | **UNRESOLVED** |
| GAP-10 | NVM programming in production | Every unit carries the intended PDO set and refuse policy | Per-unit NVM write plus readback is required; no retained NVM image | **OPEN** |

GAP-1 to GAP-8 are the blocking items listed by the integration review. GAP-9 and GAP-10 come from the product-lineup screen. Sections below cover **PD-003-D4** (safety: GAP-5, -6, -7, -9) and **PD-003-D5** (precision: GAP-3, -4, -8). Each section separates the requirement (implementation-neutral, testable) from the alternative methods (not chosen).

## Fixed inputs used below

| Input | +12 V | −12 V | +5 V | Class / owner |
|---|---:|---:|---:|---|
| Source band at the Board B source terminals | 12.00–12.30 V | 12.00–12.20 V (magnitude) | 5.05–5.10 V | OSC contract |
| Half-band (centered setpoint) | 150 mV | 100 mV | 25 mV | Arithmetic |
| 20 ms transient requirement (must not trip) | 2.0 A | 1.9 A | 0.4 A | OSC ledger |
| Interface maximum (must trip at or below) | 2.1 A | 2.0 A | 0.5 A | OSC ledger |
| Allowed limiter max/min ratio, and ± about center | 1.050, ±2.44 % | 1.053, ±2.56 % | 1.25, ±11.1 % | Arithmetic |
| Ancillary Board B current on the rail | 14 mA | 13.9 mA | 6.6 mA | [`supply-capability.json`](supply-capability.json) |
| OSC load capacitance | 120–180 µF | 120–180 µF | 80–120 µF | OSC contract (150 / 150 / 100 µF ±20 %) |
| Load step for the precision screen | 0.5 A | 0.5 A | 0.2 A | PA (b1-gates R4b); edge rate UNAV |

If the sense also sees a Board B ancillary current that can vary from 0 to its maximum, the windows shrink to ±2.09 % (+12 V) and ±2.20 % (−12 V). The ancillary values come from `supply-capability.json` for the current Board B and were not re-derived for B1. The sense must measure interface current only, or the tolerance must absorb this.

Netlist facts used (from [`board_p_spec.py`](../scripts/schgen/board_p_spec.py) and [`board_b_spec.py`](../scripts/schgen/board_b_spec.py)): JOUT1/J5 pins 1–2 carry VBUS_OUT and pins 5–6 GND. Board P: ATT = U1.11, J3.6, JOUT1.3; PDOK = U1.20 (POWER_OK2), J3.7, JOUT1.4. Board B: ATT = J5.3, P1.1; PDOK = J5.4, P1.2. Neither board has a pull-up on either net. The [owner bundle](../.claude/skills/component-stusb4500qtr/) records both as open-drain active-low (pin map). Its "10–100 k pull-up to a rail ≤ 5 V" is a project choice from the board-a interface (PROJECT_STATE, NEEDS BENCH), not a manufacturer limit. Its mirror Table 20 reading puts POWER_OK2, not ATTACH, in the 28 V high-voltage group; the ATT absolute maximum is UNAV.

TPS54560 EN is 1.1 / 1.2 / 1.3 V (G, from `b1-gates.md`). TPS54560 is the B1 candidate converter from [`supply-alternatives.md`](supply-alternatives.md), not a part on the current Board B.

## GAP-5: interface current upper limit (PD-003-D4)

### Requirement

| ID | What | Limit | Condition | Verified by |
|---|---|---|---|---|
| R5.1 | No trip at demand | No trip at ≤ 2.0 / 1.9 / 0.4 A on +12 / −12 / +5 V, including the 20 ms transient and the startup envelope (1.759 / 1.658 / 0.287 A) | All rails loaded at once; full VIN, temperature range (UNAV) and lifetime | Electronic-load step to each value for 20 ms, repeated; chamber |
| R5.2 | Trip at interface maximum | Trip at ≤ 2.1 / 2.0 / 0.5 A, interface current only | Same | Slow ramp until trip; record trip current per unit |
| R5.3 | All-rail consequence | A trip on any rail turns all three rails off through R6.2, latched per R6.4 | — | Scope all rails plus enable during trip |
| R5.4 | Trip time | Rail current above R5.2 for no longer than t_trip | t_trip UNAV: OSC to set with its conductor and connector ratings | Scope current probe |

### Alternative methods

| Method | Candidate (class) | Guaranteed limit used | Max/min ratio | +12 V (≤ 1.050) | −12 V (≤ 1.053) | +5 V (≤ 1.25) | Added drop at the max (in loop, R4.1) |
|---|---|---|---:|---|---|---|---|
| Integrated eFuse | TPS25947, latch or auto-retry variants (G-U, SLVSFC9C, revised May 2026) | RILM 1.65 kΩ: 1.800 / 2.028 / 2.200 A; "±10 % for ILIM > 1 A"; 2.7–23 V | 1.222 | FAIL | n/a (positive only) | FAIL: 6.65 kΩ row 0.425–0.575 A (1.353); 1.007 A row 0.850–1.150 A | ≤ 45 mΩ × 2.1 A = 95 mV |
| Integrated eFuse | TPS25982 (G, from `b1-gates.md`) | 2 A row 1.53–2.43 A | 1.59 | FAIL | n/a | UNAV | ≤ 4.5 mΩ: 9 mV |
| Integrated eFuse | TPS1663 (S, SLVSET9F overview page) | "±7 %" stated at 6 A only | ≈ 1.15 | FAIL | n/a | UNAV | UNAV |
| Hot-swap controller + shunt, fold-back | LTC4282 (G, from `b1-gates.md`) | 12.1 / 12.5 / 12.9 mV at FB 1.3 V, plus 0.5 % shunt (PA) | 1.077 | FAIL | n/a | **PASS on paper** | ≈ 13 mV + FET (UNAV) |
| Negative hot-swap controller | LTC4252 (S, catalog summary) | 50 mV breaker "±10 %"; Vin −15 to −500 V | ≈ 1.22 | n/a | FAIL; also below its 15 V minimum | n/a | UNAV |
| Shunt + current-sense comparator, resistor-set threshold, common shutdown | INA301A3 (G-U, SBOS713A) + 10 mΩ 0.1 %, 50 ppm/K shunt (PA) + 0.1 %, 25 ppm/K RLIMIT (PA) | Offset 35 µV + 0.5 µV/K drift; gain error 0.2 % + 10 ppm/K; comparator offset 4.5 mV at 25 °C; ILIMIT 79.2–80.8 µA over −40..125 °C TA; CM 0–36 V | 1.059 (±2.88 %) | FAIL by 19 mA (2.119 A max) | Floated variant only | PASS on paper | 21 mV (shunt) |
| Same, threshold driven from a precision reference | As above, LIMIT driven by REF50xxI 0.05 %, 3 ppm/K (G-U) through a 0.05 % divider (PA) | As above. LIMIT may be driven by an external voltage source (G-U, SBOS713A §7.3.3.2). ILIMIT 79.2–80.8 µA still flows into the driving source, so the threshold term must include ILIMIT × R_TH of the divider or buffer (UNAV until the network is drawn) | 1.035 (±1.73 %) | **PASS on paper** (2.070 A max) | PASS on paper (1.967 A max) only if floated on −12 V (NOT RUN) | PASS on paper | 21 mV |
| Fuse class | MF-MSMF250 PTC (G) | Hold 2.50 A at 23 °C; trip 5 A | not a window | Hazard protection only | same | same | 0.21 V (must be in loop) |

Worst-case linear budget for the comparator rows, as a percentage of a 20.5 mV sense signal (2.05 A × 10 mΩ, gain 100). The temperature span 25 → 125 °C is PA: the ambient range is UNAV, and the INA301 limits are stated over TA.

| Term | Resistor path | Reference path |
|---|---:|---:|
| Amplifier offset: 35 µV + 0.5 µV/K × 100 K = 85 µV | 0.41 % | 0.41 % |
| Gain: 0.2 % + 10 ppm/K × 100 K | 0.30 % | 0.30 % |
| Comparator offset: 4.5 mV / 2.05 V (25 °C only; full temperature UNAV) | 0.22 % | 0.22 % |
| Shunt: 0.1 % + 50 ppm/K × 100 K (PA) | 0.60 % | 0.60 % |
| Threshold, resistor path: ILIMIT ±1.0 % + RLIMIT 0.1 % + 25 ppm/K × 100 K (PA) | 1.35 % | — |
| Threshold, reference path: REF50xxI 0.05 % + 3 ppm/K × 100 K = 0.08 %; divider 0.05 % + 10 ppm/K tracking × 65 K = 0.065 % (PA); ILIMIT × R_TH UNAV | — | 0.195 % + UNAV |
| **Total** | **2.88 %** (ratio 1.059; 2.119 A max) | **1.73 %** (ratio 1.035; 2.070 / 1.967 A max) |

RSS is not used because only guaranteed limits are admissible.

**Plain finding.** No retrieved integrated eFuse, hot-swap controller or PTC holds the 2.0–2.1 A (+12 V) or 1.9–2.0 A (−12 V) window. The best integrated part, LTC4282, misses by 2.6 %: with its minimum at 2.0 A its maximum is 2.154 A (+12 V). It cannot be used on −12 V, where the same ratio would give 2.046 A. No negative-rail limiter with a guaranteed window was retrieved. Only the shunt plus current-sense comparator with a reference-driven threshold fits on paper, and only if four UNAV items close: the ILIMIT × source-impedance term, comparator offset over temperature, shunt TCR, and a floated −12 V implementation with a level-shifted fault. +5 V fits with LTC4282 or the comparator path.

| Method family | Pros | Cons / open |
|---|---|---|
| Integrated eFuse | One part; reverse blocking and UVLO included (TPS25947) | ±10 % class cannot hold the window; positive only |
| Hot-swap controller | Fold-back, timer, external FET sizing | ±3.7 % effective; FET SOA; positive only |
| Shunt + comparator + common shutdown | Best tolerance; one trip line can drive the common enable (R6.2) directly | Most parts; UNAV terms; −12 V needs a floating bias supply and level shift; blanking time must be defined against R5.1 |
| Fuse class | Simple; no tolerance chain | Does not enforce the interface maximum |

### Decision options for the ±12 V window (nothing decided)

This page holds the OSC limits fixed. Only options 3 and 4 act within them. Options 1, 2 and 5 would change the OSC contract; they are listed only so OSC can see the consequence, and this page proposes none of them.

1. **OSC widens its interface maximum** to at least the chosen limiter's guaranteed maximum, for example ≥ 2.16 / 2.05 A for LTC4282-class or ≥ 2.44 / 2.32 A for TPS25947-class. OSC decides.
2. **OSC lowers its no-trip transient demand** so the window grows. OSC decides.
3. **Pursue the discrete precision path** and close its UNAV terms by retrieval, then a bench trip test per unit.
4. **Per-unit calibration of the trip point** removes initial terms; drift terms stay and need guaranteed temperature data (UNAV).
5. **Accept fuse-class hazard protection only**, with the interface maximum held by OSC-side demand control instead of supply enforcement. This changes the OSC contract; OSC decides.

## GAP-6: input UVLO and coordinated all-rail enable (PD-003-D4)

### Requirement

| ID | What | Limit | Condition | Verified by |
|---|---|---|---|---|
| R6.1 | Input UVLO | All rails disabled while Board B input < V_UV. V_UV(fall, min) above the input at which any rail leaves its band at maximum load (UNAV; PA floor 14.0 V) plus margin. V_UV(rise, max) below the lowest valid 20 V input (18.4 V, PA). Hysteresis covers the cable step (UNAV) | Full temperature | Slow input ramp up and down on a lab source |
| R6.2 | One common disable | Every trigger turns all three stages off. Skew between the first and last enable deassert ≤ t_skew | t_skew UNAV; OSC to accept | Scope three EN pins and three rails |
| R6.3 | Trigger list | Input UV (detach, hard reset, charger swap, re-contract to 5 V, and a 5 A→3 A downgrade that changes the contract), any rail UV/OV, any R5 trip, any R7 reverse event | — | Each event on the bench |
| R6.4 | Latch | After any trigger, rails stay off until a fresh full-class contract exists. A trigger is cleared only by VBUS removal or by VBUS falling to vSafe0V; a hard reset (VBUS to vSafe0V) therefore clears it, and the restart still needs a fresh full-class contract. No automatic retry into a sag | — | Event, then restore input without re-plug: rails must stay off |
| R6.5 | Detection before regulation loss | t_detect + t_off < the time for the input to fall from V_UV to the regulation floor at maximum load | Example (PA): 100 µF input bulk, 52 W, 16.5 → 14.0 V ≈ 73 µs; so tens of µs | Scope VIN, EN and rails on a detach at full load |
| R6.6 | Common start | All three rails start from the same enable, inside the contract current, no faster than the OSC 10 ms minimum soft start, and within the OSC load-capacitance ceiling | — | Startup capture |

### Alternative methods

| Method | Candidate (class) | Guaranteed limits used | Pros | Cons / UNAV |
|---|---|---|---|---|
| A. Window comparator + common open-drain enable + latch | TPS3700 (G-U, SBVS187G) | VIT+ 396 / 400 / 404 mV, VIT− 387 / 394.5 / 400 mV (±1 % over temperature); hysteresis 5.5 TYP / 12 max mV; VDD 1.8–18 V (abs max 20 V); sense pins ≤ 6.5 V; open-drain outputs to 18 V; tPHL 18 µs TYP; TJ −40..125 °C | Few parts; µs detection; no firmware | Needs a bias rail ≤ 18 V from the 20 V input; external hysteresis and latch; one part per two thresholds |
| A′. Same with a general comparator and reference | LM393B (G in the OSC bundle `component-ti-lm393bidr`: offset 4.0 mV max, −40..85 °C) + REF50xxI (G-U) | As stated | Parts already in the OSC evidence set | Sibling evidence read from a local checkout (65cefd4) not verified against the epic pin |
| B. Sequencer / supervisor IC | LTC2928 (G-U, Rev C) | 4 channels; threshold 0.4925 / 0.500 / 0.5075 V over temperature (1.5 %); "any internal or external fault condition forces all enable outputs low"; one negative supply on V1; VCC 2.9–6 V or HVCC 7.2–16.5 V; C 0–70 °C, I −40..85 °C | Simultaneous fault shutdown, rail UV monitors and fault latch in one part; handles −12 V monitoring | Complex configuration; bias supply; I grade stops at 85 °C; normal power-down is reverse-sequenced (configuration UNAV) |
| C. Input eFuse UVLO + fault wired to the common enable | TPS25947 (G-U) | EN/UVLO rising 1.183 / 1.20 / 1.223 V, falling 1.076 / 1.09 / 1.116 V; latch-off (L) or auto-retry (A), tRST 110 ms TYP; FLT output on TPS259470x only, TPS259472x/474x have PG instead; 2.7–23 V, abs max 28 V | Adds input inrush, OV and reverse blocking in one part | Positive input only; rail faults still need A or B; the variant sets which output can drive the common enable |
| D. MCU supervisor | STM32G031-class (limits not retrieved here) | — | Flexible policy; can read STUSB4500 status over I2C | Firmware against the C2 "no firmware" basis; needs its own bias; boot time vs R6.5; watchdog |

**Contract awareness.** A voltage UVLO sees every event that moves VBUS: detach, hard reset (to vSafe0V) and re-contract to 5 V. Under the C2 NVM basis (PDO2 = 20 V / 3.5–5 A as the only 20 V PDO), a 3 A re-offer cannot match, so the device falls back to a 5 V contract (G-U, per the lineup's UM2650 reading), which UVLO sees. A current-class change that keeps 20 V is invisible to UVLO. PDOK cannot be the off-trigger because POWER_OK2 stays asserted after detach (G-U). It can only qualify the on-condition (R6.4). Whether Q1 opens before VBUS falls on a hard reset is UNAV: bench check.

## GAP-7: reverse blocking per rail (PD-003-D4)

### Requirement

| ID | What | Limit | Condition | Verified by |
|---|---|---|---|---|
| R7.1 | Unpowered Board B | Current into each terminal ≤ I_REV,max with the terminal held at 12.3 / −12.2 / 5.1 V | Board B input open or 0 V; temperature range; I_REV,max UNAV (OSC to set) | Source-measure unit on each terminal |
| R7.2 | Powered, rail forced high | Reverse current ≤ I_REV,max within t_REV after the terminal is forced ΔV beyond its setpoint | ΔV and t_REV UNAV (PA: 0.5 V, µs class) | SMU step plus current probe |
| R7.3 | No back-feed to the source | No reverse current into J5 / VBUS_OUT in any off state, including the R6 shutdown with OSC bulk charged | 150 µF ±20 % per ±12 V rail | Current probe on J5 during shutdown |

A probable back-feed path in the B1 candidate (not the current Board B): with the input collapsed, OSC bulk drives a buck output back through the inductor and the converter's high-side FET body diode to the input. The body-diode behavior is not stated in the retrieved TPS54560 limits: UNAV. The −12 V inverting stage has a different path, also UNAV.

### Alternative methods

| Method | +12 V | −12 V | +5 V | Candidate and limits (class) | In-loop drop at max | Pros / cons |
|---|---|---|---|---|---|---|
| A. Ideal-diode controller + NMOS | Yes | No (positive referenced) | Yes (ANODE ≥ 4 V) | LM74700-Q1 (G-U, SNOSD17G): VAK(REG) 13 / 20 / 29 mV; VAK(REV) −17 / −11 / −2 mV; tREVERSE 0.45 / 0.75 µs; ANODE 4–60 V; ANODE abs ±65 V; TA −40..125 °C | max(29 mV, I × RDS(on)); NMOS UNAV | Fast, low loss. Reverse current up to \|VAK(REV)\| / RDS(on) flows before turn-off; off-state leakage UNAV; its servo interacts with the terminal-sense loop (NOT RUN) |
| B. Negative-rail ideal diode (NMOS in the −12 V line) | — | Yes | — | LTC4354 (G-U, Rev C): ΔVSD 10 / 30 / 55 mV; gate pulled off at −140 mV reverse (text); tOFF 0.7 (TYP) / 1.2 (max) µs (column labels unclear in the fetch); shunt VZ 10.25–11.75 V; VCC 4.5 V–VZ; C 0–70 °C, I −40..85 °C; examples −5.2 to −72 V, no stated minimum | ≤ 55 mV + I × RDS(on) | The only retrieved negative-rail blocking controller. Shunt bias headroom at 12 V is small (screen needed); I grade 85 °C; dual-channel part used single (PA) |
| C. eFuse with back-to-back FETs | Yes | No | Yes | TPS25947 (G-U): VREVTH −36.45 / −29.3 / −22.3 mV; RON ≤ 45 mΩ; reverse leakage 10.1 µA at 21.5 V (as listed); input to −15 V | ≤ 95 mV | Combines reverse block, UVLO and OV; limit too wide for R5 |
| D. Schottky diode | Yes | Yes | Yes | No part retrieved: VF and hot leakage UNAV | Several 100 mV (UNAV); about 0.5–1 W per ±12 V rail | Simplest and polarity-agnostic; leakage may break R7.1; loss and heat |
| E. Converter disable only | Partial | Partial | Partial | — | 0 | Does not block the body-diode path; not sufficient alone |

## GAP-9: insufficient-source indication (PD-003-D4)

### Requirement

| ID | What | Limit | Condition | Verified by |
|---|---|---|---|---|
| R9.1 | Show on refuse | Indicator visibly on within t_ind (PA 1 s, covering negotiation) whenever VBUS_IN is present and no full-class contract exists | VBUS_IN 4.75–21 V (PA); charger matrix: 5 V only, 45 W, 60 W on a 3 A cable, 100 W on a 5 A cable | Charger and cable matrix |
| R9.2 | Clear on accept | Off within t_ind once the full-class contract exists | — | Same |
| R9.3 | Never with rails on | Indicator never on while Board B rails are on | Including hard reset and downgrade | Event matrix |
| R9.4 | Survive and stay within budgets | Survives VBUS-side transients up to the GAP-1 clamp; draw ≤ I_ind (PA, inside the 5 V default budget); respects ATT/PDOK pin limits (ATT absolute maximum UNAV; ATT is not in the 28 V high-voltage group) | — | Design check plus surge test |

The indicator must sit on Board P, fed from VBUS_IN, because Board B has no power on a refused contract.

### Alternative methods

| Method | Candidate (class) | Pros | Cons / UNAV |
|---|---|---|---|
| A. Logic "ATT asserted AND PDOK deasserted" + constant-current LED from VBUS_IN | NSI45020 (G-U, mirror, Rev 2): 45 V max; Ireg 17 / 20 / 23 mA at VAK 7.5 V, 25 °C; overhead 1.8 V TYP for 80 % | No firmware; uses existing signals | ATT needs a pull-up rail; the bundle's ≤ 5 V choice is project state, not a manufacturer limit (local LDO or zener). Dissipation about 0.43 W at 21 V (PA LED VF 2 V) is high for the package (UNAV). PDOK behavior on hard reset re-contract is UNAV |
| B. Voltage-qualified: "VBUS_IN present AND below about 17 V (PA)" | Comparator such as TPS3700 (G-U) | Independent of the POWER_OK latch; valid under the C2 policy, where refuse always ends in a 5 V contract | Only valid while no other PDO voltage is enabled; threshold and bias design needed |
| C. STUSB4500 GPIO configured in NVM | Function options UNAV in the owner bundle; GPIO is NC on Board P | Fewest parts | Depends on GAP-10 image and readback; ST behavior UNAV |
| D. MCU reading the RDO status over I2C | — | Most information | Firmware; I2C pull-up domain is the open VREG_2V7 loading gate |

## GAP-3: source voltage bands (PD-003-D5)

### Requirement

| ID | What | Limit | Condition | Verified by |
|---|---|---|---|---|
| R3.1 | DC band at the terminals | 12.00–12.30 / 12.00–12.20 (magnitude) / 5.05–5.10 V, measured Kelvin between each terminal and its GND terminal | Load from OSC minimum (UNAV) to continuous; input 18.4–21 V (PA); ambient range and lifetime UNAV (owner) | 6.5-digit DMM, 4-wire, in a chamber |
| R3.2 | Dynamic band | Terminal voltage stays inside the band during load steps | Step 0.5 / 0.5 / 0.2 A (PA), edge rate UNAV (OSC) | Scope with recorded bandwidth |
| R3.3 | Allocation | DC error + step excursion + ripple/2 ≤ 150 / 100 / 25 mV | — | Arithmetic from R3.1, R3.2, R8.1 |
| R3.4 | Derived output-impedance ceiling | Peak \|Zout\| ≤ (half-band − DC setpoint error of the chosen method) / step. Example with method C's 20 / 20 / 8 mV: ≤ 0.26 / 0.16 / 0.085 Ω | Including OSC load capacitance | Network analyzer or step response |

Without OSC capacitance the B1 peaks (0.33 / 0.47 / 0.32 Ω, PA, `b1-gates.md`) exceed the R3.4 ceiling on every rail. With OSC capacitance the peak is 0.23–0.41 Ω, not split by rail in `b1-gates.md`: even its low end exceeds the −12 V and +5 V ceilings, and +12 V is undetermined. **The dynamic term therefore forces a method change independent of the DC method.**

### Alternative methods (DC accuracy and dynamics)

| Method | DC setpoint error (worst-case) +12 / −12 / +5 | Fixes dynamics? | Candidate limits (class) | Pros / cons / UNAV |
|---|---|---|---|---|
| A. Internal reference, fixed divider | 144 / 144 / 59 mV: **FAIL** | No | TPS54560 VFB ±1 % (G) | Baseline only |
| B. Trimmed divider (per-unit) | Initial error removed; VFB temperature drift not separately specified: UNAV | No | — | Production trim step; drift not guaranteed |
| C. Terminal sense + outer DC servo with a precision reference | 20 / 20 / 8 mV (`b1-gates.md`) | No; inner loop still sets Zout | REF50xxI 0.05 %, 3 ppm/K (G-U); OPA2187 10 µV at 25 °C, full temperature UNAV (S); OPA4197 100 µV at 25 °C (G in the OSC bundle; local checkout 65cefd4, not verified against the epic pin) | DC fits all rails on paper. Open: divider tracking, reference long-term drift, authority clamp, −12 V level shift |
| D. Post-regulator LDO with SET driven from a precision reference | About 12 / 12 / 6 mV (reference 0.08 % + VOUT−VSET ±2 mV), plus SET-drive amplifier and divider terms (UNAV) | Likely; LDO Zout UNAV | LT3045-1 (G-U): 2–20 V in, 500 mA, ISET 98–102 µA, VOUT−VSET ±2 mV, current limit 570 / 710 / 850 mA at VIN 2 V, VOUT 0 V, paralleling supported (20 mΩ ballast, ≤ 20 % sharing). LT3094 (G-U, mirror): −2.3 to −20 V, 500 mA, ±2 mV, dropout 410 mV max at 500 mA | ±12 V at 2.1 A needs 5–6 parallel devices per rail. Tied SET pins source 5 × 100 µA that the reference or its buffer must sink. Ballast drop (≈ 10 mV) sits outside the loop unless a servo trims SET. About 0.5 V × 2 A ≈ 1 W headroom loss per rail; the LT3045-1 VIOC output can hold the switcher headroom. TJ −40..125 °C |
| E. Post-LDO with RSET only | ±2 %: 243 / 243 / 101 mV: **FAIL** | Yes | LT3045-1 / LT3094 ISET ±2 % (G-U) | Simple but too coarse |

## GAP-4: zero added drop (PD-003-D5)

### Requirement

| ID | What | Limit | Condition | Verified by |
|---|---|---|---|---|
| R4.1 | No added drop | Terminal voltage meets R3.1 at every load up to the R5.2 trip current; Board B carries no allowance for drop between any internal regulation point and its source terminals | All loads | 4-wire terminal voltage at 0 / continuous / transient load |
| R4.2 | Headroom | The regulator covers the sum of in-loop drops at the trip current, at the worst input and temperature | — | Arithmetic plus bench |
| R4.3 | Stability and fault states | Loop stable with OSC capacitance and each in-loop element in every state (conducting, limiting, blocking). A bounded output if the sense path opens (authority clamp or OVP) | — | Simulation (NOT RUN), then Bode/step bench |

### In-loop drop per element at the trip current (headroom cost, not a terminal error)

| Element | +12 V at 2.1 A | −12 V at 2.0 A | +5 V at 0.5 A | Class |
|---|---:|---:|---:|---|
| Shunt 10 mΩ (R5 comparator path) | 21 mV | 20 mV | 5 mV (or 50 mΩ: 25 mV) | PA |
| LM74700 + NMOS | ≤ 29 mV + I × RDS(on) | — | ≤ 29 mV | G-U / UNAV |
| LTC4354 + NMOS | — | ≤ 55 mV + I × RDS(on) | — | G-U / UNAV |
| TPS25947 | ≤ 95 mV | — | ≤ 23 mV | G-U |
| MF-MSMF250 PTC, if kept | 0.21 V (0.44 W) | 0.20 V | 0.05 V | G |
| Paralleled LDO ballast, if outside the servo | ≈ 10 mV, **violates R4.1** | ≈ 10 mV | — | G-U example |

Methods: (A) terminal sense around all series elements (shunt, blocking device, eFuse, PTC, filter, copper, terminal), so every one sits inside the loop, with an authority clamp; (B) remove series elements outside the loop, so protection becomes sense-plus-shutdown instead of a PTC; (C) post-LDO Kelvin-sensed at the terminal, with upstream elements absorbed by the LDO headroom. In every case the loop includes devices with their own servo or limit behavior (ideal-diode regulation, eFuse limiting): interaction NOT RUN. Renegotiating the 0.2 V budget is an OSC decision, not a method.

## GAP-8: ripple and noise (PD-003-D5)

### Requirement

| ID | What | Limit | Condition | Verified by |
|---|---|---|---|---|
| R8.1 | Ripple at load | < 1 mVpp per rail, inside the bands | All loads from OSC minimum (DCM and pulse skip included) to transient; input 18.4–21 V; bandwidth B UNAV (agree with OSC) | Scope, recorded bandwidth, short ground spring or coax |
| R8.2 | OSC noise gates | OSC 2 mV / 1 mV precision gates | As OSC defines | OSC procedure |
| R8.3 | No sub-corner bursts | No burst or skip frequency below the filter corner at any load | — | Spectrum at minimum load |

### Alternative methods

| Method | Result available | Candidate limits (class) | Pros / cons / open |
|---|---|---|---|
| A. Two-stage LC + damping | 0.023–0.047 mVpp fundamental, CCM arithmetic (`b1-gates.md`) | TPS54560 fsw min 450 kHz (G) | No new parts; ESL, edges, DCM, skip NOT RUN |
| B. Post-LDO after the switcher (with or without LC) | 14.6 mVpp × 10^(−76/20) ≈ 2 µVpp at 1 MHz (arithmetic on a TYP figure; no guaranteed bound) | LT3045-1 76 dB at 1 MHz (TYP); LT3094 74 dB at 1 MHz (TYP); both at 2 V headroom and 500 mA; noise 0.8 µVrms 10 Hz–100 kHz (TYP) | Also helps R3.2. PSRR at about 0.5 V headroom and 450 kHz UNAV; 1 W loss per ±12 V rail |
| C. Keep CCM: preload or forced PWM | Avoids the DCM / skip cases | No forced-PWM converter retrieved; preload is PA | Preload costs power and thermal margin |
| D. A + B combined | — | — | Most robust on paper; most parts and loss |

## Comparison and marked candidate directions (not adopted)

| Gap | Candidate direction, **not adopted** | Why | What must close first |
|---|---|---|---|
| GAP-5 | ±12 V: shunt + current-sense comparator with a reference-driven threshold, tripping the common enable. +5 V: the same or LTC4282 class | Only family with a paper window; integrated parts miss by ≥ 2.6 % | The ILIMIT × source-impedance term, comparator offset over temperature, shunt TCR, and a floated −12 V implementation with a level-shifted fault; or an OSC decision from the option list |
| GAP-6 | Hardware supervisor with one common open-drain enable and a fault latch cleared only by VBUS removal (A or B) | No firmware; µs detection; matches all-on / all-off | Bias rail, thresholds vs regulation floor, VBUS_EN_SNK bench timing |
| GAP-7 | LM74700-class + NMOS on +12 / +5 V, LTC4354-class on −12 V, all inside the terminal-sense loop | Lowest drop; retrieved reverse thresholds | I_REV,max from OSC; NMOS selection; loop interaction |
| GAP-9 | Voltage-qualified indicator on Board P (B), optionally ANDed with ATT | Avoids the POWER_OK latch | Board P change approval; threshold and bias design |
| GAP-3 / 4 / 8 | Terminal-sensed regulation with every series element in the loop and a precision reference. A post-LDO stage is the method that addresses R3.4 and R8.1 together | DC fits on paper; only the LDO path also lowers Zout and ripple | Zout and PSRR at real headroom, paralleling, thermal, loop stability: NOT RUN |

## How each gap could close

| ID | Next analysis (no design change) | Needs a decision | Needs simulation or bench |
|---|---|---|---|
| GAP-1 | Define a surge envelope (waveform, energy, cable inductance); screen an input OVP or surge-stopper and the alternative controllers (CYPD3177 30 V, AP33772S 34 V) | PD-003-D3 controller choice | Surge test |
| GAP-2 | Retrieve CC protection parts rated above 22 V and confirm PD signaling compatibility | — | Short test |
| GAP-3 | Retrieve LDO load-transient and Zout data; agree step amplitude and edge rate with OSC; close the servo UNAV terms | PD-003-D5 | Loop stability, load step |
| GAP-4 | Screen terminal-sense stability with OSC capacitance and in-loop devices | PD-003-D5 | Loop stability |
| GAP-5 | Size the LIMIT drive impedance; retrieve comparator drift over temperature; screen a floated −12 V sense with a level-shifted fault; options 1, 2 and 5 are OSC's to consider, not proposed here | OSC interface limit; PD-003-D4 | Trip test per unit |
| GAP-6 | Draft the enable and latch chain and its timing against R6.5 | PD-003-D4 | Detach, hard reset and downgrade tests |
| GAP-7 | Obtain I_REV,max from OSC; screen NMOS and LTC4354 bias at 12 V | PD-003-D4 | Back-feed test |
| GAP-8 | Add ESL, DCM and pulse-skip screens; agree the measurement bandwidth with OSC | — | Ripple and noise measurement |
| GAP-9 | Draft methods A and B against R9.1–R9.4 | PD-003-D4; Board P change | Charger matrix |
| GAP-10 | Define the NVM image and readback procedure | PD-003-D1 | Programming bench check |

None of these steps changes a schematic, PCB or part selection until the owner approves it. Promoting any G-U fact below to G needs retained primary bytes and an owner bundle through the component-spec-audit workflow.

## Sources retrieved 2026-10-20

| Part | Document | Class |
|---|---|---|
| TPS25947 | [TI SLVSFC9C](https://www.ti.com/lit/pdf/slvsfc9) | G-U |
| LM74700-Q1 | [TI SNOSD17G](https://www.ti.com/lit/ds/symlink/lm74700-q1.pdf) | G-U |
| INA301 | [TI SBOS713A](https://www.ti.com/lit/gpn/INA301) | G-U |
| TPS3700 | [TI SBVS187G](https://ti.com/lit/gpn/TPS3700) | G-U |
| LTC4354 | [ADI Rev C](https://www.analog.com/media/en/technical-documentation/data-sheets/4354fc.pdf) | G-U |
| LTC2928 | [ADI Rev C](https://wcm-cce.cldnet.analog.com/media/en/technical-documentation/data-sheets/ltc2928.pdf) | G-U |
| LT3045-1 | [ADI 30451fa](https://www.analog.com/media/en/technical-documentation/data-sheets/30451fa.pdf) | G-U |
| LT3094 | [Rev 0, xdevs mirror](https://xdevs.com/doc/Linear/Datasheets/LT3094_Rev0_9-5-18.pdf) | G-U (mirror) |
| NSI45020 | [onsemi Rev 2, TI E2E mirror](https://e2e.ti.com/cfs-file/__key/communityserver-discussions-components-files/196/NSI45020JZ_2D00_D.PDF) | G-U (mirror) |
| OPA2187 | [SBOS807A summary, radiolocman](https://www.radiolocman.com/datasheet/data.html?di=305585) | S |
| TPS1663 | [SLVSET9F overview page, alldatasheet](https://www.alldatasheet.com/html-pdf/2230695/TI2/TPS1663/959/14/TPS1663.html) | S |
| LTC4252 | [Rev E summary, radiolocman](https://www.radiolocman.com/datasheet/data.html?di=401315) | S |

Carried over from [`b1-gates.md`](b1-gates.md) and [`supply-alternatives.md`](supply-alternatives.md) unchanged: TPS54560 (G), TPS25982 (G), LTC4282 (G), MF-MSMF250 (G), REF50xxI (G-U). Prices were not retrieved for any new part: CP UNAV.
