# As-built identity, LED Board P bring-up findings and PD controller options (research)

**Status: research only. Nothing here is adopted.** No part, schematic, PCB, NVM image or controller is changed or selected. No rework, NVM programming, energizing or bench step is authorized by this page; every bench step below is a proposal that needs its own owner approval. Every schematic and PCB stays an unvalidated draft. Requested on zudo-pd#218 (comment 6286606035, items 1 and 4).

Sibling repository: [Takazudo/zudo-led-lamp](https://github.com/Takazudo/zudo-led-lamp), read only at `origin/main` `1fc399e` (the commit the LED audit also used). Evidence classes: **G** guaranteed (official primary source), **G-U** guaranteed figure from a mirror or unsourced copy, **TYP** typical, **PA** project assumption, **UNAV** unavailable. "Measured" below always means a measurement reported on the **LED** boards; nothing has been measured on any zudo-PD board.

## 1. Which hardware actually exists

### 1.1 zudo-PD hardware ordered: renewal Board B only (no PD Board P)

**Identity (owner, zudo-pd#218 comments 6287052727 and 6287748641):** the zudo-PD order shown as 2026-09-20 03:33:54 contains **renewal Board B and zudo-bus, and no Board P**. The owner confirms the PD-specific Board P (D5 SMAJ16A) was **not ordered**; the intention was to verify the LED Board P (§1.2) first. No manufactured PD Board P exists, so no zudo-PD Board P state is "as built", and the complete P+B system is not S3.

**Board B component configuration matches S3** (owner, from the authenticated JLCPCB order-history BOM dialog, read only): U6/U7 C459702 (LT1963AEQ#TRPBF), U8 C666306 (adjustable LT3015EQ#PBF), R26 C861589, R27 C861519, R28 C110776. That excludes S1 and S2, which carry C107286 / C666307 and no R26–R28. The BOM dialog does **not** establish Board B copper, mask, paste or silk identity, or the LED2 rotation, and no production-file hash or substitution history was obtained (a download attempt had an uncertain outcome; no downloaded file is claimed). Those remain unverified.

Package reference: [`releases/corner-support-review/`](releases/corner-support-review/), last changed at commit `f25194f` (2026-09-22); nothing under `manufacturing/releases/` changed from `f25194f` to HEAD. Board B files at HEAD (the package `SHA256SUMS` agrees; the Board P files in the same package were never manufactured):

| File | SHA-256 |
|---|---|
| `board-b/bom.csv` | `e238ec7cf620b6054b5ecb155a54574334e0073893e3526a60f449d7cb030c7d` |
| `board-b/cpl.csv` | `8b92bd161ae30e0d0ef114335c42b538cd9b7221526f319e77ac946cf991a252` |
| `board-b/board-b-gerbers.zip` | `9fc4e93e717865110e227cd4d95ee110e005e738771286ff40b8275eb1917de4` |

Package history after the stated order time (every commit is later than 03:33:54 in any timezone; the zudo-bus archive commit 23 minutes later suggests JST):

| State | Commit (committer time) | U6/U7 | U8 | Board B copper |
|---|---|---|---|---|
| S1 | `8157428` / `ec656b7` (2026-09-21 01:56–02:31 +0900) | LT1963AEQ#PBF C107286 | LT3015EQ-12#PBF C666307 (fixed −12 V) | — |
| S2 | `aeeff56` (2026-09-21 13:20 +0900) | as S1 | as S1 | Zip changed only in date stamps (S2 changed Board P D5 only) |
| **S3 (matches the ordered BOM)** | `f25194f` (2026-09-22 01:06 +0900) | LT1963AEQ#TRPBF C459702 | LT3015EQ#PBF C666306 (adjustable) with new divider R26–R28 | BOM/CPL and F_Cu, mask, paste and silk layers; LED2 CPL rotation 90 → 270 |

Inference (not stated by the owner or JLCPCB): because the S3 commit postdates the order, the LDO substitutions and the U8 divider were probably applied during JLCPCB order review; no substitution history was established. Whether the built copper and LED2 placement also match S3 is open; an unpowered look at Board B (R26–R28 pads present, LED2 orientation) can confirm it.

**Historical only:** the v0.3.0 combined board (JLCPCB-confirmed BOM in `jlcpcb-order-snapshots/v0_3_0/`), v0.4.0 as packaged (`7854736`, D4 USBLC6-2 on VBUS_IN, RESET tied to GND) and the post-#93 variant (`9f4d624`) are earlier revisions, not the boards on the bench. The `corner-support-review/ORDER-NOTES.md` sentence that no renewal hardware was ordered is superseded for Board B (ordered) and remains correct for Board P (not ordered).

**Sibling packages (read only, `origin/main`, no later edits to these paths):**
- zudo-led-lamp: `manufacturing/jlcpcb/2026-09-19/` at `d13540d` (2026-09-19 07:44:56 +0900, 4 minutes after the stated 07:41:02 order). `board-p/bom.csv` `7969f3915955af36251a000f3f036c0ad5efa4dc3009568403e3335577cc613f`, `board-p/board-p-gerbers.zip` `196c8702bc0e00d830d2895265d14a3c97732affa4b730bf6cae2bd2501e0126`. Matches the order variant on file timing; the factory-confirmed data was not downloaded (`manufacturing/ORDER-STATUS.md`, outside the package folder). The retained CPL already includes the owner's Board L RV1 180° fix.
- zudo-bus: `manufacturing/jlcpcb/2026-09-20/` and `2026-09-20-r2/` both added at `bea5d58` (2026-09-20 03:57:21 +0900; `9107a8a` a minute later changed only `.gitattributes`). `zudo-bus-order-2026-09-20.zip` `5fc3dd9536fc9a06ba09391e534d94e63c6e8bcc413bf636af359b1c1aa7c5d3`, `-r2.zip` `6e5d484f33520299b1ea5676243cef9b2fb3718ff416a767a5eb79308343dcde`. `ORDER-STATUS.md` says r2 (U1 CPL rotation 90) is the corrected reference and "not a claim that it was the exact uploaded archive"; the user corrected U1's rotation in JLCPCB's viewer, so we infer (not confirmed) that the built placement matches r2.

### 1.2 zudo-led-lamp Board P that arrived

- Release `manufacturing/jlcpcb/2026-09-19/` (commit `d13540d`); the order was reported by the user; JLCPCB's final factory data was not downloaded (`ORDER-STATUS.md`). Two PCBAs are on the bench (#144).
- Fitted BOM (`board-p/bom.csv`): STUSB4500QTR, AO3401A, **SMAJ20A D5 C571370** (input TVS; VC max 32.4 V at its rated IPP, waveform-conditioned, #34), TYPE-C-31-M-17, R11 100 kΩ, **R12 150 kΩ**, R13/R14 470 Ω, R15/R16 4.7 kΩ to VREG_2V7, R19/R20 0 Ω DB links, **R21 10 kΩ RESET pull-down**, C1 10 µF, C2/C35 100 nF, C30/C34 1 µF. R17/R18 (external Rd) and D6/D7 (CC protection) are **DNP**.
- The LED audit (#144 comment 6002714821) confirmed generator/netlist/BOM/CPL parity for this release (file parity, not physical assembly).
- This LED Board P is the **existing USB-board candidate for initial verification** (owner, comment 6287748641): D5 C571370 (SMAJ20A), U1 C2678061 (STUSB4500QTR) per the JLCPCB order-history BOM. It is not evidence that a PD Board P with SMAJ16A was manufactured.
- **The unbuilt zudo-PD renewal Board P design (§1.1) is the same circuit** (`scripts/schgen/board_p_spec.py`: R21 10 kΩ, R15/R16 on VREG_2V7, R19/R20 DB links, R17/R18/D6/D7 DNP) **except D5 = SMAJ16A** instead of SMAJ20A.

## 2. LED Board P findings (LED measurements only)

### 2.1 What was measured on the LED boards (#144, as reported)

- Early readings: VBUS_IN reached 15 V while VBEN and the Q1 gate sat at about 15 V (switch off) and JOUT1 read millivolts. Once, with Board L attached, the output briefly reached 15 V and collapsed.
- Current state, both PCBAs, 3 chargers and several cables: VBUS stays at 5 V, VBEN ≈ VBUS (Hi-Z), JOUT1 millivolts.
- **RESET (U1.6) = 0.93 V** powered from 5 V, with R21 10 kΩ to GND (about 93 µA must be flowing from somewhere).
- Active CC = 1.43 V (consistent with a single Rd on a 3 A source).
- NVM was written earlier (PDO2 15 V / 3 A, `POWER_ONLY_ABOVE_5V=1`) and read back; the ST GUI now reports "I2C read error" (host restart pending, so not yet separated from a host-side fault).
- #143: J2/J3 silkscreen labels are wrong (J2.4 printed `NC` is RESET; J3.5 printed `RST` is GND). Probing by silkscreen can misidentify or drive RESET.

### 2.2 Board-level causes to rule out before blaming the chip

Ranked from the LED audit plus this review; none is proven.

| # | Candidate | Basis | Status |
|---|---|---|---|
| B1 | **RESET outside its guaranteed low (≤ 0.35 V; high ≥ 1.2 V)** at 0.93 V | DS12499 Table 22 (G-U in the project bundles; the LED audit read the full Rev 7 PDF from ST's official repository) | Strongest candidate for the present inability; the source of the ~93 µA is unidentified. ST's own application circuit also uses a 10 kΩ RESET pull-down, so "R21 too large" is not supported |
| B2 | RESET disturbed through J2.4 (silkscreen `NC`, #143) by a jig, probe or leakage path | #143 mapping; unpowered RESET→SCL ≈ 13 kΩ reading | Plausible contributor; not shown |
| B3 | **R15/R16 load VREG_2V7**, which ST describes as decoupling-only | DS12499 §2.2.15 | Documented-use mismatch; low confidence as the autonomous root cause (idle-high lines draw almost nothing) |
| B4 | Assembly (U1 QFN voids/bridges, EP, R21 value/placement) on both boards | Same symptom on two boards argues against a random defect, not against a systematic one | Not inspected |
| B5 | Host/programmer state (I2C error after earlier success) | #144 notes pending host restart | Open |
| B6 | Input TVS **SMAJ20A VC max 32.4 V at IPP** (waveform-conditioned, #34), above the STUSB4500 28 V absolute maximum (G-U) | #34 primary evidence | Not a cause of the 5 V-only symptom, but a damage path on any surge; unresolved gate |
| — | CC topology, R14 path, NVM content, Q1 | LED audit static checks | Not supported as present root causes |

Chip incompatibility is not indicated by any of this: the documented conditions (B1, B3, B6) are design or operating-condition departures that a different board could remove.

### 2.3 Which LED findings apply to the zudo-PD Board P design (not built)

| Finding | zudo-PD renewal Board P design (never manufactured) |
|---|---|
| R21 10 kΩ RESET pull-down + J2.4 RESET pad | **Applies** to the design (same circuit) |
| R15/R16 4.7 kΩ on VREG_2V7 | **Applies** |
| J2/J3 silkscreen labels from Board A | **Applies**: same footprints; check labels against the netlist before probing |
| TVS above 28 V | D5 SMAJ16A instead of SMAJ20A: 26 V at 25 °C (G), hot clamp unproven (PD-CLAMP-1). Design only; no PD Board P was built |
| DB links + DNP Rd | Applies (same as LED) |

The historical v0.4.0 differences (RESET tied to GND, D4 USBLC6-2 on VBUS, external Rd fitted) no longer describe the design.

**No LED measurement is a measurement of any zudo-PD board**, and none may be attributed to the untested PD Board B. The PD-side gates in [`input-clamp-fix.md`](input-clamp-fix.md), [`design-gaps-20v.md`](design-gaps-20v.md) and LED #34 stay open.

### 2.4 Proposed diagnostic sequence (not executed; each step needs approval)

Read-only and low-energy steps first. None is authorized here. D3 and D4 energize the LED boards; LED #34's safety gate says "Do not energize either board for USB-PD operation" until its checks close, so they also need that gate resolved or explicitly waived by the owner.

| Step | Board | Action | Needs |
|---|---|---|---|
| D0 | zudo-PD | **Done for components** (owner, comment 6287748641): Board B BOM matches S3; no PD Board P exists. Copper/silk and LED2 rotation not yet confirmed | — |
| D1 | zudo-PD Board B | Unpowered visual and continuity check against the S3 netlist (R26–R28 fitted, U6–U8 markings and orientation, LED2 polarity, J5/J6/J7 labels against nets). Procedure for approval: [`board-b-unpowered-check.md`](board-b-unpowered-check.md) | Approval (handling only) |
| D2 | LED | Unpowered: measure R21 out of circuit or lift one end; check RESET pad to every neighbour | Approval (rework) |
| D3 | LED | Current-limited 5 V on VBUS only, programmer disconnected: RESET, VREG_2V7, VREG_1V2, VDD | Approval (energizing) |
| D4 | LED | The LED audit's single rework test (R21 bridged to 0 Ω, R15/R16 removed, SCL/SDA grounded), then one cold 15 V attach | Approval (rework + energizing) |
| D5 | zudo-PD Board B | Only after D1, with a verified USB source board (for example the LED Board P after D2–D4) and the Board B gates closed: current-limited bring-up. No PD Board P exists to pair with it | Approval (energizing) |

## 3. STUSB4500: board faults vs intrinsic limits, and simpler alternatives

### 3.1 Separate the two

**Board or operating-condition faults** (fixable in this design): RESET level (B1/B2), VREG_2V7 loading (B3), silkscreen labels (#143), TVS clamp above 28 V (B6), possible host/I2C state (B5). None of these is a property of the STUSB4500 itself.

**Intrinsic STUSB4500 properties** (would follow the chip into any design; from the owner bundle and [`product-lineup.md`](product-lineup.md), G-U unless noted):
- Configuration lives in **NVM written over I2C** (UM2650); every unit needs programming and readback, and the NVM is specified for **1000 write cycles at TA = 105 °C** (DS12499 Table 22; the owner-bundle endurance fact remains open, see `product-lineup.md`).
- **POWER_OK flags stay asserted after detach** until a new attach or reset; they are contract-state flags, not live-voltage indicators.
- One FLEX current is shared by the flexible PDOs; matching needs exact voltage and sink current ≤ source current, otherwise a 5 V contract.
- VREG_2V7 is decoupling-only, so programming needs a separate logic supply for the I2C pull-ups.
- VBUS-side pins 28 V and CC 22 V absolute maximum (G-U), which drives the clamp problem.
- No documented hot-plug, slew or VDD series-resistor guidance (DS12499 Rev 8, see `input-clamp-fix.md`).

### 3.2 Simpler fixed-profile sinks (retrieved 2026-10-20; nothing adopted)

| Part | Configuration | Max PDO / current | VBUS-side abs max | Diagnostics | Load switch | Source and class |
|---|---|---|---|---|---|---|
| **STUSB4500** (current) | NVM via I2C; 3 PDOs | 20 V; up to 5 A | 28 V (VDD etc.), CC 22 V | POWER_OK2/3, ALERT, I2C status | Open-drain VBUS_EN_SNK to external PMOS | DS12499 Rev 8, G-U |
| **Infineon CYPD3177** (EZ-PD BCR) | **Resistor straps** on VBUS_MIN, VBUS_MAX, ISNK_COARSE, ISNK_FINE; pre-programmed, no firmware; optional I2C host | 5 / 9 / 12 / 15 / 19 / 20 V; 0–5 A coarse + up to 0.9 A fine | VBUS_IN 30 V (operating 3–24.5 V); CC1/CC2 22 V | **FAULT** pin on mismatch or ±20 % VBUS; SAFE_PWR_EN 5 V fallback; does not monitor current | Drives VBUS_IN/VDC_OUT path (external FET) | [Datasheet 002-25383 Rev *C, 2024-09-18](https://www.infineon.com/assets/row/public/documents/24/49/infineon-cypd3177-24lqxq-datasheet-en.pdf), G; reference design CY4533 EVK |
| **Hynetek HUSB238** | **VSET / ISET resistors** (open = 20 V / 3.25 A); I2C override optional; factory fuse defaults | 20 V; 3.25 A (no 5 A stated) | VIN 30 V (operating 3–25 V) | OVP/UVP/OTP actions; no dedicated fault pin documented | GATE open-drain to external PMOS | Rev 2.0, Jan 2021, [SparkFun mirror](https://cdn.sparkfun.com/assets/9/1/7/a/4/USB_PD_Sink_HUSB238.pdf), **G-U** (not from Hynetek directly) |
| **WCH CH224K** | CFG1 resistor (9/12/15/20 V) or level mode | 20 V request; current not stated | VIOHV (VBUS/CFG pins) 13.5 V, used with external series resistors; **CC 8 V** | PG open-drain; OVP/OTP | None (CH224D has GATE) | Datasheet V1F, [distributor mirror](https://uelectronics.com/wp-content/uploads/2025/04/ch224k-Datasheet.pdf), **G-U** |
| **Diodes AP33772S** | **Needs a host MCU over I2C**; boots to 5 V only | 21 V SPR / 28 V EPR; 1–5 A | VCC 34 V, CC 34 V | Rich: OVP/UVP/OCP/OTP status, INT, NTC | Charge-pump N-MOS driver | [DS46176 Rev 2-2, Nov 2023](https://www.diodes.com/assets/Datasheets/AP33772S.pdf), G |

### 3.3 Reading of the comparison (recommendation marked; not adopted)

- **Simplest setup and factory verification: CYPD3177.** Its profile is set by resistors, so it is pre-programmed and needs no per-unit programming step (the datasheet does not state whether it has internal flash or NVM), and it has a dedicated FAULT pin plus a 30 V VBUS rating, which eases the 28 V clamp problem on the VBUS side only: its CC1/CC2 are 22 V absolute maximum like STUSB4500 (Table 5, G), so the CC gate (GAP-2) stays. It does not monitor current, so the project's input trip (power-limit-60w.md) is still needed. Availability, price and exact pin-level evidence are not retrieved (UNAV); it would need a new owner bundle before any use.
- **HUSB238** is similarly resistor-configured but is documented only from a mirror (G-U) and to 3.25 A, which rules it out for a ≥ 3.5 A full-OSC contract.
- **CH224K** is the cheapest class, but its CC pins are rated 8 V absolute maximum (a CC-to-VBUS short at 20 V is far outside it), its 13.5 V VIOHV rating relies on external series resistors, and its current behavior is undocumented; it is a poor fit for a protected 20 V product.
- **AP33772S** has the best diagnostics and 34 V ratings but requires an MCU and firmware, which adds the A1-style effort the owner already flagged.
- **Keeping STUSB4500** remains viable once the board faults above are removed; its intrinsic costs are the per-unit NVM programming, the stateful POWER_OK and the 28 V clamp margin.

**Candidate direction (marked, not adopted):** fix the board-level conditions first (they apply to the LED Board P and to the unbuilt zudo-PD Board P design), and evaluate CYPD3177 as the leading simpler alternative for zudo-PD-60W in a separate, approved evidence pass. The STUSB4500 is not shown to be incompatible.

### 3.4 Manufacturing repeatability (owner criterion, zudo-pd#218 comment 6286650616)

The owner's example of ordering 60 units and having to troubleshoot about 20 of them individually is a **hypothetical concern, not an observed or estimated failure rate**. No pilot or 60-unit order is authorized. The comparison below weighs per-unit setup, test clarity, board-to-board variation and rework alongside BOM cost.

All times and ratios are **PA estimates**, derived from the number of manual steps each option needs per unit (fixture insertion, program, read back, functional attach, record), at roughly 0.5–1 min per step for a jig-based flow. They are not measured. BOM deltas are rough ratios of the Board P controller section against the STUSB4500 section = 1.0, judged from part count and the retrieved IC prices where available; prices for CYPD3177, HUSB238 and CH224K are UNAV.

| Option | Per-unit programming / setup | Clear pass/fail test | Board-to-board variation sources | Diagnosis and rework burden | Board P controller BOM (PA) |
|---|---|---|---|---|---|
| **STUSB4500 (NVM)** | Jig contact on J2; write the 40-byte NVM image; read back and compare; reload (power cycle); then functional attach. About 4–5 steps, about 2–5 min per unit | Byte-exact readback against the released image **plus** a contract check (PD analyzer or trigger: requested PDO accepted, VBEN asserted, output in band) | Wrong or partial image; I2C bus problems (pull-ups on VREG_2V7, RESET level, pad labels #143); host/GUI state; NVM endurance 1000 cycles at 105 °C limits re-programming loops | High when it fails: the LED boards show that "no contract" can come from RESET, I2C, NVM or source behavior, each needing separate probing | 1.0 |
| **CYPD3177 (resistor straps)** | None beyond assembly; functional attach only. About 1–2 steps, about 1 min | Contract check plus a defined **FAULT** pin state and SAFE_PWR_EN on a mismatching source | Strap-resistor tolerance and divider ratio on VBUS_MIN/VBUS_MAX/ISNK pins: datasheet 002-25383 Rev *C gives only suggested divider values, no resistor tolerance, and warns about layout noise on VBUS_MIN; band margin not yet computed; assembly | Low: the FAULT pin separates "source cannot supply" from board faults; straps can be checked unpowered | About 1.0–1.2 (more straps and FETs; IC price UNAV) |
| **HUSB238 (VSET/ISET)** | None with resistor setting; functional attach. About 1–2 steps | Contract check; GATE state. No dedicated fault pin documented | VSET/ISET resistor tolerance; factory fuse variant | Medium: fewer observable states than CYPD3177 | About 1.0 (IC price UNAV); limited to 3.25 A |
| **AP33772S + MCU** | Flash MCU firmware (one image, can be verified); functional attach. About 3–4 steps, about 1.5–4 min | Firmware self-test plus status register readout (OVP/UVP/OCP/OTP) plus contract check | Firmware image version; MCU clock/programming contacts; I2C between MCU and AP33772S | Medium: rich diagnostics, but firmware adds its own failure modes | About 1.2–1.5 (MCU, LDO, programming header) |
| **CH224K (reference only)** | None (CFG resistor); attach | PG pin plus contract check | CFG resistor; series resistors on VBUS | Low for setup; unsuitable at 20 V (CC 8 V absolute maximum) | About 0.8–1.0 |

**Reading (marked, not adopted).** A pre-programmed, resistor-strapped controller (no per-unit programming) with a fault output (CYPD3177) removes the per-unit programming and readback step and the I2C-bus failure modes that dominate the LED diagnosis. A small BOM increase may be worth that, as the owner suggested. Its own repeatability risk, strap tolerance against the code bands, has not been calculated yet and must be before any comparison is final. Keeping STUSB4500 is still viable if the programming flow is made deterministic: an independent I2C pull-up supply, RESET held at a valid level, a byte-exact readback gate and a functional contract gate per unit.

**What current validation should establish.** The aim is the **cause** of the LED Board P failure and a **repeatable procedure** that gives the same result on every board, not a single board that once produced output. In the plan in §2.4, D0–D1 fix which hardware is being tested, D2–D3 isolate the RESET and supply conditions, and D4 is the single rework test. A pass means the defined pass/fail checks above hold on **both** LED boards after the same rework, and the steps are written down so another unit can be processed the same way. Each step still needs approval, and LED #34's energization gate still applies.

### 3.5 Open items

- zudo-PD as-built state: Board B only, components match S3 (owner, JLCPCB BOM dialog); copper/mask/paste/silk and LED2 rotation unconfirmed; no production-file hash. No PD Board P was ordered.
- Source of the LED RESET current; outcome of the LED rework test (needs approval).
- Primary (manufacturer-hosted) copies of HUSB238 and CH224K datasheets; CYPD3177 and AP33772S pin-level evidence, availability and price.
- None of the alternatives has an owner bundle, footprint or symbol in this repository.
