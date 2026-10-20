# Supply alternatives for the OSC demand

**Status: screening arithmetic and catalog lookups only. This is a draft.** Every schematic and PCB here is unvalidated. Efficiency, thermal, ripple and startup checks are `NOT RUN` for every option. Nothing here is validated, qualified or released.

The figures come from [`../scripts/pcb/calculate-supply-alternatives.py`](../scripts/pcb/calculate-supply-alternatives.py). It reads the OSC probe loads and the ancillary rail currents from [`supply-capability.json`](supply-capability.json), the same inputs [`supply-capability.md`](supply-capability.md) uses. External sources were retrieved on 2026-10-20.

Evidence classes: **G** guaranteed manufacturer limit · **G-U** guaranteed, retained only from a mirror or a secondary summary · **DP** design point · **TYP** typical · **PA** project assumption · **CP(date)** catalog price, non-binding · **UNAV** unavailable.

## Demand and screening points

| OSC brief (owned by the OSC ledger, not verified here) | +12 V | −12 V | +5 V | External power |
|---|---:|---:|---:|---:|
| Planning-normal, canonical (**basis**) | 1.535 A | 1.436 A | 0.224 A | 36.77 W |
| Planning-normal, Stage54 conditional (unadopted; not a basis) | 1.493 A | 1.394 A | 0.224 A | 35.76 W |
| Continuous requirement | 1.7 A | 1.6 A | 0.3 A | 41.10 W |
| 20 ms transient | 2.0 A | 1.9 A | 0.4 A | 48.80 W |

| Board B input point | Value | Class |
|---|---|---|
| 15 V floor / ideal | 14.0 V / 15.00 V | PA (from `supply-capability.json`) |
| 20 V derated (same 14.0/15 = 6.7 % derate) / cable-drop / ideal | 18.67 V / 18.4 V / 20.00 V | PA |
| Contract current | 3 A, or 5 A for B2 | G-U (USB-PD contract) |

Q1, cable and connector losses sit upstream of the board-input point. They are inside the derate and are not added again.

The ancillary rail currents are 0.014 A on +12 V, 0.0139 A on −12 V and 0.0066 A on +5 V (indicator plus divider, from `supply-capability.json`). Each rail also has a series path outside the regulation loop: PTC R1max 0.100 Ω (G) plus 0.02 Ω of filter and copper (PA). **P_anc** is the sum of the ancillary power and that PTC I²R. It is 0.82 W at canonical planning-normal (0.80 W for Stage54), 0.93 W at continuous and 1.16 W at transient.

The efficiency sets are all PA, with no retained data for any converter:

| Set | +12 V buck | −12 V inverter | +5 V buck (light load) |
|---|---:|---:|---:|
| Base | 0.92 | 0.85 | 0.83 |
| −3 pt | 0.89 | 0.82 | 0.80 |
| −5 pt | 0.87 | 0.80 | 0.75 |

The same sets apply at 15 V and 20 V. Lower duty at 20 V moves the buck and inverter losses in opposite directions, and no data exists to separate them.

## Why 15 V / 3 A cannot reach the continuous requirement

Required weighted end-to-end efficiency is `Pout_ext / (Vb × 3 A − P_anc)`:

| Demand | 14.0 V floor | 15.00 V ideal (45 W) | 18.67 V | 18.4 V |
|---|---:|---:|---:|---:|
| Planning-normal, canonical | 89.3 % | 83.2 % | 66.6 % | 67.6 % |
| Planning-normal, Stage54 conditional | 86.8 % | 80.9 % | 64.8 % | 65.7 % |
| Continuous | **100.1 %, infeasible** | **93.3 %**: implausible for three non-synchronous stages, but not physically impossible | 74.6 % | 75.7 % |
| Transient (power basis) | 119.5 % | 111.3 % | 89.0 % | 90.3 % |

The transient is an energy question over 20 ms, covered in the [transient section](#20-ms-transient-energy-question).

**Efficiency note.** The two efficiency pairs differ because they use different load bases. The 88.6 % (15 V) / 95.0 % (14 V) pre-rail floor in `supply-capability.md` uses the Stage54 conditional load. On the canonical load, the same floor gives **91.1 % / 97.6 %**, matching the OSC ledger's 91 % / 98 % (external, from zudo-osc-hole-field PR #289; not verified here). That floor is still an optimistic lower bound: it covers the fitted pre-rails only, with no ancillary current and no converter loss. This table's lower figures assume switcher-direct 12 V and 5 V outputs instead of the 13.44 / 14.145 / 6.519 V pre-rails.

## Options

### A1: keep 15 V / 3 A, switcher-direct rails on Board B

- Three TI **TPS54560DDAR** stages: +12 V buck, +5 V buck, −12 V inverting buck-boost. Each feeds the rail through an LC post-filter, with no LDO.
- All three PTCs become **Bourns MF-MSMF250/16X-2**.
- Board P is unchanged.

### B1 / B2: 20 V / 3 A (60 W) or 20 V / 5 A (100 W)

- Board B gets the same conversion as A1, or the hybrid below.
- Board P changes; see the [Board P change set](#board-p-change-set-b1b2).
- 20 V / 3.25 A also counts as more than 3 A, so it falls in the B2 cable class.

### Hybrid (20 V)

- ±12 V: a switcher to about 12.7 V, then an LDO at 0.7 V headroom (PA). LDO ground current is 2 % (PA).
- +5 V: switcher-direct.
- **Blocker:** this needs LDOs rated for 2 A or more on ±12 V. The LT1963A/LT3015 are characterized only to 1.5 A (G-U). A negative LDO of 2 A or more is **UNAV**: none was identified with retrieved limits.

### C1: separate product

- A 24 V brick, Mean Well GST90A24-P1M (90 W, 90 % efficient, TYP), feeding a dedicated TPS54560 board. No USB-PD.
- An AC-DC triple module was screened and fails: Mean Well RT-65B gives only 0.5 A on −12 V (G-U, distributor listing).

### Board input current (A) against a 3 A contract

| Demand | Eta set | 15 V floor | 15 V ideal | 20 V derated | 20 V cable | Hybrid, 20 V derated |
|---|---|---:|---:|---:|---:|---:|
| Planning-normal, canonical | base / −3 / −5 | **3.05 / 3.16 / 3.24** | 2.85 / 2.95 / 3.02 | 2.29 / 2.37 / 2.43 | 2.32 / 2.40 / 2.46 | 2.46 / 2.55 / 2.61 |
| Stage54 conditional (not a basis) | base / −3 / −5 | 2.96 / 3.07 / 3.15 | 2.77 / 2.86 / 2.94 | 2.22 / 2.30 / 2.36 | 2.26 / 2.34 / 2.39 | 2.39 / 2.48 / 2.54 |
| Continuous | base / −3 / −5 | 3.41 / 3.53 / 3.62 | 3.18 / 3.30 / 3.38 | **2.56 / 2.65 / 2.72** | 2.60 / 2.69 / 2.76 | **2.75 / 2.85 / 2.92** |
| Transient | base / −3 / −5 | 4.06 / 4.20 / 4.31 | 3.79 / 3.92 / 4.02 | **3.04 / 3.15 / 3.23** | 3.09 / 3.20 / 3.28 | 3.27 / 3.38 / 3.47 |

### Maximum continuous output, ratio 1.7 : 1.6 with +5 V held at 0.3 A (PA)

| Contract / point | +12 V | −12 V |
|---|---:|---:|
| 15 V / 3 A floor | 1.40–1.49 A | 1.32–1.40 A |
| 15 V / 3 A ideal | 1.50–1.60 A | 1.41–1.51 A |
| 20 V / 3 A derated, switcher-direct | 1.88–2.00 A | 1.77–1.89 A |
| 20 V / 3 A, hybrid | 1.75–1.86 A | 1.65–1.75 A |
| 20 V / 5 A derated | 3.2–3.4 A by input power; Board B parts limit it to about 2.5 A at 23 °C (PTC hold, G), lower at elevated ambient | same |

### 20 ms transient: energy question

- If the source sees the full transient, B1 draws 3.04–3.23 A at 18.67 V and 3.09–3.28 A at 18.4 V (PA arithmetic), above the 3 A contract. Behavior then depends on the source's overcurrent tolerance, which is **UNAV**.
- B1 meets the transient only in one of two ways:
  - **(a)** the source advertises PD Peak Current overload capability. That is source-dependent and not guaranteed.
  - **(b)** the board adds a sink-side input current limit or eFuse set below 3 A, plus hold-up capacitance.
- Hold-up needed for (b), all PA:
  - base efficiency, 18.67 → 17.67 V: 16 mJ deficit, **≈0.9 mF**;
  - −5 pt: 87 mJ, about 4.8 mF;
  - 18.4 → 17.4 V: 1.8–5.7 mF.
- At 15 V, 14.0 → 13.0 V needs 22–27 mF (0.30–0.37 J), which is impractical.
- Existing input bulk does not count unless an input limit exists: without one, the source still supplies the transient.

## Exact-part limits used

| Part | Fact | Class / source |
|---|---|---|
| TPS54560DDAR | VIN 4.5–60 V, abs max 65 V; high-side current limit 6.3 / 7.5 / 8.8 A (min / typ / max); RDS(on) 92 mΩ typ / **190 mΩ max** (VIN 12 V, BOOT-SW 6 V); θJA 42 °C/W on the standard board; thermal shutdown 176 °C; inverting use described (§8.3, SLVA317) | G (θJA TYP), [TI SLVSBN0C](https://www.ti.com/lit/ds/symlink/tps54560.pdf) |
| TPS54560DDAR | $1.1049 (1+), $0.7487 (100+); 9,536 in stock | CP(2026-10-20), [LCSC C31966](https://www.lcsc.com/product-detail/C31966.html) |
| MF-MSMF250/16X | Hold 2.50 A at 23 °C, 2.24 A at 40 °C, 1.98 A at 50 °C, 1.85 A at 60 °C, 1.29 A at 70 °C, 0.94 A at 85 °C; trip 5 A; 16 V; R1max 0.100 Ω | G, [Bourns MF-MSMF datasheet](https://www.bourns.com/docs/Product-Datasheets/mf-msmf.pdf) |
| MF-MSMF250/16X-2 | $0.61 (1 pc) | CP(2026-10-20), [Digi-Key](https://azcus.digikey.com/en/products/detail/bourns-inc/MF-MSMF250-16X-2/2563289) |
| TVS2200DRVR | 22 V standoff, VBR min 24.6 V, **28.4 V max clamp at 40 A, 8/20 µs** | G, [TI TVS2200](https://www.ti.com/product/TVS2200) |
| TVS2200DRVR | $0.4672 (5+) | CP(2026-10-20), [LCSC C523793](https://www.lcsc.com/product-image/C523793.html) |
| AOD4185L | −40 V; ±20 V VGS; −40 A **at TC = 25 °C**; 15 mΩ max at −10 V, 20 mΩ at −4.5 V | G, [AOS](https://www.aosmd.com/products/mosfets/p-channel-mosfets-8v-60v/aod4185) |
| AOD4185L | $0.4474; 34 in stock | CP(2026-10-20), [LCSC C77993](https://www.lcsc.com/product-detail/C77993.html) |
| STUSB4500 | Sink up to 20 V / 5 A, 3 NVM PDOs; VDD 4.1–22 V operating; VBUS pins 28 V; CC 22 V | G-U, [ST product page](https://www.st.com/en/interfaces-and-transceivers/stusb4500.html) and the repository owner bundle |
| Type-C cables | More than 3 A requires an electronically marked cable | G-U (Type-C Cable and Connector Spec R1.1 as summarized in [TI SSZTBJ8](https://ti.com/lit/pdf/ssztbj8)) |
| LT3015 / LT1963A / LM2596S / AP63201 | $16.57 / $4.6427 / $0.6299 / $0.7228 (1+) | CP(2026-10-20), LCSC [C666306](https://www.lcsc.com/product-detail/C666306.html), [C459702](https://www.lcsc.com/product-detail/C459702.html), [C347423](https://www.lcsc.com/product-detail/C347423.html), [C2071044](https://www.lcsc.com/product-detail/C2071044.html) |
| GST90A24-P1M / RT-65B | $30.80 / $22.20 (1+), plus a 21 % tariff noted by the seller | CP(2026-10-20), Jameco ([GST90A24](https://www.jameco.com/z/GST90A24-P1M-Mean-Well-24-Volt-3-75-Amp-90-Watt-Regulated-Switching-Table-Top-Power-Supply_2223494.html), [RT-65B](https://www.jameco.com/z/RT-65B-MEAN-WELL-Power-Supply-Triple-Output-5V-5A-12V-2-8A-12V-0-5A-65W_323540.html)) |

### Stress screens (PA: 22 µH, 400 kHz, Vf 0.5 V, RDS(on) at the 190 mΩ max, 0.25 W switching loss per stage)

| Stage | 14.0 V input | 18.67 V input | vs limit |
|---|---|---|---|
| Inverter peak switch current (IL + ΔI/2) at 1.6 / 1.9 A | 3.40 / 3.97 A | 3.10 / 3.60 A | 6.3 A min (G) |
| Inverter conduction loss / rise on 42 °C/W | 0.82–1.16 W / 45–59 °C | 0.54–0.77 W / 33–43 °C | NOT RUN, installed θJA UNAV |
| +12 V buck at 1.7 / 2.0 A: conduction loss / rise | 0.47–0.66 W / 30–38 °C | 0.36–0.50 W / 26–31 °C | NOT RUN |
| PTC drop outside the loop at R1max, 1.7 / 2.0 A | 0.17 / 0.20 V | same | Hold equals load at about 63 °C (1.7 A) and 49 °C (2.0 A) ambient |
| J5 two-contact sharing (equal split, unverified) | A1: 1.50 A per contact | B1: about 1.25 A per contact | 3 A per contact (G) |

## Board P change set (B1/B2)

| Item | Change | Gate status |
|---|---|---|
| D5 TVS | SMAJ16A → TVS2200 (22 V standoff) | **OPEN.** The 28.4 V clamp at 40 A exceeds the STUSB4500 VDD and VBUS_VS_DISCH 28 V absolute max, so the margin is negative and the surge envelope is undefined. The CC pins are 22 V absolute max, leaving 2 V at 20 V in a CC-to-VBUS short. Not solved. |
| U1 NVM policy | 20 V / 3 A sink PDO as the only non-5 V PDO, with `POWER_ONLY_ABOVE_5V = 1` | **NOT RUN.** The policy must reject 20 V offers below 3 A (for example a 45 W charger offering 20 V / 2.25 A) and keep VBUS_EN_SNK off. The STUSB4500 matching rules are not verified. Programming, readback and power-cycle gates stay as today. |
| Q1 | AO3401A is marginal at 20 V / 3 A: VDS margin 1.6 V and VGS margin 0.6 V at the clamp (G-U). AOD4185L is required for B2 (TO-252 means a re-layout) | Turn-on slew against inrush and inverter startup at 20 V: **NOT RUN** |
| J1 / JOUT1–J5 | J1 is rated 5 A (G, owner bundle). Header pair is 3 A per contact | Sharing unverified. B2 additionally needs a 5 A e-marked cable |

## Missing gates (all NOT RUN)

- **Noise.** The OSC brief's acceptance gates for any no-LDO option are **≤2 mV** post-factory / static path and **≤1 mV** same-setting load change. No ripple or spur estimate exists for switcher-direct, the hybrid or the post-filter.
- **Noise strategy options.** An active ripple filter or capacitance multiplier costs about 0.5 V of headroom (PA). OSC-local regulation is another route. Both are NOT RUN.
- Source OCP tolerance at the ~3 A operating point (A1 at the floor, and the B1 transient).
- A1 Q1 at 3 A: 0.585 W and 73 °C rise on 125 °C/W (from `supply-capability.md`). NOT RUN.
- Inverter startup inrush against the PD source (rule `inverting-startup-vs-pd-source`), with the new parts.
- Converter efficiency, installed θJA, PTC local ambient, and output-capacitor stability.

## Cost class (per set, qty 1)

| Option | Board B IC delta | Board P delta | Charger tier the user needs |
|---|---|---|---|
| A1 | ≈ −$24.5 (1+ prices): removes LT3015, 2× LT1963A, AP63201, 2× LM2596S ($27.84); adds 3× TPS54560 ($3.31). Passives UNAV | 0 | 45 W PD (any) |
| B1 | Same as A1. Hybrid: removes about $24.5 of ICs and adds ≥2 A LDOs (UNAV) | ≈ +$1 (TVS2200, AOD4185L) | ≥60 W, 20 V-capable PD; 3 A cable |
| B2 | Same as A1 | ≈ +$1, plus copper rework | 100 W PD plus 5 A e-marked cable |
| C1 | New board, similar to A1 | Not used | 24 V / 90 W brick at $30.80 plus tariff |

Charger and cable prices are **UNAV** (not retrieved).

## Verdict (screen only)

| Option | Planning-normal | Continuous | 20 ms transient |
|---|---|---|---|
| Current chain (15 V, LDOs) | FAIL (per `supply-capability.json`: LDO characterization, PTC hold and U4 limits; G / G-U / PA) | FAIL | FAIL |
| A1 (15 V / 3 A, switcher-direct) | **FAIL** at the 14.0 V floor (3.05–3.24 A). Passes only at an ideal 15.00 V at base and −3 pt (2.85–2.95 A); −5 pt gives 3.02 A and fails. Stage54 conditional: 2.96 A base | FAIL | FAIL (22–27 mF hold-up, impractical) |
| B1 (20 V / 3 A, switcher-direct) | Screen PASS (2.29–2.43 A at 18.67 V; up to 2.46 A at 18.4 V) | Screen PASS (2.56–2.72 A at 18.67 V; up to 2.76 A at 18.4 V) | **Not met** unless PD Peak Current is advertised or a sink limit below 3 A plus ≈0.9–5.7 mF hold-up is added |
| Hybrid (20 V / 3 A) | Screen PASS | Screen PASS (2.75–2.92 A at 18.67 V; 2.96 A at 18.4 V); blocked by ≥2 A LDOs (negative one UNAV) | Same gate as B1 (3.27–3.47 A at 18.67 V; 3.52 A at 18.4 V) |
| B2 (20 V / 5 A) | Screen PASS | Screen PASS | Screen PASS (input power, PA); Board B ~2.5 A per rail limit at 23 °C |
| C1 (24 V / 90 W) | Screen PASS | Screen PASS | Screen PASS (input power, PA) |

Screen PASS and FAIL here mean the input-current arithmetic with PA efficiencies only. Every other check is NOT RUN.

The Stage54 OSC reduction (canonical minus a 42 mA maximum-Iq allowance on each analog rail) is unadopted. It is shown only as a labeled conditional row. Even counted, it lowers planning-normal by only about 1 W. It changes no continuous or transient verdict, because the requirement currents are unchanged. For A1 it would turn a planning-normal FAIL at the floor into a base-case edge (2.96 A).

## Separate findings

- On 2026-10-20 LCSC showed AP63201WU-7 (C2071044) **out of stock**. This is a CP observation and affects the current Board B regardless of the decision.
- [`../boards/board-p/README.md`](../boards/board-p/README.md) described the retired SMAJ20A 32.4 V clamp as the open gate although the spec fits the SMAJ16A. This change corrects that paragraph.

## Decision request (recommendation marked; not chosen)

1. **Input contract.** Choose one of:
   - 20 V / 3 A (**recommended**). It meets continuous on the screen. The transient needs either (a) a source advertising PD Peak Current, or (b) a sink-side input limit below 3 A plus about 1–6 mF hold-up.
   - 20 V / 5 A, which meets the transient by input but needs a 100 W charger and a 5 A e-marked cable.
   - Keep 15 V. This only works if OSC lowers continuous to about 1.40–1.49 / 1.32–1.40 / 0.3 A or less. That is below even the canonical planning-normal of 1.535 / 1.436 A, which A1 fails at the 14.0 V floor. The transient would also have to be met by overload at the source.
2. **Board B conversion and noise strategy.** Choose one of:
   - switcher-direct plus LC post-filter;
   - the hybrid with ≥2 A ±12 V LDOs (the negative LDO is UNAV);
   - an active ripple filter / capacitance multiplier, or OSC-local regulation.

   Whichever is chosen must pass the OSC 2 mV / 1 mV gates, which are NOT RUN.
3. **Board P change set.** Approve the TVS2200 + Q1 + 20 V-only NVM policy set, or another set, accepting the open TVS-versus-28 V gate and the NOT RUN policy-matching verification.
