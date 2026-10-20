# Board P input clamp vs the STUSB4500 absolute maximum: fix proposal (screen)

**Status: analysis and documentation only. Nothing here is adopted.** No schematic, PCB, BOM, NVM or part selection changes. Every schematic and PCB stays an unvalidated draft. **Nothing on this page is measured.** The surge envelope (waveform, energy, source and cable inductance, repetition, edge rate) is undefined, so every margin below holds only at the stated datasheet points.

Figures come from [`../scripts/pcb/calculate-input-clamp-fix.py`](../scripts/pcb/calculate-input-clamp-fix.py) (sections 1–5). The zener model is the one in [`../scripts/pcb/calculate-b1-gates.py`](../scripts/pcb/calculate-b1-gates.py): VZ max at 5 mA, no rdif credit below 5 mA, linear rdif above, plus SZ max × (Tj − 25 °C). The model, the 470 Ω series value and the ambient points are project assumptions. External sources were retrieved on 2026-10-20. This page addresses GAP-1 and GAP-2 in [`design-gaps-20v.md`](design-gaps-20v.md) and row R6/TVS in [`b1-gates.md`](b1-gates.md).

Evidence classes: **G** guaranteed in the cited manufacturer table; **G-U** guaranteed, but the reading or its applicability is not independently confirmed; **TYP** typical only; **PA** project assumption; **UNAV** not available. "Hot" TVS cases are at an **initial Tj before the surge**, as the datasheets state them.

## 1. Problem

**STUSB4500 limits** (DS12499 Rev 8 Table 20, **G-U**: the [owner bundle](../.claude/skills/component-stusb4500qtr/) records mirror-only evidence; b1-gates.md read st.com directly, and promotion is a separate step):
- **28 V:** VDD (U1.24), VBUS_EN_SNK (U1.16), VBUS_VS_DISCH (U1.18), DISCH (U1.9) and POWER_OK2 (U1.20, exported on JOUT1.4).
- **22 V:** CC1/CC2 (U1.2 / U1.4), plus CC1DB/CC2DB (U1.1 / U1.5), which are tied to CC through R19/R20 (0 Ω).

On Board P, VDD sits directly on VBUS_IN with D5. VBUS_VS_DISCH reaches VBUS through R14 470 Ω, DISCH through R13 470 Ω (via Q1), and VBUS_EN_SNK through R11 + R12 = 250 kΩ. POWER_OK2 reaches 28 V only through whatever Board B pulls it to (no pull-up on either board today).

| Option | Primary clamp | Clamp (class, waveform, condition) | Margin to 28 V | Verdict |
|---|---|---|---:|---|
| Current 15 V design | D5 SMAJ16A C74561 | 26.0 V at 15.4 A, **10/1000 µs**, 25 °C (G, [owner bundle](../.claude/skills/component-renewal-input-protection/)) | **+2.00 V** | PASS at the datasheet point only |
| Current 15 V design, hot | same | The VBR coefficient 0.1 %/K is **TYP** and not a VC bound. Scaling VC by it gives 27.56 V at initial Tj 85 °C and 28.60 V at initial Tj 125 °C (estimate) | +0.44 / **−0.60 V** (estimate) | **UNPROVEN**: no guaranteed hot clamp exists |
| 20 V candidate (B1/C2) | TVS2200 | 28.0 V at 40 A / 27 °C; 28.35 V at 35 A, initial Tj 125 °C; **8/20 µs** (G, [SLVSED5C](https://www.ti.com/lit/ds/symlink/tvs2200.pdf) Electrical Characteristics) | 0.00 / **−0.35 V** | **FAIL** at the hot point. The 0.00 V figure is itself fragile: §1 Features of the same datasheet states 28.4 V at 40 A |

The current 15 V design passes at 25 °C (G), but its hot clamp is unbounded, so it is UNPROVEN rather than a guaranteed overshoot. The 20 V candidate has a guaranteed hot overshoot.

**CC pins (22 V).** D6/D7 (PESD24VS1UB) are DNP on Board P, and even fitted their VBR is 26.5–27.5 V (G, [owner bundle](../.claude/skills/component-pesd24vs1ub-c85382/)). They are ESD parts and do not hold CC below 22 V. A CC-to-VBUS short (for example, a damaged cable or plug) gives the following, and the same applies to CC1DB/CC2DB:
- 15 V: 15.75 V at VBUS max (PA) → **+6.25 V**;
- 20 V: 21.0 V → **+1.00 V**;
- a short during a surge reaches the primary clamp: −4.00 V (SMAJ16A), −2.70 V (TVS1800) and −6.35 V (TVS2200). That is a double fault, so it is listed but not used as a pass criterion (PA).

**Not covered here.** Q1 margins at the clamp (AO3401A VDS 1.6 V and VGS 0.6 V at 28.35 V, G-U, per [`b1-gates.md`](b1-gates.md)) and Board B input ratings follow whichever clamp is chosen. They are noted, not re-screened.

## 2. Candidate fixes

### (a) Lower-clamp passive TVS

**The waveforms are not like for like.** SMAJ16A is specified at 10/1000 µs. TVS1800 and TVS2200 clamp voltages are specified at 8/20 µs only. For 10/1000 µs they give a peak current rating but no clamp voltage.

| Part | Use | Limits (class) | Margin to 28 V | Effect on 15 V | Effect on 20 V | Surge rating vs the current part |
|---|---|---|---:|---|---|---|
| **TI TVS1800** (flat clamp, WSON 2 × 2 mm) | 15 V only | VRWM 18 V; VBR 19.5 / 21.3 / 23.8 V at 1 mA; VC 23.4 V at 40 A / 27 °C and 24.7 V at 35 A, initial Tj 125 °C, both 8/20 µs; IR ≤ 13 / 330 / 1150 nA at 27 / 85 / 105 °C (G, [SLVSED4A](https://www.ti.com/lit/ds/symlink/tvs1800.pdf)) | **+4.60 / +3.30 V**, 8/20 µs only | Clear: VBR min 19.5 V vs 15.75 V | **Not usable**: VBR min 19.5 V < 21 V, so a 20 V contract makes it conduct (as SMAJ16A does today) | 8/20 µs 40 A / 960 W. **10/1000 µs only 6 A / 120 W, with no clamp voltage**, vs SMAJ16A 15.4 A / 400 W with a 26 V clamp (G). The TVS1800 guarantee does not cover the long pulse SMAJ16A is rated for |
| SMAJ15A C571368 (in repo) | 15 V | VC 24.4 V at 16.4 A, 10/1000 µs, 25 °C; VWM 15 V; VBR 16.7–18.5 V (G, [owner bundle](../.claude/skills/component-smaj15a-c571368/)) | +3.6 V at 25 °C only; hot unbounded (same TYP problem) | **VWM 15 V < 15.75 V**: below the standoff rule | Not usable | 400 W, 10/1000 µs |
| TVS2200 (already the 20 V candidate) | 20 V | above | 0.00 / −0.35 V | — | Fails hot | 8/20 µs 40 A / 1120 W; 10/1000 µs 5 A / 145 W, no clamp voltage (G) |
| Any passive with VRWM ≥ 21 V and hot VC ≤ 28 V | 20 V | None retrieved (as in b1-gates.md) | — | — | **None found** | — |

**Slew-rate limit (TVS1800 and TVS2200, G).** The maximum input slew rate is 2.5 V/µs at 27 °C and 0.7 V/µs hot. SLVSED4A gives the hot point at 105 °C in its table and cites 125 °C in §8.5.3. Faster edges make the device clamp briefly; the datasheet says this is harmless once, but repeated fast edges can overheat it and raise leakage. USB-C hot-plug edge rates on Board P are **not screened**.

### (b) Per-pin series R + zener behind the primary clamp

VDD, VBUS_VS_DISCH and DISCH each get a local zener behind a series resistor (470 Ω PA; R13/R14 already exist). VBUS_EN_SNK gets a zener at VBEN, which is fed through R11 + R12 = 250 kΩ, so the 470 Ω model is conservative there.

Zeners: Nexperia BZX84 series Rev 7 (G, [datasheet](https://assets.nexperia.com/documents/data-sheet/BZX84_SER.pdf)):
- BZX84-C20: VZ 18.8–21.2 V at 5 mA, rdif ≤ 55 Ω, SZ ≤ 18.0 mV/K, IR ≤ 0.05 µA at 14 V;
- BZX84-C24: VZ 22.8–25.6 V, rdif ≤ 70 Ω, SZ ≤ 22.0 mV/K, IR ≤ 0.05 µA at 16.8 V;
- both: Ptot 250 mW (Tamb ≤ 25 °C, FR4 standard footprint), Rth(j-a) ≤ 500 K/W, Tj ≤ 150 °C;
- surge (Table 5 and Table 8 note 2, re-read 2026-10-20, G): PZSM 40 W and IZSM 1.5 A (C20) / 1.25 A (C24), tp 100 µs square wave, Tj 25 °C before the surge. Fig. 1 gives PZSM against pulse duration at 25 °C and 150 °C (maximum values); its curve values are not read here;
- IR: specified **only at 25 °C** and only at the VR above. Fig. 9 gives IR against VR for C7V5–C24 at 25 °C as **typical** values. No IR at elevated temperature exists in the datasheet.

All margins below depend on the PA model, the 470 Ω value and the ambient point. **They are not guaranteed.**

| Option | Zener | Input case | Node at Ta (or initial Tj) 25 / 70 / 125 °C | Margin to 28 V |
|---|---|---|---|---:|
| 15 V | C20 | SMAJ16A 26.0 V transient | 21.46 / 22.18 / 23.07 V | +6.54 / +5.82 / +4.93 V |
| 15 V | C20 | SMAJ16A hot estimate 28.6 V | 21.73 / 22.45 / 23.34 V | +6.27 / +5.55 / +4.66 V |
| 15 V | C20 | TVS1800 24.7 V transient | 21.32 / 22.05 / 23.00 V | +6.68 / +5.95 / +5.00 V |
| 20 V | C24 | TVS2200 28.35 V transient | 25.65 / 26.59 / 27.80 V | +2.35 / +1.41 / **+0.20 V** |
| 20 V | C24 | Sustained at TVS2200 VBR max 27.6 V (self-heated) | 26.36 / 26.98 / 27.60 V | +1.64 / +1.02 / +0.40 V |

The 20 V rows reproduce b1-gates.md. That page's fixed-current bound for sustained overvoltage gives about 0.65 V at 50 °C and **0.2 V at 70 °C**. Both the 70 °C sustained bound and the 125 °C initial-Tj transient row (25.6 + 0.022 × 100 = 27.8 V) leave about 0.2 V. The 20 V per-pin margin is therefore about **0.2–1.4 V hot, PA-dependent**.

**Zener power.** The 15 V C20 case at the 28.6 V hot estimate draws 14.6 mA, about 317 mW. That exceeds Ptot 250 mW, which is acceptable only as a transient. The pulse rating is now re-read (G): PZSM 40 W at 100 µs, Tj 25 °C before the surge. The SMAJ16A pulse is 10/1000 µs, longer than 100 µs, and the Fig. 1 curve value at that duration is not read, so the transient margin is a large ratio (about 0.3–1 W against 40 W at 100 µs) rather than a closed figure. In the other cases the zeners carry at most about 10 mA.

**Smaller VDD series R (script section 5; PA model; nothing selected).** A smaller VDD resistor relaxes the DC limit and still keeps a wide clamp margin. All rows use BZX84-C20, the worst of 25 °C and initial-Tj 125 °C, and the idle load of 1.36 mA (IDD 210 µA G-U plus the VREG_2V7 pull-ups PA):

| VDD series R | VDD at 4.75 V in, idle load | Allowed IDD + load for VDD ≥ 4.1 V | Node at SMAJ16A 26.0 V (G point) | Node at 28.6 V hot estimate (TYP-based) |
|---:|---:|---:|---:|---:|
| 100 Ω | 4.61 V | 6.50 mA | 23.89 V (+4.11 V) | 24.81 V (+3.19 V) |
| 220 Ω | 4.45 V | 2.95 mA | 23.38 V (+4.62 V) | 23.90 V (+4.10 V) |
| 330 Ω | 4.30 V | 1.97 mA | 23.19 V (+4.81 V) | 23.56 V (+4.44 V) |
| 470 Ω | 4.11 V | 1.38 mA | 23.07 V (+4.93 V) | 23.34 V (+4.66 V) |

The node columns are the highest-node case (initial Tj 125 °C), where the zener current is lowest. The worst-case **pulse dissipation** is at 25 °C and low VZ, so it is computed separately (script section 5; PA model, VZ max to VZ min 18.8 V plus rdif above 5 mA):

| VDD series R | Peak current, 26.0 V / 28.6 V in | Zener peak, 26.0 V | Zener peak, 28.6 V estimate | Series-R peak, 26.0–28.6 V |
|---:|---:|---:|---:|---:|
| 100 Ω | 48 / 65 mA | 0.74–1.02 W | 1.17–1.44 W | 0.11–0.42 W |
| 220 Ω | 27 / 37 mA | 0.40–0.54 W | 0.63–0.75 W | 0.07–0.30 W |
| 470 Ω | 14 / 19 mA | 0.21–0.27 W | 0.32–0.38 W | 0.04–0.17 W |

Ignoring rdif entirely bounds the current higher, for example (28.6 − 18.8) V / 220 Ω = 44.5 mA. Every zener figure is far below PZSM 40 W at 100 µs, but that rating is for **Tj 25 °C before the surge only** (G); Fig. 1 has a lower 150 °C curve, and its value at the 10/1000 µs duration is not read, so the zener pulse margin is not closed. The pulse rating of the 0603 series resistors is **not screened (UNAV)**.

At about 220 Ω the DC headroom is about 2.2× the known idle load. Its 28 V margin is +4.62 V at the guaranteed SMAJ16A 26.0 V point and +4.10 V at the TYP-scaled 28.6 V estimate (both PA model). The active-PD IDD is still UNAV, so no value closes the DC limit from sources alone. A local VDD capacitor after the resistor (value PA, not chosen) would also be needed; Board P has C1/C2 only on VBUS_IN. The VDD pin also needs the resistor to be compatible with ST's intended use: DS12499 gives no VDD series-resistor guidance (G-U, below), and the ST evaluation board reading is ambiguous: [UM2398 Rev 1](https://www.st.com/resource/en/user_manual/um2398-getting-started-with-the-stevalisc005v1-evaluation-board-for-stusb4500-stmicroelectronics.pdf) lists a fitted R1 470 Ω (0603, ±5 %) in its BOM, but the extracted schematic text does not tie R1 to any net; the only resistor placed beside the VDD label is R12, marked "NC" with no BOM line. Both readings are recorded; whether ST's reference design has a VDD series R is **unconfirmed**, and even if confirmed it would be reference-design evidence (G-U), not a guarantee.

**Operating impact.**
- **Standoff.** C20 VZ min 18.8 V vs 15.75 V gives +3.05 V; C24 VZ min 22.8 V vs 21.0 V gives +1.80 V. The 15.75 V and 21.0 V points are the project's ±5 % source range (PA, [`power-budget.md`](power-budget.md)); a USB PD primary source for the tolerance was searched for but not retrieved (UNAV). IR at the operating maximum is not guaranteed for either zener: it is specified only at 14 V and 16.8 V at 25 °C, and the 25 °C curve is typical only. **Leakage at 15.75 V, hot, cannot be closed from sources.** For comparison, SMAJ16A IR ≤ 1 µA at VR 16 V (G, TA 25 °C per the table header, [Littelfuse SMAJ datasheet](https://www.littelfuse.com/assetdocs/tvs-diodes-smaj-datasheet?assetguid=13c2a823-03b8-4d1f-9ddc-9b44670aed9d)) already sits on VBUS_IN today.
- **VBUS_EN_SNK.** Zener leakage flows through R11 100 kΩ and sets Q1's VGS while Q1 should be off. 1 µA gives 0.10 V (PA limit), so IR at VBUS max, hot, must be ≤ about 1 µA: UNAV, needs a bench measurement.
- **VDD series R.** A series R drops the VDD supply. The idle IDD is ≤ 210 µA (G-U; DS12499 Table 22 lists idle only, and the column reading is uncertain), plus 1.15 mA of I²C pull-up load (b1-gates.md). That needs R ≤ 478 Ω to keep VDD ≥ 4.1 V at a 4.75 V vSafe5V low point (PA), so 470 Ω leaves only 8 Ω; the sweep above shows lower values. DS12499 Rev 8 (re-read 2026-10-20) gives **no** active-PD IDD, no VDD UVLO threshold beyond the 4.1–22 V operating range, no VDD series-resistor or VDD transient-protection guidance, and says VREG_2V7 is "used only for external decoupling" (G-U). NVM programming with the R in place is NOT RUN.
- **Surge rating.** The primary TVS still takes the energy, so the per-pin network keeps the primary's rating. With SMAJ16A kept, that is the full 400 W at 10/1000 µs.

### (c) Input OVP front end (series switch ahead of the controller)

| Part | Limits (class) | 15 V | 20 V | Notes |
|---|---|---|---|---|
| **ADI LTC4367** + back-to-back N-MOSFETs | VIN −40 to 100 V absolute maximum; operating 2.5–60 V; OV reference 492.5 / 500 / 507.5 mV; tGATE(FAST) 2 µs typ, 6 µs max (CGATE 2.2 nF); IQ 30–90 µA (G, [Rev C](https://www-cce.cldnet.analog.com/media/en/technical-documentation/data-sheets/ltc4367.pdf)) | OV 18 V typ gives a trip of 17.38–18.64 V (1 % divider, PA): +1.63 V over VBUS max, +9.36 V under 28 V | OV 23.5 V typ gives 22.69–24.33 V: +1.69 V over 21 V, +3.67 V under 28 V | Turns everything off on OV, consistent with all-rail-off; also gives reverse blocking. **Exposure during the 2–6 µs turn-off is UNAV** without the surge envelope, so a downstream clamp (a or b) is still needed. Adds two MOSFETs in the 3–5 A path (loss and SOA not screened) |
| ST TCPP01-M12 / TCPP03-M20 | IN_GD/SOURCE (TCPP01) and VBUSc/sense pins (TCPP03): 24 V absolute maximum. CC connector side 24 V; CC device side 4 V (TCPP01) and 7 V (TCPP03, G-U). CC OVP 5.6–6.4 V (TCPP01) or 5.5–6.0 V (TCPP03), 60–100 ns. VBUS OVP reference 1.20–1.34 V (TCPP01) or Vsense 1.10–1.25 V (TCPP03). Supply: TCPP01 VCC 2.7–3.6 V, TCPP03 VCC_VCONN 2.7–5.5 V (G-U) (G, [DS12900 Rev 7](https://www.st.com/resource/en/datasheet/tcpp01-m12.pdf), [DS13618 Rev 5](https://www.st.com/resource/en/datasheet/tcpp03-m20.pdf)) | **VBUS side fails**: 24 V absolute maximum is below SMAJ16A 26 V and TVS1800 24.7 V hot. CC side usable | **VBUS side fails** | **The only retrieved CC fix (GAP-2).** It needs a supply. The only Board P candidate is VREG_2V7, which sits at the 2.7 V minimum and is not documented by ST as a load source. Use with the STUSB4500 is not documented by ST (it lists STM32 UCPD): G-U |

### (d) Different sink controller (reference only)

CYPD3177 (30 V) and AP33772S (34 V) are already noted in design-gaps-20v.md GAP-1. Either is a PD-003-D3 controller decision, not a clamp fix, and is not re-screened.

## 3. Rough cost and effort (PA, unverified; separate measures)

The per-unit ratio is Board P manufacturing cost per unit against the current Board P (1.0). The effort ratio is one-off design and test effort against a simple part swap (1.0). The two ratios are not combined.

| Fix | Board P per unit | Design and test effort | Main drivers |
|---|---|---|---|
| (a) TVS1800 swap for D5 (15 V) | ≈ 1.0× | 1.0–1.2× | New WSON land, layout change and an owner bundle; long-pulse rating review |
| (b) Four zeners and one added VDD R | ≈ 1.0–1.05× | 1.2–1.5× | Placement and routing; VDD-R and NVM verification; leakage evidence |
| (a) + (b) | ≈ 1.05× | 1.3–1.6× | As above |
| (c) LTC4367 + 2 N-MOSFETs (+ (a) or (b) downstream) | ≈ 1.2–1.5× | 1.5–2× | IC, MOSFETs, divider, area; loss and SOA at 3–5 A; surge test |
| TCPP01/03 for CC | ≈ 1.1–1.3× | 1.3–1.6× | IC, supply, layout; STUSB4500 compatibility test |

Prices are UNAV and were not retrieved.

## 4. Status of the decision (nothing selected or adopted)

**Owner direction** ([zudo-pd#218, 2026-10-20](https://github.com/Takazudo/zudo-pd/issues/218#issuecomment-6285879564)): continue evidence gathering and analysis without selecting or adopting (a), (b) or (b'); close the documented uncertainties of (b) first and keep (a) as the comparison. This is not acceptance of the narrow VDD resistance margin, the unknown leakage or any protection shortfall. Parts, schematic and PCB stay unchanged. Physical surge tests, NVM programming and energizing are not authorized.

**15 V and 20 V are separate decisions.**
- **PD-CLAMP-1 (15 V only).** Open. Candidates under study: (b) SMAJ16A kept + per-pin series R + BZX84-C20 (priority for evidence), and (a) TVS1800 swap (comparison). A future 15 V selection does **not** authorize anything for 20 V.
- **PD-CLAMP-2 (20 V, future, not asked now).** TVS2200 + per-pin series R + BZX84-C24 (b') would be its own decision, after the 20 V input contract is decided. Its margin is about 0.2–1.4 V hot, PA-dependent, not guaranteed.

**Comparison as it stands (15 V).**
- (b) keeps the 400 W, 10/1000 µs SMAJ16A rating. Its margin is about 3.2–6.5 V depending on the VDD series R (PA model; table in section 2). Its open items are the leakage at 15.75 V hot, the active-PD IDD and VDD-R compatibility, and NVM programming with the R fitted.
- (a) has a guaranteed 3.3 V margin, but only at 8/20 µs, and its long-pulse rating is 120 W with no 10/1000 µs clamp voltage. It adds the slew-rate limit. It needs no VDD resistor.

**CC (GAP-2).** 15 V has +6.25 V for a single fault. At 20 V, +1.0 V is thin. ST's ESDA25P35-1U1M, which ST's evaluation board appears to place on CC, has VBR 23.3–25.8 V (G, [DS14419 Rev 4](https://www.st.com/resource/en/datasheet/esda25p35-1u1m.pdf)), above the 22 V CC limit, so it is an ESD part and not a 22 V clamp. A TCPP-class protector remains the only retrieved hardware path; it stays OPEN.

## 5. Gap register for (b) and (a)

"Closed" means closed from a primary source at the stated class. Nothing here is measured.

| Gap | Result | Class and source | What still needs a separate hardware-test approval |
|---|---|---|---|
| BZX84 surge rating (PZSM / IZSM) | **Closed at 100 µs**: PZSM 40 W, IZSM 1.5 A (C20) / 1.25 A (C24), Tj 25 °C before surge | G, [BZX84 Rev 7](https://assets.nexperia.com/documents/data-sheet/BZX84_SER.pdf) Tables 5 and 8 | Value at the 10/1000 µs duration and at 150 °C: read Fig. 1, or surge test (V4) |
| Series-R pulse dissipation (0.1–0.4 W peak at 100–220 Ω) | Not screened | UNAV | Resistor pulse rating from the resistor datasheet (source retrieval), then V4 |
| BZX84 IR at 15.75 V (C20) / 21 V (C24), hot | **Not closable from sources.** IR is guaranteed only at 14 V / 16.8 V, 25 °C; Fig. 9 is typical at 25 °C; no hot IR | G (25 °C points), TYP (Fig. 9) | Bench leakage at temperature (V1-15; V1-20 for C24 under PD-CLAMP-2) |
| BZX84 hot clamp | Bounded by SZ max (G) in the PA linear model | G limits, PA model | Surge test (V4) |
| STUSB4500 active-PD IDD | **Not in DS12499 Rev 8**: only idle IDD (column reading uncertain) | G-U, [DS12499](https://www.st.com/resource/en/datasheet/stusb4500.pdf) Table 22 | VDD current in each PD state with R fitted (V2) |
| ST guidance on a VDD series R or VDD transient protection | **None in DS12499 Rev 8.** UM2398 Rev 1: BOM has a fitted R1 470 Ω whose net is not shown; the resistor beside the VDD label is R12 "NC" with no BOM line. Unconfirmed | G-U (absence in DS12499); UM2398 reading unconfirmed | VDD start and PD operation with R fitted (V2) |
| VDD minimum / UVLO | Only the 4.1–22 V operating range; no UVLO threshold | G-U, DS12499 Table 21 | V2 |
| VREG_2V7 load capability | DS12499 says the pin is "used only for external decoupling" (1 µF typ, 0.5–10 µF); no load current is given. Board P already loads it with R15/R16 4.7 kΩ pull-ups (a pre-existing gap, independent of the clamp) | G-U | V2 (VREG_2V7 voltage under pull-up load) |
| SMAJ16A hot clamp | **Not closable.** VBR coefficient 0.1 %/K typical only; power derating against initial Tj in Fig. 3 (curve only); IR ≤ 1 µA at 16 V with no temperature stated | G (25 °C VC), TYP (coefficient), [Littelfuse SMAJ datasheet](https://www.littelfuse.com/assetdocs/tvs-diodes-smaj-datasheet?assetguid=13c2a823-03b8-4d1f-9ddc-9b44670aed9d) | Surge test at temperature (V4) |
| SMAJ16A 8/20 µs rating | **Not published**; 400 W at 10/1000 µs only | G (absence) | V4 if an 8/20 µs envelope is chosen |
| VBUS maximum at 15 V (standoff criterion) | 15.75 V is the project's ±5 % range; a USB PD primary source was searched for and not retrieved | PA | — (source retrieval, not a test) |
| VDD series R limit (478 Ω at 470 Ω) | **Relaxed on paper**: 220 Ω allows 2.95 mA; margin +4.62 V at the 26.0 V G point, +4.10 V at the 28.6 V TYP-scaled estimate (section 2) | PA model; TYP for the hot point | V2 |
| Surge envelope (waveform, energy, cable, repetition) | Undefined | — | Owner-defined envelope, then V4 |
| TVS1800 slew limit (comparison (a) only) | 2.5 V/µs at 27 °C, 0.7 V/µs hot | G, [SLVSED4A](https://www.ti.com/lit/ds/symlink/tvs1800.pdf) | Hot-plug edge capture (V5) |
| CC 22 V at 20 V | OPEN; no part found | — | CC short test (V6-20), PD-CLAMP-2 scope |

## 6. Proposed verification plan (not executed; each step needs hardware-test approval)

No step below is authorized. Each needs a built prototype and an explicit owner approval for that test. Energizing, NVM programming and surge tests are outward hardware actions.

| ID | Test | Method (proposal) | Pass criterion (candidate) | Approval |
|---|---|---|---|---|
| V1-15 | Zener leakage at temperature, 15 V (PD-CLAMP-1) | Loose BZX84-C20 samples on a source-measure unit at VR = 15.75 V, 25 / 70 / 125 °C | IR ≤ 1 µA at the hottest board point (keeps Q1 VGS ≤ 0.1 V through R11) | needs hardware-test approval |
| V1-20 | Zener leakage at temperature, 20 V (PD-CLAMP-2 only) | As V1-15 with BZX84-C24 at VR = 21 V | As V1-15 | needs its own hardware-test approval; not covered by any 15 V approval |
| V2 | VDD start and operation with the series R fitted | Board P with the candidate R (220 Ω and 470 Ω) and a local VDD capacitor; 4.75 V vSafe5V current-limited source; log VDD, VREG_2V7 and IDD through attach, contract and detach | VDD ≥ 4.1 V and VREG_2V7 in range in every state; contract completes | needs hardware-test approval (energizing) |
| V3 | NVM programming with the R fitted | Program and read back the 15 V-only image through the jig with the R in place | Readback matches; no brownout reset during writes | needs hardware-test approval (NVM programming) |
| V4 | Surge at the defined envelope, 15 V network (PD-CLAMP-1) | Coupling network and generator per the owner-defined envelope; 25 °C and hot; probe VDD, VBUS_VS_DISCH, DISCH and VBEN at the pins; a 20 V network would be a separate V4-20 under PD-CLAMP-2 | Every pin ≤ 28 V with the agreed guard; no parameter shift after the series | needs hardware-test approval (surge) and a defined envelope |
| V5 | Hot-plug edge capture | Capture VBUS_IN rise at attach and at contract change across the charger and cable matrix | Edge rate below the TVS slew limit if (a) is used; record for (b) | needs hardware-test approval (energizing) |
| V6-15 | CC short, 15 V (PD-CLAMP-1) | CC-to-VBUS short at 15 V with a current-limited source | CC and CCxDB ≤ 22 V; device survives | needs hardware-test approval |
| V6-20 | CC short, 20 V (PD-CLAMP-2 only) | As V6-15 at 20 V | As V6-15 | needs its own hardware-test approval; not covered by any 15 V approval |
