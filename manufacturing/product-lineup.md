# Product lineup screen (PD-003)

**Status: screening and exploration only. Nothing here is adopted.** Every schematic and PCB is an unvalidated draft. Efficiency, thermal, ripple, startup and surge checks are `NOT RUN` for every option. Nothing here is validated, qualified or released, and no option is chosen. Recommendations are marked as such; they are not decisions.

The figures come from [`../scripts/pcb/calculate-product-lineup.py`](../scripts/pcb/calculate-product-lineup.py) (sections 1–10 of its output). It imports the efficiency sets, ancillary currents, PTC terms and input-power method of [`../scripts/pcb/calculate-supply-alternatives.py`](../scripts/pcb/calculate-supply-alternatives.py) unchanged. Its hold-up integration matches the B1 gate screen. See [`supply-alternatives.md`](supply-alternatives.md), [`supply-capability.md`](supply-capability.md), [`b1-gates.md`](b1-gates.md) (rows R3, R4a, R4b, R7) and [`design-gaps-20v.md`](design-gaps-20v.md). External sources were retrieved on 2026-10-20.

Evidence classes: **G** guaranteed manufacturer limit · **G-U** guaranteed or manufacturer-stated, but read only through a summarizing fetch or a secondary summary, with no bytes retained · **S** secondary source only (forum quote, code comment, mirror of a third party); never used as a pass · **DP** design point · **TYP** typical · **PA** project assumption · **CP(date, qty, currency)** catalog price, non-binding · **UNAV** unavailable.

Number tags: **calculated** means screen arithmetic from the script (PA efficiencies); **retrieved** means read from a cited source; **unverified** means not checked by simulation or bench. **Nothing here is measured**, so every calculated number is also unverified.

This page answers two separate questions:

- **(a)** What minimum supply conditions does the **current full OSC** need? Demand is fixed; the supply cannot throttle it. Full OSC is impossible on a 45 W-class contract (15 V / 3 A, 20 V / 2.25 A: continuous FAIL) and is not passed on 20 V / 3 A or 3.25 A (transient not covered or EDGE; source overload UNPROVEN). That is a statement about OSC only.
- **(b)** Which **general-purpose PD supply product lineup** makes sense? Such a product may power lighter loads from low-power adapters and offer more capability on higher contracts. Being unfit for full OSC on a low contract does **not** reject an option for the product as a whole.

---

# Part (a): minimum supply conditions for full OSC

## Fixed demand-side conditions

The OSC ledger ([zudo-osc-hole-field PR #289](https://github.com/Takazudo/zudo-osc-hole-field/pull/289), head `6491ff72`) and the OSC integration owner (#288) own demand. Nothing here relaxes it.

| Condition | Value |
|---|---|
| Canonical planning (comparison basis) | 1.535 / 1.436 / 0.224 A at +12 / −12 / +5 V |
| Continuous requirement | 1.7 / 1.6 / 0.3 A, all rails at once |
| 20 ms transient requirement | 2.0 / 1.9 / 0.4 A |
| Startup envelope; interface maximum | 1.759 / 1.658 / 0.287 A; 2.1 / 2.0 / 0.5 A |
| Rail policy | All rails on or all rails off. **The supply cannot throttle OSC**: no per-rail current reduction while OSC runs |
| Governing output voltages | OSC source-band upper limits, 12.3 / 12.2 / 5.1 V (ledger review R2) |
| OSC degraded mode | About 1.3–4 oscillators switched off, plus new switchable domains. This is OSC decision **PWR-D5** and exists only as an OSC-side option. **It is never a supply feature** |

Consequence: a supply that limits current under overload and lets the rails sag is a brownout and **fails**. The only admissible adaptive behavior toward OSC is **accept or refuse**: all rails come up only on a contract that covers the full requirement, and otherwise all rails stay off with an indication.

## What the source offers

PDO sets follow the USB PD power rules as summarized by [Renesas](https://www.renesas.com/en/support/engineer-school/usb-power-delivery-02) (**S**: a vendor tutorial, not the USB PD specification). The PDP-to-current rule below is therefore a planning basis, not a primary pass basis; it closes only with the primary USB PD power-rules text (UNAV, same retrieval failure as below):

- 27–45 W PDP: 5 V and 9 V at 3 A; 15 V scales with power.
- 45–60 W: 5, 9 and 15 V at 3 A; 20 V = PDP / 20.
- Above 3 A: the source must identify a 5 A e-marked cable, which it discovers over SOP′. Otherwise it caps at 3 A and 60 W.

So the 20 V offer is 2.25 A from a 45 W charger, 3 A from 60 W, 3.25 A from 65 W, 3.5 A from 70 W, 4 A from 80 W, 4.5 A from 90 W and 5 A from 100 W. Every offer above 3 A needs a 5 A e-marked cable.

The sink cannot detect a noncompliant source or cable that offers 5 A anyway. Cable and connector heating in that case is an **open gate**.

PPS (up to 21 V, G-U) adds no current. Neither the STUSB4500 product page ([ST](https://www.st.com/en/interfaces-and-transceivers/stusb4500.html), G-U) nor DS12499 Rev 8 mentions PPS or APDO (G-U, word search through a summarizing fetch).

**Source Peak Current (overload) and the 20 ms transient: UNPROVEN.** The only retrieved text on Fixed Supply PDO Peak Current is secondary (**S**): a TI engineer's quote on [TI E2E](https://e2e.ti.com/support/interface/f/138/t/874161) ("125% IOC for 10ms @ 50% duty cycle (low current equals 75% IOC for 10ms)") and an unmerged Linux ABI patch mirror, [kbuild 2023-10](https://ratatoskr.run/oe-kbuild-all/2023/10/8886449). The primary text was not obtained: the usb.org [USB Power Delivery](https://www.usb.org/document-library/usb-power-delivery) page lists "USB Power Delivery Specification Revision 3.2, Version 1.2" as a 43.3 MB zip, but the download was refused in this environment (proxy 403; the fetch tool cannot read the zip). The spec revision, section and table for the Peak Current field are therefore **UNAV**. On this evidence, source overload coverage of a 20 ms transient is **not established**. It is not shown to be impossible either. If the secondary table is accurate, no profile covers it: the longest overload window is 10 ms, and the 2.81 A continuous draw (94 % of IOC on 3 A) already exceeds the 75 % compensating low phase (B1 R3). The safe-side verdict stays **not passed**: a 3 A contract does not cover the transient until the primary table is quoted and shows a qualifying profile, and even then Peak Current is source-advertised, not guaranteed for every charger.

## Per-PDO capability (Board B switcher-direct, TPS54560 ×3, PA efficiencies)

Board-input current range over the base / −3 pt / −5 pt efficiency sets, at the source-band output voltages (script section 1). **PASS** means all efficiency sets fit the contract current; **EDGE** means only the base set does.

| Contract (cable) | Board input V | Planning | Continuous | 20 ms transient | Startup envelope | All maxima at once? |
|---|---|---|---|---|---|---|
| 15 V / 3 A (3 A) | 14.00 | 3.11–3.30 **FAIL** | 3.48–3.70 **FAIL** | 4.14–4.40 **FAIL** | 3.59–3.82 **FAIL** | No |
| 20 V / 2.25 A, a 45 W charger (3 A) | 18.47–18.67 | 2.33–2.50 **FAIL** | 2.61–2.80 **FAIL** | 3.10–3.33 **FAIL** | 2.70–2.89 **FAIL** | No |
| 20 V / 3 A, 60 W, or 65/100 W on a 3 A cable (3 A) | 18.40–18.67 | 2.33–2.51 PASS | 2.61–2.81 PASS | 3.10–3.35 **FAIL** on contract current; source overload UNPROVEN | 2.70–2.90 PASS | Continuous yes; transient not passed |
| 20 V / 3.25 A, 65 W (5 A e-marked) | 18.38–18.67 | PASS | PASS | 3.10–3.35 **EDGE** | PASS | Transient only at base efficiency; an LTC4282 window exists (±7.2 %, 3.018 A minimum) with 1.6–3.2 mF hold-up to 14 V |
| 20 V / 3.5 A, 70 W (5 A e-marked) | 18.35–18.67 | 2.33–2.52 PASS | 2.61–2.82 PASS | 3.10–3.35 PASS | 2.70–2.91 PASS | Yes, on input power only; 0.145 A transient margin |
| 20 V / 4 A, 80 W (5 A e-marked) | 18.31–18.67 | 2.33–2.52 PASS | 2.61–2.83 PASS | 3.10–3.36 PASS | 2.70–2.92 PASS | Yes, on input power only |
| 20 V / 4.5 A, 90 W (5 A e-marked) | 18.26–18.67 | 2.33–2.53 PASS | 2.61–2.83 PASS | 3.10–3.37 PASS | 2.70–2.93 PASS | Yes, on input power only |
| 20 V / 5 A, 100 W (5 A e-marked) | 18.22–18.67 | 2.33–2.54 PASS | 2.61–2.84 PASS | 3.10–3.38 PASS | 2.70–2.93 PASS | **Yes, on input power only** |

The transient passes on input power for any 20 V contract of at least **3.38 A** with a 5 A e-marked cable. That figure is conservative: it is the worst transient draw at the 5 A cable-drop point. Solving with the cable drop scaled to the contract itself gives 3.351 A, or about 67 W PDP (script section 7).

| Contract | Largest continuous-shaped +12 / −12 V, with +5 V at 0.3 A | J5 per contact (equal split, unverified) |
|---|---|---|
| 15 V / 3 A | 1.37–1.46 / 1.29–1.37 A | 1.85 A of 3 A (G) |
| 20 V / 2.25 A | 1.35–1.44 / 1.27–1.36 A | 1.40 A |
| 20 V / 3 A | 1.82–1.93 / 1.71–1.82 A | 1.41 A |
| 20 V / 3.25 A | 1.97–2.10 / 1.86–1.97 A | 1.41 A |
| 20 V / 5 A | +12 V 3.02–3.21 / −12 V 2.84–3.02 A by input; **Board B caps it**: MF-MSMF250 hold 2.50 A at 23 °C (G) | 1.42 A |

How these figures relate to `supply-alternatives.md`:

- **Continuous at 20 V / 3 A.** 2.61–2.81 A here versus 2.56–2.76 A there is the source-band output power, 41.96 / 41.10 W = ×1.021.
- **Cable-drop scaling.** It uses the contract current, which is pessimistic at 5 A and optimistic at 2.25 A. No verdict changes.
- **The 100 W maximum.** 3.0–3.2 A here versus 3.2–3.4 A there comes from the same two causes.

**Loss and thermal.**

- The 6.8–9.8 W Board B loss at continuous is PA. Its independence from input voltage is an artifact of the fixed-efficiency model.
- Installed θJA is UNAV, so thermal is `NOT RUN`.
- The MF-MSMF250 hold current equals the continuous load at about 63 °C (+12 V) and 64 °C (−12 V) local ambient (G curve). Local ambient includes the PTC's self-heat, which is UNAV.

## Sink PDO2 current choice for the OSC contract

The STUSB4500 NVM can encode every candidate current (see the [STUSB4500 facts](#stusb4500-facts-from-st-documents-g-u) below). The choice sets which chargers are accepted, not the demand. **100 W is not required**; it is one margin choice among four. Script section 7:

| Sink PDO2 (20 V) | NVM encoding (DS12499 Table 17, G-U, retrieved) | Minimum charger PDP, plus 5 A e-marked cable (S rule) | Common chargers accepted | Worst transient draw (calculated) | Transient screen margin (calculated) | Continuous margin (calculated) |
|---|---|---:|---|---:|---:|---:|
| 3.40 A (shown only for reference) | `I_SNK_PDO_FLEX` = 340 (10 mA steps; one value shared by all PDOs) | 68 W | 70, 80, 90, 100 W | 3.35 A | +0.047 A | +0.58 A |
| **3.50 A** | LUT `1100b` | **70 W** | 70, 80, 90, 100 W | 3.35 A | +0.145 A | +0.68 A |
| **4.00 A** | LUT `1101b` | **80 W** | 80, 90, 100 W | 3.36 A | +0.638 A | +1.17 A |
| **4.50 A** | LUT `1110b` | **90 W** | 90, 100 W | 3.37 A | +1.129 A | +1.67 A |
| **5.00 A** | LUT `1111b` | **100 W** | 100 W only | 3.38 A | +1.621 A | +2.16 A |

Every row refuses 45 W, 60 W and 65 W chargers and any charger behind a 3 A cable. The margins are input-power arithmetic on PA efficiencies, with no converter, PTC or thermal check. Any efficiency shortfall beyond the −5 pt set (UNAV) eats directly into these margins. The 3.40 A FLEX row (0.047 A) is shown only for reference and is not a candidate; the 3.5 A margin of 0.145 A is also thin. The trade is charger reach against margin; the owner chooses (decision D1 below).

## The transient on a 20 V / 3 A contract

The sink-side limit must sit between the 2.81 A worst continuous draw and 3 A: a ±3.2 % window. **The best retrieved limiter is LTC4282, at ±3.7 % effective. It leaves no window at 2.81 A. Hold-up would be 2.9–4.3 mF to a 14 V floor or 8.0–13.0 mF for 1 V droop, and at −5 pt the limiter cannot recharge it** (B1 gate screen R3). Integrated ±10 %-class eFuses are far wider. Source overload coverage is UNPROVEN (above). At 20 V / 3.5 A and above, the transient fits the contract, so no limiter or hold-up is needed.

## Minimum conditions for full OSC (summary)

| Item | Minimum | Basis |
|---|---|---|
| Contract | 20 V fixed PDO at ≥ 3.38 A (conservative); in NVM terms PDO2 = 20 V / 3.5 A or higher | Calculated, unverified: script sections 1 and 7; PA efficiencies |
| Charger | ≥ 70 W PDP offering 20 V / ≥ 3.5 A (or the PDP matching the chosen PDO2 current) | USB PD power rules, S (Renesas summary) |
| Cable | 5 A e-marked | G-U |
| Sink policy | Accept/refuse: `POWER_ONLY_ABOVE_5V = 1`; no match gives a 5 V mismatch contract with the path off | DS12499 §3.3.2, Table 16, G-U |
| 20 V / 3 A or lower | Not passed: continuous fits at 20 V / 3 A but the transient is not covered (overload UNPROVEN; no limiter window) | B1 R3 |
| Open gates that still apply | Source bands (servo), ripple, interface maximum and reverse blocking, coordinated all-rail shutdown, TVS vs 28 V and CC 22 V, PTC ambient about 63 °C, NVM production readback, cable noncompliance | [`design-gaps-20v.md`](design-gaps-20v.md) GAP-1 to GAP-10 |

---

# STUSB4500 facts from ST documents (G-U)

Retrieved from st.com on 2026-10-20 through a summarizing fetch with no bytes retained, so all rows are **G-U**. Direct downloads from st.com were refused in this environment (proxy 403). The [owner bundle](../.claude/skills/component-stusb4500qtr/) still records these facts as UNSOURCED mirror evidence; promoting them is separate work.

- [DS12499 Rev 8](https://www.st.com/resource/en/datasheet/stusb4500.pdf) (November 2022)
- [UM2650 Rev 3](https://www.st.com/resource/en/user_manual/um2650-the-stusb4500-software-programing-guide-stmicroelectronics.pdf) (January 2023)
- [STSW-STUSB002 data brief DB3647 Rev 1](https://www.st.com.cn/resource/en/data_brief/stsw-stusb002.pdf) (June 2018): the NVM GUI. It states only that the "NVM area" can be "read, configured and written" and names no parameters. No separate ST application note on NVM fields was found.

| Topic | ST text (quoted or closely paraphrased) | Locator |
|---|---|---|
| Current encoding | `I_SNK_PDO1/2/3` are 4-bit fields. `0000b` selects the flexible value; `0001b`–`1111b` select a LUT: 0.50, 0.75, 1.00, 1.25, 1.50, 1.75, 2.00, 2.25, 2.50, 2.75, 3.00, **3.50, 4.00, 4.50, 5.00 A** | DS12499 Table 16, Table 17 |
| Flexible current | "10 mA ≤ 0.01*I_SNK_PDO_FLEX[9:0] ≤ 5A by steps of 10 mA"; "Flexible current value common to all PDOs"; default 2.0 A | Table 16, §3.3.1 |
| PDO voltages | PDO2/PDO3 "5 V ≤ … ≤ 20 V by steps of 50 mV"; defaults 15 V and 20 V; `SNK_PDO_NUMB` 1–3 PDOs | Table 16 |
| Priority | PDO1 low (mandatory), PDO2 medium, PDO3 high | Table 8 |
| Matching rule | "The comparison starts from the SNK_PDO with the highest priority … The voltage is compared first, the current afterwards." Match when V(SNK_PDOi) = V(SRC_PDOj) **and** I(SNK_PDOi) ≤ I(SRC_PDOj). "The comparison loop stops at the first match." | §3.3.2 |
| Mismatch | "if no match happens, the USB PD negotiation ends with an explicit USB PD contract at 5 V"; the RDO is sent with capability mismatch set, operating current from the source's 5 V PDO and maximum current I(SNK_PDO1) | §3.3.2 |
| Voltage equality | Exact: in Table 9 case 4, a 15.1 V sink PDO does not match a 15 V source PDO, and the lower-priority 15 V / 1 A PDO then matches | Table 9 |
| `REQ_SRC_CURRENT` | `0b`: "Request I(SNK_PDO) as operating current in RDO message" (default). `1b`: request I(SRC_PDO). §3.3.3: "In case the sink is not able to consume more power than requested, this option must not be used"; it also causes the source to allocate a power reserve | Table 16, §3.3.3, Table 9 |
| `POWER_ONLY_ABOVE_5V` | `1b`: "VBUS_EN_SNK pin enabled only when source attached and VBUS voltage negotiated to PDO2 or PDO3 voltage" | Table 6, §2.2.10, Table 16 |
| `USB_COMM_CAPABLE` | `0b` "Sink does not support data communication" (default) | Table 16 |
| `SNK_UNCONS_POWER` | `0b` "No external source of power" (default); `1b` external power sufficient | Table 16 |
| VBUS monitor | `SHIFT_VBUS_HL/LL` 1–15 % in 1 % steps; defaults +10 / −15 % (PDO1) and +5 / −15 % (PDO2, PDO3) | Table 16 |
| POWER_OK flags | The flag of the negotiated PDO asserts. "At detachment the POWER_OK pins remain enabled (if already asserted)" while VBUS_EN_SNK goes Hi-Z; they reinitialize "after new attachment or after a reset" (stated for POWER_OK configuration 2, the default; the POWER_OK_CFG setting must be recorded per image) | §2.2.8 |
| Hard reset | If, after a hard reset, PD communication is broken, error recovery "de-asserts the VBUS power path by disabling the VBUS_EN_SNK, POWER_OK2 and POWER_OK3 pins". **Timing is not stated** | §3.7 |
| NVM endurance | 1000 write cycles at TA = 105 °C (the owner-bundle endurance fact remains open; it is not promoted here) | Table 22 |
| Runtime PDOs | PDO registers 0x85–0x90 are writable; fixed sink PDO current is "in 10 mA units" (B9…0), voltage in 50 mV units | UM2650 §1.4, Table 2 |
| RDO status | 0x91–0x94 carry the RDO: object position, capability-mismatch bit, operating and maximum current in 10 mA units | UM2650 §1.8, Table 3 |

What this settles, and what it does not:

- **3.5 / 4 / 4.5 / 5 A sink currents are encodable** through the LUT (G-U). The earlier "UNAV in the owner bundle" statement is superseded at G-U level.
- **The source must offer at least the sink current at exactly the sink voltage**, otherwise the PDO is skipped. With no match the path stays off under `POWER_ONLY_ABOVE_5V = 1`. Accept/refuse without an MCU is supported on paper; programmed behavior is `NOT RUN` until bench readback.
- **Two PDOs at the same 20 V with different currents (A2)** are not addressed by ST. The stated rule implies that PDO3 (20 V / 5 A) is tried first and PDO2 (20 V / 3 A) matches if PDO3 fails. This is an inference from §3.3.2, not a stated case, so it stays a bench item.
- **The high-voltage path drops at detach and on hard-reset error recovery**, but the timing is unstated. POWER_OK flags latch after detach, so they cannot by themselves tell a load that power is valid.
- Errata and a Peak Current request field in the RDO were not looked for (UNAV).

---

# Part (b): PD product lineup

## Options

| Option | Configuration | Lighter loads on low adapters | Full OSC | Firmware |
|---|---|---|---|---|
| **A1** adaptive general-purpose | STUSB4500 (or AP33772S) + MCU; per-rail sense; all-rail trip; class signal on the header | Yes: per-class rating | Only if OSC is gated to a minimum class whose trip window fits (about 4.5 % at 70 W, UNPROVEN; wide at 90–100 W). Never by stepping limits under a running OSC | Yes |
| **A2** two classes, no MCU | PDO1 5 V, PDO2 20 V / 3 A, PDO3 20 V / ≥ 3.5 A; POWER_OK3 (U1.14, currently NO_CONNECT on Board P) must be routed to a new header pin to mark the high class; latches after detach | Yes, at 20 V / 3 A | High class only, and only if OSC adopts PWR-D5 for the low class or reads the class pin | None |
| **B-common** two SKUs, one PCB, identical parts | One 20 V parts set (TVS2200, AOD4185L) in both SKUs; SKUs differ only in the NVM image (high: PDO2 20 V / ≥ 3.5 A; low: 15 V / 3 A) | Low SKU | High SKU (= C2) | None |
| **B-common-pop** one PCB, population variants | Dual footprints: low SKU fits SMAJ16A + AO3401A, high SKU fits TVS2200 + AOD4185L | Low SKU | High SKU | None |
| **B-separate** two PCBs | Low keeps today's Board P (SMAJ16A 26 V max at 15.4 A, 10/1000 µs, 25 °C, per [`power-budget.json`](power-budget.json) `input_protection_screen`, and AO3401A) | Low board | High board | None |
| **C1** fixed 20 V / 3 A | PDO1 5 V, PDO2 20 V / 3 A | Yes | **Not passed** (transient) | None |
| **C2** fixed 20 V high class | PDO1 5 V, PDO2 20 V / 3.5–5 A (D1), `SNK_PDO_NUMB = 2`, `POWER_ONLY_ABOVE_5V = 1` | No: refuses everything below the chosen class | Screen PASS on input power | None |

## A1 as a general-purpose PD product

This defines what A1 would have to guarantee. It is a candidate specification (PA), not a design.

**Class table** (calculated, unverified; script section 8; worst efficiency set, cable point; MF-MSMF250 hold at 23 °C caps 2.50 A and is lower when warm). Ratings are simultaneous, all-rail figures at the stated shape. "Peak-inclusive" means a load whose own peaks stay at or below these figures fits the contract on input power. The shape is the OSC ratio; other load shapes need their own calculation.

| Class | Accepted contract (cable) | Continuous shape +12 / −12 / +5 V | Peak-inclusive shape +12 / −12 / +5 V | Status |
|---|---|---|---|---|
| 0 | 5 V only, no matching PDO, or any fault | Rails off | Rails off | Refuse, indicate |
| 1 | 15 V / 3 A or 20 V / 2.25 A (45 W, 3 A cable) | 1.35 / 1.27 / 0.30 A (lower of the two rows) | 1.32 / 1.26 / 0.40 A | Screen only |
| 2 | 20 V / 3 A (60 W, or more behind a 3 A cable) | 1.82 / 1.71 / 0.30 A | 1.79 / 1.70 / 0.40 A | Screen only |
| 3 | 20 V / 3.25 A (65 W, 5 A e-marked) | 1.97 / 1.86 / 0.30 A | 1.94 / 1.84 / 0.40 A | Screen only |
| 4 | 20 V ≥ 3.5 A (≥ 70 W, 5 A e-marked) | 2.12 / 2.00 / 0.30 A at 70 W; up to the 2.50 A PTC cap at ≥ 90 W | 2.09 / 1.99 / 0.40 A at 70 W | **OSC class**: covers 2.0 / 1.9 / 0.4 A |

These figures come before any trip tolerance. Each rail's trip threshold must sit above its rating by the sensing tolerance, and the sum of the trip maxima must still fit the contract. That lowers the published ratings by an amount that is UNAV until a sensing chain is chosen. Unlike OSC, a general-purpose product can pick its ratings to leave that margin, so the LTC4282 no-window problem in R3 does not arise for A1's own general-purpose ratings; it can arise for the OSC minimum class (see verdict).

**Required behavior.**

| Event | A1 behavior | Never allowed |
|---|---|---|
| Attach | The MCU reads the contract (RDO status and source PDOs over I2C; `REQ_SRC_CURRENT = 1` makes the RDO carry the source's offered current). It sets the class lines, waits a defined time, then enables all rails together | Rails up before the class is valid |
| Class signal to the load | Two or more open-drain class lines on the header, valid before rails rise and released when rails drop. Not the latched POWER_OK pins | Using POWER_OK alone after detach |
| Load above the class rating | All-rail trip and latch with a fault indication. Restart only by re-attach or a user action | Constant-current limiting, rail sag, per-rail foldback (brownout) |
| Configured minimum class (for OSC) | A jumper or NVM field sets a minimum class. Below it, rails stay off with "insufficient source" shown | Running OSC on a lower class |
| Detach, hard reset | Input UVLO and a common enable drop all rails together; class lines release | One rail collapsing first |
| Re-contract or downgrade (multi-port charger, new Source_Capabilities) | ALERT interrupt to the MCU. If the new class is lower, all rails go off, the class lines update, and rails restart only at the new class after an off time. Never step limits with rails live | Live stepping |
| Upgrade while running | Keep the current class until the next off/on cycle | Raising limits under load |
| Reverse current | Per-rail reverse blocking (GAP-7) | Back-feed into Board B or the source |
| MCU fault | Watchdog reset forces rails off; hardware trip comparators work without firmware | Firmware-only protection |

**What A1 needs beyond C2.**

- MCU (STM32G031F8P6 used for pricing) with a supply from VBUS through an LDO, and a firmware image with an I2C driver for the PD controller.
- Per-rail current sensing, including a level-shifted −12 V sense, plus fast hardware trip comparators.
- VBUS and input current sensing.
- Class lines and a fault line on the Board B header. This needs a new header pin assignment.
- Calibration of the sense chain, and a test matrix of firmware × charger × cable.

**Failure modes.**

| Failure | Effect | Mitigation (candidate) |
|---|---|---|
| Class misread too high | Load overdraws; source OCP or hard reset collapses VBUS (brownout) | Hardware input-current trip set from the contract; rails trip on input UVLO |
| Charger advertises more than it delivers | Collapse under load | UVLO all-rail off; not a pass, only safe |
| Noncompliant cable on a > 3 A offer | Cable heating, undetectable by the sink | Open gate, as for C2 |
| Downgrade faster than the MCU can react | Short over-contract interval | PD timing for the new contract is UNAV; bench check |
| Firmware hang | Rails stay at the last state | Watchdog plus hardware trips |
| Load ignores the class lines | Trip on every overload | Documented load contract; OSC must read the class or set a minimum class |
| PTC heating at high class | 2.50 A hold at 23 °C falls with ambient | Thermal `NOT RUN` |

**Verdict for A1 (screen).** As a general-purpose product, A1 is feasible on paper and is **not rejected**. It is the most capable and the most work: firmware, sensing, calibration, a header change and a charger matrix. For full OSC, A1 can act like C2 only if its minimum class is high enough that the per-rail trip maxima (at least the OSC transient, or the 2.1 / 2.0 / 0.5 A interface maximum, plus sensing tolerance) still fit the contract. At class 4 / 70 W the window is only about 4.5 % per rail (calculated: 2.09 / 1.99 A capacity against 2.0 / 1.9 A) and is UNPROVEN until a sensing chain is chosen; at 90–100 W it is wide. Live stepping or current limiting under OSC always fails.

## Behavior gates common to every option (all NOT RUN)

| Event | Required behavior | Mechanism (draft) |
|---|---|---|
| Connect, wrong charger or cable | All rails off; "insufficient source" shown | NVM mismatch keeps VBUS_EN_SNK off (G-U). The indicator must sit on Board P, fed from VBUS_IN, as ATT asserted and PDOK not |
| Detach, charger swap, hard reset, multi-port 5 A→3 A downgrade | **Coordinated all-rail off, never a sag.** Re-enable only on a fresh contract at the required class | Board B input UVLO plus a common shutdown of all three stages. ST states VBUS_EN_SNK goes Hi-Z at detach and on hard-reset error recovery, but gives no timing (G-U); bench check |
| Startup | Inside the contract; no faster than the OSC 10 ms minimum soft start; within the OSC load-capacitance ceiling | Rule `inverting-startup-vs-pd-source` is open with the new stages |
| Source bands | 12.00–12.30 / 12.00–12.20 / 5.05–5.10 V | **FAIL with the TPS54560 internal reference on every rail (B1 R4b). Terminal sense plus a precision servo is needed (candidate, NOT RUN). This applies to every option** |
| Ripple | 1 mVpp at load; 2 / 1 mV precision gates | R4a `NOT RUN` (measurement) |
| Reverse current, interface maximum | Reverse blocking; 2.1 / 2.0 / 0.5 A enforced, with all-rail trip | R7 unresolved: PTC trip 5 A, no per-rail limiter with a 0.1 A window |
| Surge | Every VBUS-side absolute maximum respected | TVS2200 vs STUSB4500 28 V: 0.00 / −0.35 V. **CC pins 22 V absolute maximum against a CC-to-VBUS short: 2 V at nominal 20 V, about 1 V at 21 V (+5 %, PA reading of the source band), less during source transients**. Both OPEN |
| Cable | No overheating | A noncompliant 5 A offer on a 3 A cable is undetectable by the sink; OPEN |
| NVM production | Intended image in every unit | Per-unit write plus readback; endurance 1000 cycles at 105 °C (G-U) |

## Controller alternatives (G-U, via a summarizing fetch)

- **[AP33772S](https://www.diodes.com/datasheet/download/AP33772S.pdf)** (DS46176 Rev 10-2)
  - Needs an I2C host MCU. Without one it stays at 5 V.
  - VCC absolute maximum 34 V; CC 34 V.
  - Drives an external high-side NMOS.
  - Its OVP recovery text conflicts within the document.
- **[CYPD3177](https://www.infineon.com/assets/row/public/documents/24/49/infineon-cypd3177-24lqxq-datasheet-en.pdf)** (002-25383 Rev *C)
  - Resistor-strapped standalone operation, up to 5 A; raises FAULT and drops the output on mismatch.
  - VBUS absolute maximum 30 V; **CC 22 V**.
  - Its I2C content is UNAV.

The TVS2200 clamp is 28 V maximum at 40 A / 27 °C and 28.35 V maximum at 35 A / 125 °C (G). Against each controller's absolute maximum:

| Controller | Absolute maximum used | Margin, 27 °C / 125 °C |
|---|---|---|
| STUSB4500 | 28 V | 0.00 / −0.35 V |
| CYPD3177 | 30 V | +2.00 / +1.65 V |
| AP33772S | 34 V | +6.00 / +5.65 V |

None of these margins is an installed-surge result.

## Cost and manufacturing comparison (rough)

Owner direction: rough ratios are enough, and product feasibility comes first. Every ratio below is an **unverified project judgment (PA)** built from the retrieved IC subset and the count of cost drivers. No finished-product price was retrieved, and none is invented. The reference is **C2** (one PCB set, no firmware). The per-unit cost ratio (manufacturing one unit) and the effort ratio (one-off design, verification and test) are separate measures and are not combined. The current design (15 V Board P, LDO chain on Board B) is shown on the IC row only.

| Option | Per-unit cost vs C2 (PA, unverified) | Development and setup effort vs C2 (PA, unverified) | Main cost drivers | UNAV inputs |
|---|---|---|---|---|
| **C2** | 1.0× (reference) | 1.0× | Servo, shutdown, reverse blocking, 20 V Board P set, NVM readback, charger/cable matrix | Passives, PCB, assembly, test, protection network |
| **B-common** | About the same (≈ 1.0×) | About 1.0–1.1× | As C2, plus a second NVM image, label and SKU check | Test and support cost of the second SKU |
| **B-common-pop** | Low SKU about 0.95–1.0×; high as C2 | About 1.1–1.3× | Dual footprints, two BOM/CPL variants, misprogramming control | Layout feasibility of the dual footprints; assembly setup per variant |
| **B-separate** | About the same (≈ 1.0×) | About 1.5–2× | Second Board P layout, ERC/DRC/parity, bench and documents | PCB, stencil and assembly setup for the second board |
| **A1** | About 1.1–1.3× | About 2× or more | MCU, per-rail sensing and trip comparators, MCU LDO, header change, firmware, calibration, firmware × charger × cable matrix | Sensing chain, comparators, LDO, header, firmware effort |

Retrieved IC subset only (calculated from catalog prices, qty 1; not product cost; script section 10): the current design's PD sink, Board P TVS/MOSFET and Board B regulators total $30.86; C2 and both B-common SKUs $7.18; the low variant of B-common-pop or B-separate $6.34; A1 $8.42 (sensing UNAV). The difference between lineup options at this level is $0.84–1.24 per set; the big Board B saving is common to every option.

**Not retrieved (UNAV):** protection parts beyond TVS/MOSFET (BZX84-C24 clamp network, CC protection, reverse-blocking switches, per-rail limiters, LTC4282); servo op-amps, dividers and their count per rail; A1 current-sense amplifiers, comparators, MCU LDO and header; all passives and inductors; PCB fabrication; assembly (JLCPCB setup, extended-part fees, through-hole); stencils; test fixtures and per-unit test time; NVM programming and calibration time; firmware development; chargers; 5 A e-marked cables; enclosure and labels.

### Manufacturing and support drivers

| Driver | A1 | B-common (NVM-only SKUs) | B-common-pop | B-separate | C2 |
|---|---|---|---|---|---|
| PCB designs, ERC/DRC/parity sets (A2, not tabulated: Board P routes POWER_OK3 and the header gains a pin) | P + B redesign with MCU, sensing, header pins | 1 P + 1 B | 1 P (dual footprints, unscreened) + 1 B | 2 P + 1–2 B | 1 P + 1 B |
| Assembly variants | 1 | 1 | 2 BOM/CPL variants | 2 boards | 1 |
| Programming and test | Firmware + NVM; sense calibration; firmware × charger × cable matrix | NVM image per SKU; readback per unit | As B-common | Per board | One NVM image; readback per unit; charger and cable matrix |
| Firmware | Yes | No | No | No | No |
| Misprogramming risk | Firmware bug | Low SKU on the high image: safe (same parts). **High SKU on the low image: OSC on 15 V / 3 A, continuous FAIL, brownout.** Needs readback plus a SKU label check | **Low variant on a 20 V image overstresses SMAJ16A** | Same as B-common-pop | None across SKUs |
| User-facing label | Rating per class: needs a clear table | "Light: 45 W" and "High: ≥ 70–100 W + 5 A cable" | Same | Same | **20 V charger at or above the PDO2 class and a 5 A e-marked cable** |

Every option shares the source-band servo, the coordinated Board B shutdown, reverse blocking and the thermal work.

B-common, B-common-pop and B-separate low SKUs rely on the label alone; overload beyond the rating ends in source OCP or hard reset (a sag, not a coordinated off) unless input UVLO plus a common shutdown (D5) catches it. Only A1 enforces a rating.

<details>
<summary>Appendix: retrieved catalog prices and IC deltas at qty 1 / 10 / 100</summary>

All LCSC, USD per unit, CP(2026-10-20, qty 1/10/100, USD). Script section 9 holds the same data.

| Part | Role | Qty 1 | Qty 10 | Qty 100 | Stock / note | Source |
|---|---|---:|---:|---:|---|---|
| STUSB4500QTR | PD sink | 2.8412 | 2.4296 | 1.9095 | 5,002 | [C2678061](https://www.lcsc.com/product-detail/C2678061.html) |
| AP33772SDKZ-13-FA01 | A1 alternative | 3.8615 | 3.2923 | 2.6116 | **Out of stock** | [C24374260](https://www.lcsc.com/product-detail/C24374260.html) |
| CYPD3177-24LQXQ | Alternative | 1.6253 | 1.3689 | 1.0436 | 17, not production stock | [C2959321](https://www.lcsc.com/product-detail/C2959321.html) |
| STM32G031F8P6 | A1 MCU | 1.231 | 1.0942 | 0.8602 | 2,723 | [C529334](https://www.lcsc.com/product-detail/C529334.html) |
| TPS54560DDAR | Board B, 3 per set | 1.1049 | 0.9703 | 0.7487 | 9,536 | [C31966](https://www.lcsc.com/product-detail/C31966.html) |
| TVS2200DRVR | 20 V Board P | 0.5811 | 0.4659 | 0.3556 | 738 | [C523793](https://www.lcsc.com/product-detail/C523793.html) |
| AOD4185L | 20 V Board P | 0.4474 | 0.3524 | 0.2393 | 34, not production stock | [C77993](https://www.lcsc.com/product-detail/C77993.html) |
| SMAJ16A (Littelfuse) | Today's Board P D5 | 0.1468 (MOQ 5) | 0.1468 | 0.1237 (50+) | 17,670 | [C74561](https://www.lcsc.com/product-detail/C74561.html) |
| AO3401A (UMW) | Today's Board P Q1 | 0.0352 (MOQ 20) | 0.0352 (MOQ 20) | 0.0352 | 1,357,480 | [C347476](https://www.lcsc.com/product-detail/C347476.html) |
| LT3015EQ#PBF | Removed from Board B | 16.57 | 15.903 | 13.7398 | 813 | [C666306](https://www.lcsc.com/product-detail/C666306.html) |
| LT1963AEQ#TRPBF | Removed, 2 per set | 4.6427 | 4.0242 | 3.2844 | 2,120 | [C459702](https://www.lcsc.com/product-detail/C459702.html) |
| AP63201WU-7 | Removed | 0.7228 | 0.5884 | 0.4556 | **Out of stock** | [C2071044](https://www.lcsc.com/product-detail/C2071044.html) |
| LM2596S-ADJ (UMW) | Removed, 2 per set | 0.6299 | 0.5228 | 0.3864 | 65,715 | [C347423](https://www.lcsc.com/product-detail/C347423.html) |
| REF5050IDR | Servo reference example (every option) | 2.304 | 1.9462 | 1.4527 | 5,710 | [C24696](https://www.lcsc.com/product-detail/C24696.html) |

The TVS2200 page now shows 1+ $0.5811 and 10+ $0.4659. `supply-alternatives.md` records $0.4672 at 5+ from an earlier read; that row may be stale (not edited here).

IC deltas, USD per set, qty 1 / 10 / 100 (calculated):

| Change | Delta | Applies to |
|---|---|---|
| Board B: remove LT3015, 2× LT1963A, AP63201, 2× LM2596S | −27.84 / −25.59 / −21.54 | Every option |
| Board B: add 3× TPS54560 | +3.31 / +2.91 / +2.25 | Every option |
| Board P 20 V set: +TVS2200 +AOD4185L −SMAJ16A −AO3401A | +0.85 / +0.64 / +0.44 | All except the low board of B-separate and the low variant of B-common-pop |
| A1: add MCU only | +1.23 / +1.09 / +0.86 | A1; sensing, LDO, comparators and class lines UNAV |
| AP33772S + MCU instead of STUSB4500 (relative to C2); relative to A1 with MCU: +1.02 / +0.86 / +0.70 | +2.25 / +1.96 / +1.56 | A1 variant; the external-NMOS power-path topology change is UNAV |
| CYPD3177 instead of STUSB4500 | −1.22 / −1.06 / −0.87 | Any option |

**These are IC deltas, not finished-product BOM deltas.**

</details>

## Recommendation (marked; nothing adopted)

**Recommended screen basis: B-common with C2 as its high image.** One PCB and one parts set; the high NVM image is the OSC supply; a low image is available if the owner wants a light SKU. Reasons:

- Full OSC needs a ≥ 3.5 A, 20 V contract in every option. C2 delivers that with no firmware.
- One PCB with identical parts removes the misprogramming overstress of population variants. The retrieved saving from population variants is only $0.44–0.85 per set at IC level.
- A low SKU on the common PCB adds only an NVM image and a label at IC level; its test, labelling and support cost is UNAV.

**Alternatives, with reasons:**

- **A1** if a single adaptive product is preferred over SKUs. Feasible, but it needs firmware, sensing, header pins and a charger matrix; its added cost beyond the $0.86–1.23 MCU is UNAV. OSC then needs a minimum class whose trip window fits (see the A1 verdict).
- **A2** only if OSC adopts PWR-D5 or reads a class pin. Same-voltage PDO matching is an inference, not a stated ST case.
- **B-separate** only if the low SKU must keep today's Board P unchanged.

**Failed or not-passed options, with reasons (for full OSC only):**

- 15 V / 3 A and 20 V / 2.25 A: continuous FAIL on input current.
- C1, 20 V / 3 A: transient not passed. Source overload is UNPROVEN, and the best limiter has no window.
- 20 V / 3.25 A: transient EDGE, base efficiency only.
- A1 with live stepping or current limiting under OSC: brownout, never a pass.

**Main uncertainties:** PA efficiencies (all margins), the primary USB PD Peak Current text, same-voltage PDO matching and VBUS_EN_SNK timing (bench), thermal and PTC ambient, the servo terms, the TVS vs 28 V and CC 22 V gates, cable noncompliance, and every price not retrieved.

## Owner decisions requested (minimal; recommendation marked)

1. **D1, PDO2 current for the OSC class:** 3.5 A (≥ 70 W, +0.145 A margin), 4 A (≥ 80 W, +0.64 A), 4.5 A (≥ 90 W, +1.13 A) or 5 A (100 W only, +1.62 A). No recommendation: this trades charger reach against margin on PA efficiencies.
2. **D2, lineup shape:** B-common with C2 high image (**recommended**), A1, A2, B-common-pop or B-separate.
3. **D3, low SKU:** whether a light SKU is wanted at all. **This is open; it is not decided here.** If wanted, its rating and charger label are needed. Script section 5 screens two candidate low-SKU labels (1.2/0.8/0.5 A and 1.0/1.0/0.3 A) as PASS at 15 V / 3 A on input power (calculated, unverified).
4. **D4, controller for 20 V:** keep STUSB4500 and close the 0.00 / −0.35 V and CC 22 V gates, or evaluate CYPD3177 (30 V VBUS, CC 22 V) or AP33772S (34 V; needs an MCU; out of stock).
5. **D5, required work under every option:** input UVLO, coordinated all-rail enable, reverse blocking, an "insufficient source" indicator, and terminal sense plus a precision servo (B1 R4b).

## Requested OSC owner review

- Whether a 20 V charger offering at least the chosen PDO2 current (at least 70 W at 3.5 A, up to 100 W at 5 A) with a 5 A e-marked cable is an acceptable input class (PWR-D3).
- Accept/refuse semantics: rails stay off on any lesser contract.
- A detach, hard reset or 5 A→3 A downgrade on a multi-port charger gives a coordinated all-rail off. ST does not state the VBUS_EN_SNK timing, so it needs a bench check.
- If an A1 or A2 supply is chosen, whether OSC reads a class signal or relies on a minimum-class setting in the supply.
- If any OSC use on 60 W or 45 W is wanted, decide PWR-D5. The supply would then need:
  - the power-class signal: which header pin, its polarity, its validity after detach (the POWER_OK flags latch), and its pull-up domain;
  - the load-shedding domains and their sequence before rails rise;
  - the guaranteed degraded demand and transient.
- Terminal sense and servo placement against the source bands, the 1 mVpp ripple gate, and the PTC ambient of about 63 °C.
