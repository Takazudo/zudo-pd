# OSC supply options: comparison for a later user decision

**Status: analysis only. Nothing here is adopted, and no option is selected.** OSC demand is OSC-owned and is not lowered here. Planning contract (zudo-osc-hole-field #289), in +12 / −12 / +5 V order:
- continuous 1700 / 1600 / 300 mA;
- 20 ms transient 2000 / 1900 / 400 mA;
- interface maximum 2.1 / 2.0 / 0.5 A.

OSC currently recommends **D3-A** (20 V at ≥ 3.38 A, preferably 20 V / 5 A) with **D5-1** (accept or refuse, no partial supply), pending the user's decision.

Sources: [`supply-capability.md`](supply-capability.md), [`supply-alternatives.md`](supply-alternatives.md), [`product-lineup.md`](product-lineup.md), [`power-limit-60w.md`](power-limit-60w.md), [`product-comparison.md`](product-comparison.md), [`design-gaps-20v.md`](design-gaps-20v.md), [`input-protection-20v.md`](input-protection-20v.md), [`board-b-protection-20v.md`](board-b-protection-20v.md). Nothing is measured.

## 1. Assumptions every row inherits (labelled)

| Assumption | Value | Class | Used for |
|---|---|---|---|
| Converter efficiency sets (+12 buck / −12 inverter / +5 buck) | Base 0.92 / 0.85 / 0.83; −3 pt 0.89 / 0.82 / 0.80; −5 pt 0.87 / 0.80 / 0.75; the same sets at 15 V and 20 V | **PA**: no retained efficiency data for any converter | Every board-input current and every "PASS on input power" |
| Source-band output voltages | 12.3 / 12.2 / 5.1 V | OSC contract | Output power |
| Board-input derate | 20 V × 14.0/15 scaling → 18.67 V; extra cable drop → 18.4 V (3 A); 18.22 V (5 A) | PA | Input current |
| Ancillary rail currents | 14 / 13.9 / 6.6 mA | calc | Power budget |
| Existing-board LDO thermal | Dissipation 4.2 / 3.5 / 2.0 W at the PD targets; required θJA ≤ 20.1 / 24.0 / 43.5 °C/W at 40 °C ambient | calc; installed θJA **NOT RUN** | Option (c) |
| TPS54560 thermal | θJA 42 °C/W on the JEDEC board (G, TYP figure); inverter conduction 0.54–1.16 W → 33–59 °C rise | calc on PA losses; installed θJA **UNAV** | Options (a), (b) |
| Board P eFuse loss (T3) | 3.38² × 53 mΩ = 0.61 W; JEDEC RθJA 31.4 °C/W → about 19 °C | calc on G limits; installed **UNAV** | Options (a), (b) |
| PTC derating | MF-MSMF250 2.50 A hold at 23 °C (G); hold equals load at about 63 °C (1.7 A) and 49 °C (2.0 A) | G / calc | (a), (b) |
| Ambient inside the enclosure | UNAV | — | Every thermal row |

## 2. Options

| | (a) Redesign to the OSC contract, D3-A (C2) | (b) 60 W-class with explicit limits (C1-L, R60) | (c) Existing Board B, light loads only |
|---|---|---|---|
| Input contract | 20 V fixed PDO; preferred **20 V / 5 A** (100 W source + 5 A e-marked cable); 3.5 A variant accepts ≥ 70 W | 20 V / 3 A (≥ 60 W) + ≥ 3 A cable | 15 V / 3 A + ≥ 3 A cable; 20 V unsafe |
| NVM (draft, G-U) | PDO1 5 V; PDO2 20 V / 5 A (LUT `1111b`); `POWER_ONLY_ABOVE_5V` = 1; `REQ_SRC_CURRENT` = 0; no PDO3. Refuse = 5 V contract with Board B off (D5-1) | PDO2 20 V / 3 A | Existing 15 V-only image (no retained image) |
| Continuous 1.7/1.6/0.3 A | PASS on input power (2.61–2.84 A of the contract; calc, PA η) | EDGE / marginal | **FAIL** (already at canonical) |
| 20 ms transient 2.0/1.9/0.4 A | PASS on input power, 3.10–3.38 A vs 5 A (+1.62 A at 5 A, +0.145 A at 3.5 A; calc) | **FAIL** by 0.35–0.56 A | INFEASIBLE |
| Input clamp vs 28 V (L7) | **T3**: TPS26630 OVP eFuse ahead of Board P, protected node ≤ 24.6 V at ≥ 100 µF effective (+3.4 V; calc on G + TYP + PA). Fallback T2 EDGE +0.2…+1.4 V | Same as (a) | SMAJ16A +2.0 V at 25 °C (G); hot unproven (PD-CLAMP-1 open) |
| CC 22 V | +1.0 V single fault; double fault open; TCPP03-M20 G-U only | Same | +6.25 V single fault |
| Input contract enforcement | eFuse I(OL) 4.185–4.815 A inside 3.38…5 A at the 5 A PDO (G limits); none at 3.5 A (charger OCP) | Input trip (INA301 or LTC4282 class) needed; window marginal | Charger OCP only |
| Interface maximum 2.1/2.0/0.5 A | INA301A3 + reference LIMIT: +12 V ≤ 2.070 A, −12 V ≤ 1.967 A (floated, NOT RUN), +5 V PASS; INA301 terms now **G** | Same parts | Not provided (PTC only) |
| Reverse blocking | Input: TPS26630 NFET (G). +12/+5: LM74700-Q1 (G). −12: LTC4354 (G-U). I_REV,max UNAV (OSC) | Same | None |
| All-rail shutdown / latch / discharge | EN_ALL open-drain bus: TPS3700 UVLO and rail windows (G), INA301 latched ALERTs, eFuse FLT; latch cleared by VBUS removal; per-rail discharge switches (parts UNAV; OSC to set level and time) | Same plus trip latch | Not designed |
| Inverting start | TPS54560 inverter startup inrush vs source: open | Must fit under the trip; slow-ramp needs OSC acceptance | LM2596 ≈ 4.5 A ≥ 2 ms at any load (F4) |
| Ripple / source bands | GAP-8 NOT RUN; GAP-3 UNRESOLVED | Same | NOT RUN |
| Reuse | New Board P (eFuse front end) and new Board B; no reuse of the ordered Board B | Same as (a) | Reuses the ordered Board B for a light SKU only; still needs F4 / F8 / F9 changes and a built 15 V Board P |
| Cost (PA guesses, C2 = 1.0) | 1.0× per unit (now plus the eFuse, the protected-node bulk and three limiter / blocking channels, UNAV prices) / 1.0× effort | ≈ 1.05–1.15× / ≈ 1.3–1.6× | ≈ 1.0–1.3× / ≈ 0.5–1.0× |
| Fit for OSC | Only option that carries the recorded demand on paper | Only with an OSC PWR-D5 change; transient still unmet | No |

## 3. Gates still open for (a) (none of them closed by this page)

- **Efficiency.** Unmeasured converter efficiency; every margin uses PA sets.
- **Thermal.** Installed thermal of the eFuse, TPS54560 stages, shunts and blocking FETs.
- **Protection timing and bounds.** eFuse FET-off timing (PA = FLT timing); fast-trip TYP terms; protected-node bulk C_eff; the surge envelope.
- **CC 22 V.** The double fault, and a TCPP03-M20 primary retrieval.
- **Limiter on −12 V.** Floating bias and level shift. Shunt TCR and comparator offset over temperature.
- **Reverse and discharge values.** I_REV,max, plus the discharge level, time and skew, all from OSC.
- **Board-level checks.** Loop stability with in-loop series elements (GAP-4); ripple (GAP-8); source bands (GAP-3); indicator (GAP-9).
- **NVM.** Byte map, retained image and readback (GAP-10). Cable noncompliance at 5 A.
- **Evidence.** Owner bundles for every new part (TPS26630, TVS2200, INA301, LM74700-Q1, TPS3700, LTC4354, TPS54560); stock and price.

## 4. Decisions this feeds (nothing decided here)

- User: D3-A vs (b) vs (c); 5 A vs 3.5 A PDO2 (charger reach vs contract enforcement); PC-1…3; W60-D1…4; PD-CLAMP-1 (15 V) and PD-CLAMP-2 (20 V: T3 recommended, T2 fallback).
- OSC: PWR-D3 / PWR-D5; t_trip, I_REV,max, discharge requirement, skew limit.
