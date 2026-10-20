# Product lineup screen (PD-003)

**Status: screening and exploration only. Nothing here is adopted.** Every schematic and PCB is an unvalidated draft. Efficiency, thermal, ripple, startup and surge checks are `NOT RUN` for every option. Nothing here is validated, qualified or released, and no option is chosen.

The figures come from [`../scripts/pcb/calculate-product-lineup.py`](../scripts/pcb/calculate-product-lineup.py). It imports the efficiency sets, ancillary currents, PTC terms and input-power method of [`../scripts/pcb/calculate-supply-alternatives.py`](../scripts/pcb/calculate-supply-alternatives.py) unchanged. Its hold-up integration matches the B1 gate screen. See [`supply-alternatives.md`](supply-alternatives.md), [`supply-capability.md`](supply-capability.md) and the B1 gate screen, which uses rows R3, R4a, R4b and R7. External sources were retrieved on 2026-10-20.

Evidence classes: **G** guaranteed manufacturer limit · **G-U** guaranteed or manufacturer-stated, but read only through a summarizing fetch or a secondary source, with no bytes retained · **DP** design point · **TYP** typical · **PA** project assumption · **CP(date, qty, currency)** catalog price, non-binding · **UNAV** unavailable.

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

Consequence: a supply that limits current under overload and lets the rails sag is a brownout and **fails**. The only admissible adaptive behavior for OSC is **accept or refuse**: all rails come up only on a contract that covers the full requirement, and otherwise all rails stay off with an indication.

## What the source actually offers

PDO sets follow the USB PD power rules as summarized by [Renesas](https://www.renesas.com/en/support/engineer-school/usb-power-delivery-02) (G-U):

- 27–45 W PDP: 5 V and 9 V at 3 A; 15 V scales with power.
- 45–60 W: 5, 9 and 15 V at 3 A; 20 V = PDP / 20.
- Above 3 A: the source must identify a 5 A e-marked cable, which it discovers over SOP′. Otherwise it caps at 3 A and 60 W.

So the 20 V offer is 2.25 A from a 45 W charger, 3 A from 60 W, 3.25 A from 65 W, 3.5 A from 70 W, 4.5 A from 90 W and 5 A from 100 W; every offer above 3 A needs a 5 A e-marked cable. The sink accepts only a source current at or above its PDO current, so **a 20 V / 5 A sink PDO refuses every charger below 100 W, and any charger behind a 3 A cable**.

The sink cannot detect a noncompliant source or cable that offers 5 A anyway. Cable and connector heating in that case is an **open gate**.

PPS (up to 21 V, G-U) adds no current. The STUSB4500 product page does not list PPS ([ST](https://www.st.com/en/interfaces-and-transceivers/stusb4500.html), G-U). **Source Peak Current coverage of the 20 ms transient is UNPROVEN and treated as not passed** (B1 gate screen R3). The 10 ms longest-window figure is secondary evidence only; the usb.org specification text was not retrieved.

## Per-PDO capability (Board B switcher-direct, TPS54560 ×3, PA efficiencies)

Board-input current range over the base / −3 pt / −5 pt efficiency sets, at the source-band output voltages. **PASS** means all efficiency sets fit the contract; **EDGE** means only the base set does.

| Contract (cable) | Board input V | Planning | Continuous | 20 ms transient | Startup envelope | All maxima at once? |
|---|---|---|---|---|---|---|
| 15 V / 3 A (3 A) | 14.00 | 3.11–3.30 **FAIL** | 3.48–3.70 **FAIL** | 4.14–4.40 **FAIL** | 3.59–3.82 **FAIL** | No |
| 20 V / 2.25 A, a 45 W charger (3 A) | 18.47–18.67 | 2.33–2.50 **FAIL** | 2.61–2.80 **FAIL** | 3.10–3.33 **FAIL** | 2.70–2.89 **FAIL** | No |
| 20 V / 3 A, 60 W, or 65/100 W on a 3 A cable (3 A) | 18.40–18.67 | 2.33–2.51 PASS | 2.61–2.81 PASS | 3.10–3.35 **FAIL** | 2.70–2.90 PASS | Continuous yes; transient no |
| 20 V / 3.25 A, 65 W (5 A e-marked) | 18.38–18.67 | PASS | PASS | 3.10–3.35 **EDGE** | PASS | Transient only at base efficiency; an LTC4282 window exists (±7.2 %, 3.018 A minimum) with 1.6–3.2 mF hold-up to 14 V |
| 20 V / 3.5 A, 70 W (5 A e-marked) | 18.35–18.67 | 2.33–2.52 PASS | 2.61–2.82 PASS | 3.10–3.35 PASS | 2.70–2.91 PASS | Yes, on input power only; 0.145 A transient margin |
| 20 V / 4 A, 80 W (5 A e-marked) | 18.31–18.67 | 2.33–2.52 PASS | 2.61–2.83 PASS | 3.10–3.36 PASS | 2.70–2.92 PASS | Yes, on input power only |
| 20 V / 4.5 A, 90 W (5 A e-marked) | 18.26–18.67 | 2.33–2.53 PASS | 2.61–2.83 PASS | 3.10–3.37 PASS | 2.70–2.93 PASS | Yes, on input power only |
| 20 V / 5 A, 100 W (5 A e-marked) | 18.22–18.67 | 2.33–2.54 PASS | 2.61–2.84 PASS | 3.10–3.38 PASS | 2.70–2.93 PASS | **Yes, on input power only** |

The transient passes on input power for any 20 V contract of at least about 3.38 A (about 68 W PDP) with a 5 A e-marked cable: 3.35–3.38 A worst case. **The 100 W minimum in C2 is a margin choice set by sink PDO2 = 20 V / 5 A, not a demand requirement.** PDO2 = 20 V / 3.5 A (at least 70 W) passes with 0.145 A screen margin at −5 pt; PDO2 = 20 V / 4 A (at least 80 W) with about 0.64 A. Whether the STUSB4500 NVM can encode these currents is UNAV in the owner bundle.

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

### The transient on a 20 V / 3 A contract

The sink-side limit must sit between the 2.81 A worst continuous draw and 3 A: a ±3.2 % window. **The best retrieved limiter is LTC4282, at ±3.7 % effective. It leaves no window at 2.81 A. Hold-up would be 2.9–4.3 mF to a 14 V floor or 8.0–13.0 mF for 1 V droop, and at −5 pt the limiter cannot recharge it** (B1 gate screen R3). Integrated ±10 %-class eFuses are far wider. At 20 V / 5 A the transient fits the contract, so no limiter or hold-up is needed.

## Can the existing STUSB4500 detect the contract and switch limits?

Sources: [DS12499](https://www.st.com/resource/en/datasheet/stusb4500.pdf) and [UM2650 Rev 3](https://www.st.com/resource/en/user_manual/um2650-the-stusb4500-software-programing-guide-stmicroelectronics.pdf), both read from st.com on 2026-10-20 through a summarizing fetch with no bytes retained, so G-U. The [owner bundle](../.claude/skills/component-stusb4500qtr/) keeps its own facts UNSOURCED.

| Capability | What the device provides | On Board P today |
|---|---|---|
| PDO selection (NVM) | Up to 3 sink PDOs; PDO1 is 5 V. Matching starts at the highest-priority PDO: voltage first, then source current ≥ sink current, and stops at the first match. With no match it makes a 5 V contract with capability mismatch (§3.3.2) | 2 PDOs; PDO2 = 15 V / 3 A intended; no retained NVM image |
| Path gate | `POWER_ONLY_ABOVE_5V = 1` enables VBUS_EN_SNK only on a PDO2 or PDO3 contract (Table 6) | Drives Q1. Accept/refuse without an MCU is policy `NOT RUN` until bench readback |
| Hard reset, mid-session 5 V re-contract | VBUS_EN_SNK behavior and timing are **not stated by ST** | Bench checks |
| Contract flags | POWER_OK2 / POWER_OK3 assert on the PDO2 / PDO3 contract at PS_READY. **They stay asserted after detach** (§2.2.8) | Only POWER_OK2 (PDOK) reaches JOUT1.4. POWER_OK3, GPIO and ALERT are NC. Board B routes ATT/PDOK only to test contacts |
| I2C status | RDO_REG_STATUS 0x91–0x94; source PDOs at 0x33–0x4E; ALERT_STATUS_1 0x0B; VBUS_VALID at 0x10; soft-reset renegotiation via 0x51 / 0x1A | Pogo pads only; the VREG_2V7 pull-up gate is open |
| Sensing | VBUS window ±5 % nominal, adjustable (§3.4.1). No current sensing | Not a brownout guard for Board B |

**Verdict.** NVM can, on paper, refuse any contract below one class. It cannot step per-rail current, and it cannot flag the class after a detach without ATT or VBUS qualification. Stepping needs an MCU, a class pin across the header, per-rail sensing and firmware, which is of no use to OSC. Production needs **per-unit NVM programming plus readback** under every option.

Alternative controllers (G-U, via a summarizing fetch):

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

## Behavior gates common to every option (all NOT RUN)

| Event | Required behavior | Mechanism (draft) |
|---|---|---|
| Connect, wrong charger or cable | All rails off; "insufficient source" shown | NVM mismatch keeps VBUS_EN_SNK off. The indicator must sit on Board P, fed from VBUS_IN, as ATT asserted and PDOK not |
| Detach, charger swap, hard reset, multi-port 5 A→3 A downgrade | **Coordinated all-rail off, never a sag.** Re-enable only on a fresh full-class contract | Board B input UVLO plus a common shutdown of all three stages. ST does not specify the VBUS_EN_SNK timing; bench check |
| Startup | Inside the contract and the OSC 10 ms / capacitance ceilings | Rule `inverting-startup-vs-pd-source` is open with the new stages |
| Source bands | 12.00–12.30 / 12.00–12.20 / 5.05–5.10 V | **FAIL with the TPS54560 internal reference on every rail (B1 R4b). Terminal sense plus a precision servo is needed (candidate, NOT RUN). This applies to every option, C2 included** |
| Ripple | 1 mVpp at load; 2 / 1 mV precision gates | R4a `NOT RUN` (measurement) |
| Reverse current, interface maximum | Reverse blocking; 2.1 / 2.0 / 0.5 A enforced, with all-rail trip | R7 unresolved: PTC trip 5 A, no per-rail limiter with a 0.1 A window |
| Surge | Every VBUS-side absolute maximum respected | TVS2200 vs STUSB4500 28 V: 0.00 / −0.35 V. **CC pins 22 V absolute maximum against a CC-to-VBUS short: 2 V at nominal 20 V, about 1 V at 21 V (+5 %, PA reading of the source band), less during source transients**. Both OPEN |
| Cable | No overheating | A noncompliant 5 A offer on a 3 A cable is undetectable by the sink; OPEN |

## Options

| Option | Configuration | OSC full mode | Firmware | Main blockers |
|---|---|---|---|---|
| **A1** adaptive, MCU stepping | STUSB4500 or AP33772S + MCU; per-rail sense and limits; class pin | **FAIL.** Stepping below demand is a brownout, and OSC cannot shed load | Yes | New header pin, MCU supply, firmware × charger matrix |
| **A2** accept/refuse with a class signal | PDO1 5 V, PDO2 20 V / 3 A, PDO3 20 V / 5 A | Only if OSC adopts PWR-D5 for PDO2 | None | Two PDOs at the same 20 V are unverified for matching; the 3 A contract fails the transient |
| **B-common** two SKUs, one PCB | One 20 V parts set (TVS2200, AOD4185L) in both SKUs. NVM: high 20 V / 5 A, low 15 V / 3 A | High: as C2. **Low: not an OSC supply** | None | Common 20 V parts trade the NVM-mismatch overstress for the open TVS-vs-28 V and CC 22 V gates in both SKUs; per-unit NVM readback stays mandatory |
| **B-separate** two boards | Low keeps SMAJ16A (26 V max at 15.4 A, 10/1000 µs, 25 °C, per [`power-budget.json`](power-budget.json) `input_protection_screen`) and AO3401A | As above | None | Doubles layout, ERC/DRC, bench and documentation work; a 20 V-programmed low unit overstresses SMAJ16A |
| **C1** fixed 20 V / 3 A | PDO1 5 V, PDO2 20 V / 3 A | Continuous PASS; **transient FAIL** | None | No limiter window (LTC4282 ±3.7 %); 3–13 mF |
| **C2** fixed 20 V / 5 A (**recommended screen basis**) | PDO1 = 5 V (mandatory), PDO2 = 20 V / 5 A, `SNK_PDO_NUMB = 2`, `POWER_ONLY_ABOVE_5V = 1` | **Screen PASS** on input power | None | See the C2 list below |

C2 blockers:

- A charger offering at least the PDO2 current at 20 V (100 W for PDO2 = 5 A; at least 70 W if PDO2 = 3.5 A is chosen) and a 5 A e-marked cable.
- Cable noncompliance gate.
- Source bands (R4b): terminal sense plus a servo.
- 1 mVpp ripple (R4a, `NOT RUN`).
- Interface-maximum enforcement and reverse blocking (R7).
- TVS vs 28 V and CC 22 V margins.
- PTC ambient about 63 °C.
- VBUS_EN_SNK bench checks.

The low SKU's useful range for lighter, non-OSC products, at a 15 V / 3 A, 14.0 V floor, switcher-direct, PA: the 1.2 / 0.8 / 0.5 A label draws 2.24–2.38 A, PASS, and 1.0 / 1.0 / 0.3 A draws 2.16–2.30 A, PASS. These are screen results, not ratings.

## Retrieved prices and BOM deltas

All prices are per unit.

| Part | Role | Qty 1 | Qty 10 | Qty 100 | Stock | Source |
|---|---|---:|---:|---:|---|---|
| STUSB4500QTR | PD sink | $2.8412 | $2.4296 | $1.9095 | 5,002 | CP(2026-10-20, qty 1/10/100, USD) [LCSC C2678061](https://www.lcsc.com/product-detail/C2678061.html) |
| AP33772SDKZ-13-FA01 | A1 alternative | $3.8615 | $3.2923 | $2.6116 | **Out of stock** | CP(2026-10-20, USD) [LCSC C24374260](https://www.lcsc.com/product-detail/C24374260.html) |
| CYPD3177-24LQXQ | Alternative | $1.6253 | $1.3689 | $1.0436 | 17, not production stock | CP(2026-10-20, USD) [LCSC C2959321](https://www.lcsc.com/product-detail/C2959321.html) |
| STM32G031F8P6 | A1 MCU | $1.231 | $1.0942 | $0.8602 | 2,723 | CP(2026-10-20, USD) [LCSC C529334](https://www.lcsc.com/product-detail/C529334.html) |
| TPS54560DDAR | Board B stage, 3 per set | $1.1049 | $0.9703 | $0.7487 | 9,536 | CP(2026-10-20, USD) [LCSC C31966](https://www.lcsc.com/product-detail/C31966.html) |
| TVS2200DRVR | 20 V Board P | $0.4672, 5+ price | UNAV | UNAV | — | CP(2026-10-20, 5+, USD), from `supply-alternatives.md` |
| AOD4185L | 20 V Board P | $0.4474 | UNAV | UNAV | 34, not production stock | CP(2026-10-20, qty 1, USD), from `supply-alternatives.md` |
| LTC4282, sense parts, 3.3 V LDO, servo reference, charger, cable | — | UNAV | UNAV | UNAV | — | Not retrieved |

Three TPS54560 cost $3.31 per set at qty 1.

IC deltas at qty 1:

- **C2.** About −$24.5 on Board B (from `supply-alternatives.md`). Board P adds about $0.9 gross, before removing SMAJ16A and AO3401A, whose prices are UNAV.
- **A1.** Adds at least the $1.23 MCU. The AP33772S route adds $3.86 and removes the $2.84 STUSB4500.
- **CYPD3177 instead of STUSB4500.** −$1.22.

Qty 10/100 deltas were not computed. **IC deltas do not set finished-product cost.**

| Cost driver | A1 | B-common | B-separate | C2 |
|---|---|---|---|---|
| PCB designs and ERC/DRC/parity sets | P + B redesign, plus MCU | 1 P + 1 B | 2 P + 1–2 B | 1 P + 1 B |
| Calibration and test | Firmware × charger matrix, sense calibration | NVM image per SKU, readback per unit | Per board | One NVM image, readback per unit, charger and cable matrix |
| Firmware | Yes | No | No | No |
| Inventory SKUs | 1 board, firmware variants | 2 NVM SKUs | 2 boards | 1 |
| User-facing label | Ratings per charger class: confusing | "OSC: 100 W + 5 A cable" vs "light: 45 W" | Same | **20 V charger at or above the PDO2 current (70–100 W) and 5 A e-marked cable required** |

Every option shares the source-band servo, the coordinated Board B shutdown and the thermal work. Board fabrication, assembly, charger and cable prices are **UNAV**.

## Owner decisions requested (recommendation marked; nothing chosen)

1. **Product configuration.** **C2, fixed 20 V / 5 A** (recommended). Alternatively, C1 or A2 only if OSC adopts PWR-D5. A1 and the low SKU do not power OSC.
2. **Low SKU for lighter products.** If one is wanted, use B-common with the single 20 V parts set in both SKUs, accepting its open TVS and CC gates.
3. **Controller for 20 V.** Keep STUSB4500 and close the 0.00 / −0.35 V and CC 22 V gates, or evaluate CYPD3177 (30 V VBUS, CC 22 V) or AP33772S (34 V; needs an MCU; out of stock).
4. **Board B shutdown architecture.** Approve input UVLO, coordinated all-rail enable, reverse blocking and a Board P "insufficient source" indicator as required work.
5. **Precision.** Approve terminal sense plus a precision servo (B1 R4b) as required work.

## Requested OSC owner review

- Whether a 20 V charger offering at least the chosen PDO2 current (at least 70 W at 3.5 A, up to 100 W at 5 A) with a 5 A e-marked cable is an acceptable input class (PWR-D3).
- Accept/refuse semantics: rails stay off on any lesser contract.
- A detach, hard reset or 5 A→3 A downgrade on a multi-port charger gives a coordinated all-rail off. ST does not specify the VBUS_EN_SNK timing, so it needs a bench check.
- If any OSC use on 60 W or 45 W is wanted, decide PWR-D5. The supply would then need:
  - the power-class signal: which header pin, its polarity, its validity after detach (the POWER_OK flags latch), and its pull-up domain;
  - the load-shedding domains and their sequence before rails rise;
  - the guaranteed degraded demand and transient.
- Terminal sense and servo placement against the source bands, the 1 mVpp ripple gate, and the PTC ambient of about 63 °C.
