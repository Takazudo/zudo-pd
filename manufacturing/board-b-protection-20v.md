# Board B protection concept at 20 V input: interface limiter, reverse blocking, all-rail shutdown and NVM (draft)

**Scope: dated protection concept feeding later PD20 development.** The original proposal/criteria below retain
its decision-time state. The 20 V / 5 A accept-or-refuse direction was later adopted; use
[decisions](../doc/src/content/docs/decisions/index.mdx) and [PD20 status](pd20-status.md) for present disposition.
This concept body is not a program-ready NVM recipe or measured protection result.

**Status: concept draft only. Nothing here is adopted.** No schematic, PCB, BOM, NVM or part selection changes. Every schematic and PCB stays an unvalidated draft. **Nothing on this page is measured.** The page serves the OSC-recommended direction D3-A (20 V at ≥ 3.38 A, preferably 20 V / 5 A) with D5-1 (accept or refuse, no partial supply). That direction is pending the user's decision.

It drafts how the requirements R5 (GAP-5), R6 (GAP-6) and R7 (GAP-7) in [`design-gaps-20v.md`](design-gaps-20v.md) could be met on the switcher-direct Board B basis (C2 / B1: three TPS54560 stages, LC post-filters, terminal sense; [`supply-alternatives.md`](supply-alternatives.md), [`b1-gates.md`](b1-gates.md)). The Board P front end is in [`input-protection-20v.md`](input-protection-20v.md). The existing S3 Board B (15 V LDO chain) is **not** in scope here.

Evidence classes as in `input-protection-20v.md`. "G (2026-10-31)" means the TI datasheet bytes were retrieved and hashed on that date (§6). Older "G-U" rows are unchanged.

## 1. Block concept

```mermaid
flowchart LR
  USB[USB-C VBUS] --> TVSc[Connector TVS]
  TVSc --> EF[TPS26630 eFuse<br/>OVP 21.5 V min, I(OL) 4.5 A,<br/>reverse block NFET]
  EF --> PN[Protected node<br/>&ge;100 uF eff.]
  PN --> STUSB[STUSB4500<br/>VDD / sense]
  PN --> SW[Load switch<br/>VBUS_EN_SNK]
  SW --> BIN[Board B input]
  BIN --> C12[+12 V TPS54560] --> S12[Shunt + INA301A3] --> RB12[LM74700-Q1 + NMOS] --> O12[+12 V terminal]
  BIN --> C5[+5 V TPS54560] --> S5[Shunt + INA301A3] --> RB5[LM74700-Q1 + NMOS] --> O5[+5 V terminal]
  BIN --> CM12[-12 V TPS54560 inverting] --> SM12[Floated shunt + INA301] --> RBM12[LTC4354 + NMOS] --> OM12[-12 V terminal]
  UV[Input UVLO + rail UV/OV<br/>TPS3700 windows] --> EN[(EN_ALL bus<br/>open-drain, latched)]
  S12 -- ALERT --> EN
  S5 -- ALERT --> EN
  SM12 -- ALERT, level-shifted --> EN
  EF -- FLT / PGOOD --> EN
  EN --> C12
  EN --> C5
  EN --> CM12
  EN --> DIS[Rail discharge x3]
```

Every series element (shunt, blocking FET) sits **inside** the terminal-sense regulation loop (GAP-4 R4.1). Loop stability with them is NOT RUN.

## 2. Interface-maximum limiter (R5: trip ≤ 2.1 / 2.0 / 0.5 A, no trip ≤ 2.0 / 1.9 / 0.4 A)

| Rail | Window max/min | Candidate | Guaranteed terms used | Ratio | Paper result | Open |
|---|---:|---|---|---:|---|---|
| +12 V | 1.050 | 10 mΩ shunt (0.1 %, 50 ppm/K, PA) + **INA301A3** + LIMIT driven from a precision reference through a 0.05 % divider | INA301A3: VOS ±35 µV, drift 0.5 µV/°C, gain error ±0.2 % + 10 ppm/°C, comparator offset 4.5 mV, ILIMIT 79.2–80.8 µA (−40…125 °C), tp ≤ 1 µs, latch mode via RESET, CM 0–36 V (**G 2026-10-31**, SBOS713A). Reference REF50xxI 0.05 %, 3 ppm/K (G-U; TI symlink 404 on 2026-10-31) | 1.035 | Min 2.0 A → max **2.070 A ≤ 2.1 A**: PASS on paper | ILIMIT × divider/buffer source impedance; comparator offset over temperature (the 4.5 mV figure is a 25 °C spec); shunt TCR is PA |
| −12 V | 1.053 | Same chain **floated**: INA301 GND tied to the −12 V rail, VS from a local 5 V bias referenced to −12 V, shunt oriented so that IN+ > IN−, ALERT level-shifted to EN_ALL | As +12 V | 1.035 | Min 1.9 A → max **1.967 A ≤ 2.0 A**: PASS on paper | Bias supply and level shift: no part chosen (UNAV); the arrangement is NOT RUN |
| +5 V | 1.25 | INA301A3, resistor-set LIMIT (0.1 %, 25 ppm/K PA) | As above | 1.059 | Min 0.4 A → max 0.424 A: PASS on paper; set near 0.45 A for margin | Low sense voltage at 0.45 A × 10 mΩ = 4.5 mV, which equals the comparator offset term: use a 50–100 mΩ shunt (PA) and recompute |
| Integrated alternatives | — | TPS25947 eFuse (G 2026-10-31, SLVSFC9C: "±10 % for ILIM > 1 A"); LTC4282 hot-swap (ADI download refused 2026-10-31; earlier G reading) | — | ≥ 1.077 | FAIL on ±12 V | — |

- **Trip action.** Each INA301 runs in **latch mode**. Its open-drain ALERT pulls EN_ALL low. RESET (the latch clear) comes only from a Board B power-on reset, so the trip clears only on VBUS removal, as R6.4 requires.
- **Blanking.** The 20 ms transient (2.0 / 1.9 / 0.4 A) sits inside the no-trip limit, so no deliberate blanking beyond noise filtering is needed. Any filter time constant must be stated against R5.4, whose t_trip is UNAV (OSC to set).
- **Accuracy budget.** The term-by-term budget is the one in `design-gaps-20v.md` GAP-5. Its INA301 inputs are now confirmed against the primary datasheet, so their class moves from G-U to G.

## 3. Reverse blocking (R7)

| Rail / point | Candidate | Limits (class) | Note |
|---|---|---|---|
| USB input, back-feed into the source (R7.3) | TPS26630 external blocking NFET | V(REVTH) −20 / −15 / −9 mV; turn-off 0.17 / 0.37 µs at 1 V overdrive, 0.48 / 3 µs at 10 mV (G 2026-10-31, SLVSE94G) | Covers the input of Board P. Blocking-NFET part choice is UNAV |
| +12 V, +5 V | LM74700-Q1 + NMOS | V(AK REG) 13 / 20 / 29 mV; V(AK REV) −17 / −11 / −2 mV (G 2026-10-31, SNOSD17G) | Reverse current up to \|V(AK REV)\| / RDS(on) flows before turn-off. Off-state leakage is UNAV. The NMOS is UNAV. On +5 V the ANODE ≥ 4 V operating floor needs checking at a collapsing rail |
| −12 V | LTC4354 + NMOS | ΔVSD 10 / 30 / 55 mV; tOFF about 1.2 µs max (G-U; ADI refused 2026-10-31) | Shunt-regulator bias headroom at 12 V not screened; I grade only to 85 °C |
| I_REV,max, ΔV, t_REV | — | UNAV: OSC to set | Needed before any pass/fail |

## 4. Coordinated all-rail shutdown, latch and discharge (R6, D5-1)

**EN_ALL** is one open-drain bus with a pull-up from a Board B bias rail. It drives the three converter EN pins. Any of these pulls it low:
- **Input UVLO.** One TPS3700 window: VIT+ 396 / 400 / 404 mV, ±1 % over temperature; VDD 1.8–18 V, so it needs a bias rail below 18 V; tPHL 18 µs TYP (G 2026-10-31, SBVS187G).
- **Rail UV/OV.** One TPS3700 per rail. On −12 V the window is sensed through a divider summed to a positive reference (NOT RUN).
- **Limiter trips.** The three INA301 ALERTs.
- **Board P eFuse FLT.** This needs FLT carried on a J5 contract pin. Board P/B connector pin use is a separate change, UNAV.
- **STUSB4500 contract loss** is detected by input UVLO: on refuse or downgrade, VBUS falls to 5 V. PDOK is used **only** to qualify turn-on, because POWER_OK2 stays asserted after detach (G-U).

**Latch.** EN_ALL is held low by a latch powered from the Board B input. INA301 latch mode covers the trip sources; UV/OV need a discrete latch (part UNAV). The latch is cleared only when the input falls below vSafe0V-class levels, through a power-on reset. A sustained source OV already behaves this way, because the eFuse OV recovery stays off at 20.5–21 V (see `input-protection-20v.md` §2.1).

**Common start.** All three converters start from EN_ALL rising, with soft start ≥ 10 ms (OSC minimum) and within the OSC load-capacitance ceiling. TPS54560 soft-start and EN thresholds come from SLVSBN0C (retrieved 2026-10-20 in `supply-alternatives.md`, not re-read here).

**Discharge, so that the rails do not decay as a partial supply.**
- When EN_ALL is low, a switch with a resistor on each rail discharges that rail. The −12 V switch must be referenced to −12 V.
- Calc at the OSC bulk of 150 µF per ±12 V rail with 47 Ω (PA): τ = 7.1 ms, 12 V to 1.2 V in about 16 ms, 0.26 A peak, 3.1 W peak, 10.8 mJ per rail. Discharge with 1 kΩ-class loads alone would take seconds and differ per rail.
- **Requirement gaps:** the discharge level, the end time, the skew between rails and the behaviour of OSC-side bulk on +5 V are UNAV and OSC must set them. Switch and resistor parts are UNAV; the resistor pulse rating is needed.

**Timing chain** for R6.5 (detect before regulation loss; tens of µs at full load):
- comparator tPHL 18 µs (TYP);
- INA301 tp ≤ 1 µs (G);
- eFuse OVP ≤ 14 µs (G).
Converter EN-to-off delay is not read (UNAV).

## 5. STUSB4500 NVM settings for 20 V / 5 A accept-or-refuse

Source: DS12499 Rev 8 Tables 6, 8, 9, 16, 17 and §3.3 as read on 2026-10-20 through a summarizing fetch (**G-U**, listed in [`product-lineup.md`](product-lineup.md)). The owner bundle still records these fields as UNSOURCED mirror evidence. On 2026-10-31 neither st.com nor the web.archive mirror could be downloaded, so nothing here is promoted.

| Field | Setting for D3-A / D5-1 | Why | Class |
|---|---|---|---|
| `SNK_PDO_NUMB` | 2 | PDO1 5 V (mandatory) plus one 20 V PDO; no second 20 V class | G-U |
| PDO1 | 5 V; `I_SNK_PDO1` minimal (for example 0.5 A, LUT `0001b`) | On refuse the device ends in a 5 V contract with maximum current I(SNK_PDO1). Board P draws only controller and indicator power then (PA) | G-U (fields); value PA |
| PDO2 voltage | 20.00 V (50 mV steps) | The match is exact on voltage | G-U |
| `I_SNK_PDO2` | LUT `1111b` = **5.00 A** (preferred), or `1100b` = 3.50 A | The match needs I(SNK) ≤ I(SRC). 5 A accepts only 100 W sources with a 5 A e-marked cable; 3.5 A accepts ≥ 70 W. The Board P eFuse 4.5 A setting enforces the input contract only with 5 A | G-U |
| PDO3 | Unused (`SNK_PDO_NUMB` = 2) | Avoids a second 20 V class and the unstated same-voltage priority case | G-U (inferred from §3.3.2) |
| `I_SNK_PDO_FLEX` | Not used (no PDO selects `0000b`) | FLEX current is shared by all PDOs | G-U |
| `POWER_ONLY_ABOVE_5V` | 1 | VBUS_EN_SNK asserts only on a PDO2/PDO3 contract, so a refused source leaves Board B unpowered | G-U |
| `REQ_SRC_CURRENT` | 0 | Request I(SNK_PDO) in the RDO; ST says option 1 must not be used if the sink cannot consume more | G-U |
| `USB_COMM_CAPABLE` / `SNK_UNCONS_POWER` | 0 / 0 | No data role, no external power | G-U |
| `SHIFT_VBUS_HL` / `SHIFT_VBUS_LL` (PDO2) | Defaults +5 % / −15 % kept. Record the effect against the eFuse protected-node offset (≤ 0.18 V) | Monitor window | G-U; interaction NOT RUN |
| `POWER_OK_CFG`, `GPIO_CFG`, VBUS discharge times | Record per image; values not decided | POWER_OK latches after detach; GPIO could serve GAP-9 | G-U (POWER_OK); GPIO options UNAV |

**NVM gaps:**
- NVM byte and bit addresses are UNAV in the repository: UM2650 mirror bytes are recorded but not accessible now, and the STSW-STUSB004 tool is unavailable.
- No retained 40-byte image, no programming jig flow and no readback exist (`fact-stusb-artifact`, NEEDS BENCH).
- Endurance is 1000 cycles at 105 °C (G-U).
- Behaviour on hard-reset recovery has no stated timing.
- The sink cannot detect a source that offers 5 A on a non-e-marked cable. Cable heating in that case is an open gate.

The settings above are a draft image description, not an NVM image.

## 6. Sources retrieved 2026-10-31 (TI public datasheets; bytes held in worker scratch only)

| Document | URL | Bytes | SHA-256 |
|---|---|---:|---|
| INA301 SBOS713A (Sep 2015, rev. Feb 2016) | https://www.ti.com/lit/ds/symlink/ina301.pdf | 889911 | `cef5f46eb09faa8cca94dab31817c1f00eda17bb6f522521464057bccd1636e5` |
| LM74700-Q1 SNOSD17G (Oct 2017, rev. Dec 2020) | https://www.ti.com/lit/ds/symlink/lm74700-q1.pdf | 2657068 | `e16b3a8c0023201fafa5825436f5f2dd6f885b92b84e65602b3f50d741c58b6f` |
| TPS3700 SBVS187G (Feb 2012, rev. Feb 2019) | https://www.ti.com/lit/ds/symlink/tps3700.pdf | 682718 | `3bb7daed20b154bf22ded78e23269c6437eb587400b89bce0f543813df94ebf0` |
| TPS25947 SLVSFC9C (Oct 2020, rev. May 2026) | https://www.ti.com/lit/ds/symlink/tps25947.pdf | 5316794 | `8f96de389903091650d4f462dcfad3210071c3ae7093623a7978f34baf8a65b4` |
| TPS2663x SLVSE94G | see `input-protection-20v.md` §4 | | |

Not retrieved on 2026-10-31: TI REF5025 (symlink 404), ADI LTC4282 / LTC4354 / LTC4367 (connection reset), ST DS12499 / UM2650 / TCPP03-M20. None of the candidates has an owner bundle in this repository.
