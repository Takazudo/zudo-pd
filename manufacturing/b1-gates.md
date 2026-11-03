# B1 gate screens: ripple, voltage bands, loss, transient path and input clamp

**Status: screening analysis only. This is a draft.** No schematic, PCB, BOM or part selection changes here, and nothing is adopted. Every fix below is a **candidate**. Every schematic and PCB stays an unvalidated draft. Ripple, loop stability, surge, thermal and startup are **NOT RUN**: no simulation, bench or measurement exists.

Scope: option **B1** from [`supply-alternatives.md`](supply-alternatives.md): 20 V / 3 A USB-PD; Board B switcher-direct TPS54560 bucks (+12 V, +5 V) and a TPS54560 inverting buck-boost (−12 V); LC post-filters; MF-MSMF250/16X-2 PTCs. Rows follow the OSC integration review **PWR-INT-03** (zudo-osc-hole-field#288; record in OSC PR #289 at `6491ff7`, R2–R4, R6, R7). Figures come from [`../scripts/pcb/calculate-b1-gates.py`](../scripts/pcb/calculate-b1-gates.py), which reuses the loads, ancillary currents and PA efficiency sets of [`../scripts/pcb/calculate-supply-alternatives.py`](../scripts/pcb/calculate-supply-alternatives.py). External sources were retrieved on 2026-10-20.

Evidence classes: **G** guaranteed manufacturer limit · **G-U** guaranteed, but retained only from a mirror or secondary summary · **DP** design point · **TYP** typical · **PA** project assumption · **CP(date)** catalog price · **UNAV** unavailable.

## OSC acceptance limits (OSC contract values; not relaxed here)

| Limit | +12 V | −12 V | +5 V |
|---|---:|---:|---:|
| Source band at the source terminals | 12.00–12.30 V | 12.00–12.20 V | 5.05–5.10 V |
| Ripple at load (inside the bands; bandwidth recorded at qualification) | < 1 mVpp | < 1 mVpp | < 1 mVpp |
| Rail plus return loss, source to load | ≤ 0.20 V | ≤ 0.20 V | ≤ 0.20 V |
| OSC's own allocation of that loss (conductors, 92 mV return shift, 40 mV protection, 20 mV distribution) | 0.194 V | 0.192 V | 0.162 V |
| Load capacitance ceiling, nominal (±20 %) | 150 µF | 150 µF | 100 µF |

Source: OSC `design/power/supply-architecture.json` at `6491ff7`. The 0.2 V budget lies **downstream** of the source terminals, and OSC already allocates 96–97 % of it on ±12 V. Any Board B drop outside regulation therefore appears as a source-band error. It cannot be booked against the 0.2 V budget.

## R2: input current at the source-band maxima

At 12.3 / 12.2 / 5.1 V output, with PTC I²R at R1max (G) and PA efficiency sets, the screen gives:
- **Continuous:** 2.61–2.77 A at 18.67 V and 2.65–**2.81 A** at 18.4 V (PWR-INT-03: about 2.82).
- **20 ms transient:** 3.10–3.35 A.

## R4: ripple, source bands and loss (analysis 1)

### Candidate output filters (all values PA; C means effective capacitance after DC bias)

| Rail | Stage 1 | Stage 2 | Damping leg | Loop crossover |
|---|---|---|---|---|
| +12 V buck, 2.0 A | L1 10 µH; C1 24 µF | Lf 2.2 µH, 10 mΩ; C2 20 µF MLCC, 2 mΩ, 0.5 nH | Cd 100 µF + Rd 0.33 Ω (≈ Z0) | 20 kHz |
| +5 V buck, 0.4 A | L1 6.8 µH; C1 40 µF | as +12 V | Cd 220 µF + 0.33 Ω | 20 kHz |
| −12 V inverter, 1.9 A | L1 10 µH; C1 40 µF | Lf 4.7 µH, 15 mΩ; C2 20 µF | Cd 100 µF + 0.47 Ω | 10 kHz (RHP zero ≈ 90 kHz at 18.67 V) |

Switching runs at 500 kHz nominal and is screened at the 450 kHz minimum (G, TPS54560 RT 200 kΩ). At 21 V the +5 V on-time is 0.51 µs, against the 135 ns minimum (TYP).

| Rail | Stage-1 ripple, worst VIN | Stage-2 gain at 450 kHz | Output, harmonics 1–50 | Against 1 mVpp |
|---|---:|---:|---:|---|
| +12 V | 14.6 mVpp (21 V) | 1/381 | 0.032 mVpp | Arithmetic margin about 30× |
| −12 V | 46.7 mVpp (pulsed, 18.4 V) | 1/813 | 0.047 mVpp | About 20× |
| +5 V | 10.6 mVpp, CCM only | 1/381 | 0.023 mVpp | About 40× in CCM. The planning load is DCM (below) |

The method (harmonic sum through the complex Lf/C2/Rd–Cd divider) is in the script. These caveats are **NOT RUN**:
- **ESL floor.** Attenuation flattens to ESL/Lf ≈ 1/4400–1/9400 above about 2 MHz. Layout ESL is UNAV.
- **Edges.** Edge spikes above about 22 MHz and the Lf self-resonance (52–76 MHz with a PA 2 pF) decide pass or fail. They need measurement with a recorded bandwidth.
- **+5 V at 0.224 A.** This load is DCM (ΔIL/2 = 0.67 A), so the triangle model does not apply: NOT RUN.
- **Pulse skipping.** TPS54560 Eco-mode pulse skipping (§7.3.3, threshold at COMP 600 mV, G; entry current depends on L) is a risk at OSC minimum or standby load. The burst frequency may fall below the filter corner.
- **No OSC-side credit.** No attenuation is credited for the OSC harness or decoupling.

### Source-band budget, worst-case sum against the half-band (feedback at the terminal)

| Rail (half-band) | Setpoint, internal VFB 0.792–0.808 V (±1 %, G) + 0.1 % divider (PA) | Setpoint, precision servo | Load step, 0.5 / 0.5 / 0.2 A (PA) × peak \|Zout\| | Internal VFB | Servo |
|---|---:|---:|---:|---|---|
| +12 V (0.150 V) | 0.144 V | 0.020 V | 0.17 V (0.33 Ω at 21 kHz) | **FAIL** (6 mV left for step and ripple) | **UNRESOLVED** |
| −12 V (0.100 V) | 0.144 V | 0.020 V | 0.24 V (0.47 Ω at 15 kHz) | **FAIL** (setpoint alone) | **UNRESOLVED** |
| +5 V (0.025 V) | 0.059 V | 0.008 V | 0.06 V (0.32 Ω at 23 kHz) | **FAIL** (setpoint alone) | **UNRESOLVED** |

- **Reference.** The TPS54560 reference alone cannot hold the OSC bands on any rail.
- **Servo candidate.** A slow outer DC servo: REF50xxI 0.05 % initial and 3 ppm/°C (G-U, [TI product page](https://www.ti.com/product/REF5050)), a 65 K span (PA), a 0.05 % divider (PA), and a zero-drift op-amp injecting into FB.
- **Servo terms that are UNAV:**
  - divider TCR tracking (10 ppm/K × 65 K = +0.065 %);
  - reference long-term drift and solder shift;
  - op-amp offset;
  - an authority clamp;
  - level-shifted −12 V sensing (the inverter FB is referenced to −12 V).
- **Load step.** Deviation at the terminal is set by the post-filter output impedance (peak 0.32–0.48 Ω, PA, with C1 as an ideal source). Step amplitude and edge rate are PA/UNAV, so the servo case is **UNRESOLVED**, not PASS.
- **OSC load capacitance.** Adding it (120–180 µF on ±12 V, 80–120 µF on +5 V) lowers the peak to 0.23–0.41 Ω. It also moves the resonance to 5–10 kHz, at or below the PA loop crossovers. The filter Q and terminal-sense stability with that capacitance are NOT RUN.

### PTC drop and the rail-plus-return loss: candidates (none adopted)

| Candidate | +12 V (2.0 A) | −12 V (1.9 A) | +5 V (0.4 A) | Note |
|---|---|---|---|---|
| Today: PTC R1max 0.100 Ω (G) outside the loop | 0.200 V, 67 % of the band | 0.190 V, 95 % | 0.040 V, 80 % | **FAIL**; OSC has no loss budget left |
| Feedback after the PTC (terminal sense), split DC/AC feedback | 0 at the terminal | 0 | 0 | Converter output rises by up to 0.2 V; PTC dissipates 0.40 W at 2 A; stability and PTC-trip behavior NOT RUN. Required in every candidate set |
| Lower-R PTC, 0.050 Ω (hypothetical, no part retrieved) | 0.100 V | 0.095 V | 0.020 V | Insufficient alone |
| eFuse, TPS25982: RON ≤ 4.5 mΩ over −40..125 °C TJ (G) | 9 mV | No −12 V high-side eFuse (UNAV) | 2 mV | Its limit tolerance cannot enforce the OSC 2.0–2.1 A window (R7) |

## R3: transient path (b), sink input limit plus hold-up (analysis 2)

The limit's minimum must be ≥ the continuous draw, and its maximum ≤ 3.0 A. The continuous draw sets the allowed max/min ratio:
- **PD screen:** 2.56 A gives 1.172 (±7.9 %); 2.76 A gives 1.087 (±4.2 %).
- **OSC basis:** 2.81 A gives **1.067 (±3.2 %)**.

| Candidate | Guaranteed limit | Ratio | Minimum when the maximum = 3.0 A | Class / source |
|---|---|---:|---:|---|
| TI TPS25982 (2.7–24 V; 30 V abs max) | 1.53–2.43 A (2 A row), 4.36–5.66 A (5 A row), −40..125 °C **TJ** | 1.59 | 1.89 A | G, [SLVSEI3D](https://www.ti.com/lit/ds/symlink/tps25982.pdf) |
| TI LM5069 (9–80 V) | VCL 48.5 / 55 / 61.5 mV **at VIN = 48 V**, plus a 0.5 % shunt (PA). Its power limit also cuts current at VDS 1–4.7 V | 1.28 | 2.34 A | G, [SNVS452G](https://www.ti.com/lit/ds/symlink/lm5069.pdf) |
| ADI LTC4282 (2.9–33 V; 45 V abs max) | 12.1 / 12.5 / 12.9 mV zero-scale at VFB = 1.3 V, over **ambient** (I grade −40..85 °C), plus a 0.5 % shunt (PA). Folds back to 30 % as FB falls 1.3 → 0 V. Intermediate DAC steps are not tabulated | 1.077 | 2.786 A | G, [Rev C](https://www.analog.com/media/en/technical-documentation/data-sheets/ltc4282.pdf) |

Hold-up uses the LTC4282 limit at 2.786 A for 20 ms at constant transient power. These figures hold **only if an FB divider keeps FB ≥ 1.3 V down to the 14 V floor**. They exceed the earlier ~0.9 mF, which assumed a 3.0 A limit and 12 / 12 / 5 V outputs.

| Eta set (start 18.67 / 18.4 V) | 1 V droop | Droop to 14.0 V (PA converter floor) | Recharge margin |
|---|---:|---:|---:|
| base | 8.0 / 8.9 mF | 2.9 / 3.2 mF | 176 / 138 mA |
| −3 pt | 10.2 / 11.2 mF | 3.5 / 3.9 mF | 84 / 44 mA |
| −5 pt | 12.0 / 13.0 mF | 3.9 / 4.3 mF | 15 / **−26 mA (window fails)** |

**Startup sequence (candidate).**
- After the 20 V contract (Q1 stays off at 5 V via `POWER_ONLY_ABOVE_5V`), the limiter charges the hold-up at a controlled dV/dt within the contract current. 4.7 mF to 20 V takes 94 ms at 1 A.
- All three TPS54560 EN pins are held low until the hold-up passes a threshold. EN is 1.1 / 1.2 / 1.3 V (G) with no voltage hysteresis, so a hysteretic comparator or the limiter's power-good is needed. The OSC soft start (10 ms minimum) follows.
- Open items: the fault timer must exceed the charge time plus 20 ms; MOSFET SOA at 1–4.7 V × 2.8 A for 20 ms; PD sink bulk-capacitance and inrush rules (UNAV); transient repetition rate (UNAV; 1 V recharge takes 122–253 ms at −3 pt).

**Verdict (b): not viable as a guaranteed path.**
- Integrated and ±10 %-class limiters exceed the allowed window by a factor of 4–9.
- The best retrieved controller has no window at the OSC-basis 2.81 A.

**Path (a) is not shown to cover the transient (UNPROVEN; safe-side verdict: not passed).**
- The source sets the Fixed Supply PDO Peak Current bits. 00b means no overload.
- The longest window is 10 ms at 50 % duty (110 / 125 / 150 % IOC), with a compensating low phase, so the period average stays at or below IOC. Evidence: **secondary only, not a primary USB PD citation**. The Peak Current table is quoted by a TI engineer on [TI E2E](https://e2e.ti.com/support/interface/f/138/t/874161) ("125% IOC for 10ms @ 50% duty cycle (low current equals 75% IOC for 10ms)") and in an unmerged Linux ABI patch mirror, [kbuild 2023-10](https://ratatoskr.run/oe-kbuild-all/2023/10/8886449). The usb.org specification text and section were not retrieved. On a 3 A contract the transient needs 105–112 % of IOC for 20 ms, while the 2.81 A continuous draw (94 % IOC) already exceeds the 75 % low phase.
- [TI SLVAFR4 §4.3](https://ti.com/document-viewer/lit/html/SLVAFR4/GUID-3B6E20F4-8F77-4204-ACB5-A7FC190D0B37) (G-U) adds that sources "are not required to support continuous overload operation". During overload the source may use vSrcPeak instead of vSrcNew, so the 18.4 / 18.67 V basis is not held.
- If the secondary table is accurate, no profile spans 20 ms. The **B1 transient stays UNRESOLVED**; it closes only via B2 or OSC demand closure, and neither is chosen here.

## TVS clamp against the STUSB4500 28 V absolute maximum (analysis 3)

**Limits.**
- **STUSB4500**, DS12499 Rev 8 Table 20 (G, retrieved directly from [st.com](https://www.st.com/resource/en/datasheet/stusb4500.pdf); the owner bundle still records mirror-only evidence, and promotion is separate):
  - absolute maximum: VDD 28 V; VBUS_EN_SNK, VBUS_VS_DISCH and DISCH 28 V; CC 22 V;
  - VDD operating range 4.1–22 V;
  - idle IDD 110 / 160 / 210 µA at 5 V (the column reading is uncertain, G-U);
  - active-PD IDD is UNAV, and there is no guidance on a VDD series resistor.
- **TVS2200** ([SLVSED5C](https://www.ti.com/lit/ds/symlink/tvs2200.pdf), G):
  - VRWM 22 V;
  - VBR 24.6 / 25.9 / 27.6 V at 1 mA;
  - 8/20 µs clamp ≤ 28.0 V at 40 A / 27 °C and ≤ 28.35 V at 35 A / 125 °C.
- **Margin:** 0.00 V and **−0.35 V**. No *retrieved* passive TVS with VRWM ≥ 21 V meets 28 V.

**Candidate fix: keep TVS2200 for the energy, remove SMAJ16A D5 for B1, and add a per-pin 470 Ω + Nexperia BZX84-C24.** BZX84-C24 limits (G, [Rev 7](https://assets.nexperia.com/documents/data-sheet/BZX84_SER.pdf)):
- VZ 22.8–25.6 V at 5 mA, rdif ≤ 70 Ω;
- SZ ≤ 22.0 mV/K;
- Rth(j-a) ≤ 500 K/W, Tj ≤ 150 °C, Ptot 250 mW;
- IR ≤ 0.05 µA at 16.8 V; IR at 21 V is UNAV.

The model takes VZ max with no credit below 5 mA, plus SZ × (Tj − 25 °C). At 21 V input the margin to the VZ minimum is 1.8 V.

| Pin / network | Case | Node voltage | Margin to 28 V | Note |
|---|---|---:|---:|---|
| VDD (U1.24): 470 Ω + zener + 1 µF | 8/20 µs: τ 470 µs barely lets the zener conduct | < clamp case | — | RC carries it |
| VDD, VBUS_VS_DISCH, DISCH | Sustained overvoltage up to TVS VBR 27.6 V, 50 °C ambient: fixed-current bound 4.3 mA, 110 mW, +55 K | 27.35 V | **≈ 0.65 V** (0.2 V at 70 °C) | Self-consistent: 26.7 V (1.3 V) |
| VBUS_VS_DISCH (U1.18): existing R14 470 Ω + zener, no RC | 28.35 V transient, 25 / 70 °C ambient | 25.65 / 26.59 V | 2.35 / **1.41 V** | 5.7 mA, 147 mW peak |
| DISCH (U1.9): existing R13 470 Ω to VBUS_OUT + zener | As VBUS_VS_DISCH whenever Q1 is on | 25.65 / 26.59 V | 2.35 / 1.41 V | New row; Q1-on paths only |
| VBUS_EN_SNK (U1.16): zener at VBEN, fed through R11 + R12 = 250 kΩ | 28.35 V, 70 °C | ≤ 26.59 V | ≥ 1.4 V | ≤ 11 µA. Leakage at 21 V flows through R11 100 kΩ and sets Q1's VGS while Q1 should be off, so IR(21 V, hot) ≤ about 1 µA is required (0.1 V); UNAV |

**Hot margins** are therefore about 0.6–1.4 V, not the 2.3 V cold figure.

**VDD series R.**
- R15 and R16 are 4.7 kΩ pull-ups to VREG_2V7. They draw about 0.57 mA each, or 1.15 mA with both lines low, and J3.3 exports VREG_2V7.
- VREG_2V7 loads therefore count toward VDD current. With the 210 µA idle maximum, 1.36 mA needs R ≤ 478 Ω for VDD ≥ 4.1 V at a 4.75 V vSafe5V low point (PA). That makes 470 Ω marginal.
- Program the NVM with the series R in place only after it is verified: NOT RUN.

**Still open.**
- ST approval of a VDD series resistor; active IDD.
- **Q1 margins at the clamp.** These apply to the fitted AO3401A: VDS 1.6 V and VGS 0.6 V (G-U). The B1 change set uses AOD4185L (−40 V, ±20 V VGS, G), whose margins are not screened here.
- CC pins (22 V): a CC-to-VBUS short at 20 V is unprotected.
- Not evaluated (UNAV): an input OVP or surge-stopper IC, or a different sink controller.
- **The surge envelope (energy, waveform, cable inductance, repetition) is undefined.** Every margin holds only at the table points.

## Gate register (PWR-INT-03 alignment)

| Row | Gate | Screen result | Status |
|---|---|---|---|
| R2 | Voltage basis for input current | 2.61–2.81 A continuous; 3.10–3.35 A transient | Reproduced |
| R3 | Input-limit tolerance and hold-up startup sequence | No guaranteed window at 2.81 A; 3–13 mF; sequencing candidate only; PD Peak Current coverage of 20 ms UNPROVEN (secondary evidence only; not passed) | **UNRESOLVED** |
| R4a | 1 mVpp ripple at load | 0.02–0.05 mVpp fundamental (CCM) on arithmetic; edges, ESL, DCM and pulse skipping not screened | **NOT RUN** |
| R4b | Source voltage bands | Internal VFB FAIL on all rails; servo with terminal sense UNRESOLVED (load step 0.06–0.24 V at PA steps; UNAV servo terms) | **UNRESOLVED** |
| R4c | 0.2 V rail plus return loss | OSC uses 0.162–0.194 V; PTC outside the loop (0.04–0.20 V) inadmissible; terminal sense is the candidate | **UNRESOLVED** |
| R6 / TVS | TVS2200 (28.0–28.35 V) against the STUSB4500 28 V absolute maximum (VDD, VBUS_VS_DISCH, DISCH, VBUS_EN_SNK); CC 22 V | 0.00 / −0.35 V margin; R + zener candidate about 0.2–1.4 V hot (PA-dependent); envelope undefined; fix proposal in [`input-clamp-fix.md`](input-clamp-fix.md) | **UNRESOLVED** |
| R7 | Input/interface current upper limit 2.1 / 2.0 / 0.5 A, coordinated all-rail shutdown, reverse blocking | Not addressed: PTC trip 5 A; no retrieved limiter holds a 0.1 A window | **UNRESOLVED** (G3 / G4) |
