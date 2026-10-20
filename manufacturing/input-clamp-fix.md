# Board P input clamp vs the STUSB4500 absolute maximum: fix proposal (screen)

**Status: analysis and documentation only. Nothing here is adopted.** No schematic, PCB, BOM, NVM or part selection changes. Every schematic and PCB stays an unvalidated draft. **Nothing on this page is measured.** The surge envelope (waveform, energy, source and cable inductance, repetition, edge rate) is undefined, so every margin below holds only at the stated datasheet points.

Figures come from [`../scripts/pcb/calculate-input-clamp-fix.py`](../scripts/pcb/calculate-input-clamp-fix.py) (sections 1–4). The zener model is the one in [`../scripts/pcb/calculate-b1-gates.py`](../scripts/pcb/calculate-b1-gates.py): VZ max at 5 mA, no rdif credit below 5 mA, linear rdif above, plus SZ max × (Tj − 25 °C). The model, the 470 Ω series value and the ambient points are project assumptions. External sources were retrieved on 2026-10-20. This page answers GAP-1 and GAP-2 in [`design-gaps-20v.md`](design-gaps-20v.md) and row R6/TVS in [`b1-gates.md`](b1-gates.md).

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
- both: Ptot 250 mW, Rth(j-a) ≤ 500 K/W, Tj ≤ 150 °C.

All margins below depend on the PA model, the 470 Ω value and the ambient point. **They are not guaranteed.**

| Option | Zener | Input case | Node at Ta (or initial Tj) 25 / 70 / 125 °C | Margin to 28 V |
|---|---|---|---|---:|
| 15 V | C20 | SMAJ16A 26.0 V transient | 21.46 / 22.18 / 23.07 V | +6.54 / +5.82 / +4.93 V |
| 15 V | C20 | SMAJ16A hot estimate 28.6 V | 21.73 / 22.45 / 23.34 V | +6.27 / +5.55 / +4.66 V |
| 15 V | C20 | TVS1800 24.7 V transient | 21.32 / 22.05 / 23.00 V | +6.68 / +5.95 / +5.00 V |
| 20 V | C24 | TVS2200 28.35 V transient | 25.65 / 26.59 / 27.80 V | +2.35 / +1.41 / **+0.20 V** |
| 20 V | C24 | Sustained at TVS2200 VBR max 27.6 V (self-heated) | 26.36 / 26.98 / 27.60 V | +1.64 / +1.02 / +0.40 V |

The 20 V rows reproduce b1-gates.md. That page's fixed-current bound for sustained overvoltage gives about 0.65 V at 50 °C and **0.2 V at 70 °C**. Both the 70 °C sustained bound and the 125 °C initial-Tj transient row (25.6 + 0.022 × 100 = 27.8 V) leave about 0.2 V. The 20 V per-pin margin is therefore about **0.2–1.4 V hot, PA-dependent**.

**Zener power.** The 15 V C20 case at the 28.6 V hot estimate draws 14.6 mA, about 317 mW. That exceeds Ptot 250 mW, which is acceptable only as a transient: the PZSM 40 W at 100 µs rating cited in the review was not re-read for this page (G-U). In the other cases the zeners carry at most about 10 mA.

**Operating impact.**
- **Standoff.** C20 VZ min 18.8 V vs 15.75 V gives +3.05 V; C24 VZ min 22.8 V vs 21.0 V gives +1.80 V. IR at the operating maximum is UNAV for both, because it is guaranteed only at 14 V and 16.8 V.
- **VBUS_EN_SNK.** Zener leakage flows through R11 100 kΩ and sets Q1's VGS while Q1 should be off. 1 µA gives 0.10 V (PA limit), so IR at VBUS max, hot, must be ≤ about 1 µA: UNAV.
- **VDD series R.** A series R drops the VDD supply. The idle IDD is ≤ 210 µA (G-U), plus 1.15 mA of I²C pull-up load (b1-gates.md). That needs R ≤ 478 Ω to keep VDD ≥ 4.1 V at a 4.75 V vSafe5V low point (PA), so 470 Ω leaves only 8 Ω. Active-PD IDD and ST guidance on a VDD series resistor are UNAV, and NVM programming with the R in place is NOT RUN.
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

## 4. Recommendation (marked; not adopted) and decision needed

**15 V design.** There are two real choices, each with a cost:
- **Keep SMAJ16A and add the per-pin 470 Ω + BZX84-C20 network (recommended).** It keeps the 400 W, 10/1000 µs rating and gives about 4.7–6.5 V of PA-dependent margin, even at the hot SMAJ16A estimate. Its costs are the VDD series R (470 Ω vs a 478 Ω limit, ST guidance UNAV, NVM programming NOT RUN), unknown zener leakage at 15.75 V, and a transient zener overload (about 317 mW) at the hot estimate.
- **Swap D5 for TVS1800.** It gives a guaranteed 3.3 V margin at 8/20 µs and initial Tj 125 °C, with no VDD resistor. But it cuts the long-pulse rating from 400 W to 120 W with no 10/1000 µs clamp voltage, and it adds the slew-rate limit.

The reason for the recommendation is that the surge envelope is undefined, so keeping the larger long-pulse rating is the safer side.

**20 V options.** TVS2200 plus the per-pin 470 Ω + BZX84-C24 network is the only retrieved path with a positive margin. That margin is about 0.2–1.4 V hot and PA-dependent, not guaranteed. Consider (c) only if a defined surge envelope shows (b) is insufficient.

**CC (GAP-2).** 15 V has +6.25 V and needs no change for a single fault. At 20 V, +1.0 V is thin. The only retrieved hardware fix is a TCPP-class CC protector, which is G-U with the STUSB4500 and has no documented supply on Board P. It stays OPEN.

**Decision needed (owner choice).** This is not a routine change: each 15 V candidate trades either long-pulse rating or VDD supply margin, and every candidate changes Board P parts and layout. The decision is:

- **PD-CLAMP-1 (15 V clamp approach):** **SMAJ16A + per-pin BZX84-C20 (recommended)** / TVS1800 swap / hold. For 20 V options, the same approval would cover TVS2200 + per-pin BZX84-C24.

Approval would **only direct closing the listed open items first**; no part, schematic or PCB change follows until they are closed:
- zener IR at VBUS max, hot;
- ST guidance on a VDD series resistor, and NVM programming with it fitted;
- the surge envelope (waveform, energy, cable inductance, repetition) and a surge test;
- hot-plug edge rate against the TVS1800/TVS2200 slew limit, if either is used;
- CC 22 V at 20 V.
