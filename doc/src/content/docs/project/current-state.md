---
title: Current State — P15, PD15 and PD20
sidebar_position: 2
---

Status on **2026-11-20 UTC** (campaign [#318](https://github.com/Takazudo/zudo-pd/issues/318), tracker
[#228](https://github.com/Takazudo/zudo-pd/issues/228)). This page owns current status.
[Variant architecture](../architecture/index.mdx) owns design responsibilities;
[release readiness](../architecture/release-readiness.md) owns acceptance gates. A software check, CAD result,
export receipt, order plan, received unit and bench measurement establish different things.

| Stream | Current source | Order files | Ordered / received | Programmed / measured |
| --- | --- | --- | --- | --- |
| Shared P15 r1 | `boards/board-p15/`, `board_p15_spec.py` | Fixed package `manufacturing/releases/corner-support-review/board-p15/` ([handoff](https://github.com/Takazudo/zudo-pd/blob/main/manufacturing/p15-order-handoff.md)); 2 assembled sets | Not ordered | NOT RUN |
| PD15 | P15 + `boards/board-b/` | P15 only; 0 new Board B | Renewal Board B (S3) received 2026-09; identity, usable count and D1 inspection incomplete | NOT RUN |
| PD20 | Board P r3 + `boards/board-b20-draft/` | Revision-bound package `manufacturing/releases/pd20-prototype-review/` ([order sheet](https://github.com/Takazudo/zudo-pd/blob/main/manufacturing/releases/pd20-prototype-review/ORDER-SHEET.md)); quantity undecided | Not ordered | No 20 V binary; T1–T8 NOT RUN |
| LED Lamp | P15 r1 + received Board L (LED Lamp section) | P15 from the shared order; 0 new Board L | Two Board L units received 2026-09-19 | Unflashed firmware candidate only; NOT RUN |

**PD20 order readiness.** No D-register item holds the PD20 order
([ledger](https://github.com/Takazudo/zudo-pd/blob/main/manufacturing/prototype-order-readiness.md)): D10–D12 left the
hold list on 2026-11-20 because only an assembled board can close their verification, and D2 left it after the
2026-11-20 review retimed its firing RC (`dec-b20-d2-firing-threshold-band`; RDG12 / RDG5 4.02k 0.1 %, CDG12 / CDG5
27 nF C0G, a value-only field sync). B20 has **294 fitted parts in 88 BOM lines, 268 top and 26 bottom**, so it is a
two-sided assembly. Electrical acceptance is NOT ESTABLISHED. The remaining pre-order items are supplier checks and
the owner's quantity decision.

## P15 r1 shared input module

| Dimension | Recorded state and next gate |
| --- | --- |
| Adopted design/source | Common STUSB4500 15 V / 3 A input for LED first, then PD15; 27 × 40 mm. `boards/board-p15/board-p15-draft.kicad_pcb`, `scripts/schgen/board_p15_spec.py` at the reviewed revision. Same hardware, population and NVM image for both uses |
| Implementation/artifacts | RESET strapped to GND, J2.4 NC; jig owns I2C pull-ups; board pull-downs and local VDD feed/clamp/decoupling implemented. Desk binary `boards/board-p15/nvm/stusb4500-15v.bin`, SHA-256 `76622e14862e53cf318b24eb662f7dc9f34d48134867cf954b30c195c26e8eeb` |
| Recorded checks | [2026-11-03 packet](https://github.com/Takazudo/zudo-pd/blob/dda9ccc/manufacturing/p15-order-decision-packet.md): net parity/CAD screens and fixed-package full verifier PASS, 151/151 checksums with original STEP; manifest base `3b9821b`, source matches at `5a21ab9`. LED enclosure interference PASS is a CAD result, not physical fit |
| Replay limits | Fixed package does not verify later HEAD. Verifier checks the working tree and requires matching historical sources plus the original local-only STEP. Regenerated NVM file is not a physical write/readback |
| Source identity (2026-11-08) | [`boards/board-p15/shared-reference.json`](https://github.com/Takazudo/zudo-pd/blob/main/boards/board-p15/shared-reference.json) records PCB `97acc5f4…`, NVM `76622e14…`, spec, schematic and package BOM/CPL hashes; reviewed commit `6b08236`, LED adoption commit `4a0741f`, frozen package base `3b9821b` as separate fields. `scripts/pcb/board-p15/verify-shared-reference.py --rev <commit>` checks it (in the Python gates). At `6b08236` the frozen source lock is 482/498 unchanged: fabrication files match; the P15 schematic differs only through the `9af3635` passive pin typing. Byte identity only. LED consumer reference: zudo-led-lamp `boards/p15-r1-reference.json` |
| Order/physical state | Plan is **two assembled P15**, reuse two existing Board Ls, then existing Board B. Order-day checklist: [`manufacturing/p15-order-handoff.md`](https://github.com/Takazudo/zudo-pd/blob/main/manufacturing/p15-order-handoff.md). No later executed-order receipt found. No P15 physical programming, acceptance or measurements recorded |
| Remaining gate | All [P15-NVM-1–7](../architecture/board-p15-programming.md) NOT RUN. Current-limited 5 V-only provisioning with both downstream boards disconnected, factory dump/write/readback/full power cycle/configuration check, then NVM-6 on a 20 V-capable test source, still disconnected. Only accepted modules proceed to L or B |

P15 has no hardware voltage window/eFuse after its sink switch. The accepted prototype residual depends on
per-unit NVM acceptance; it is not a measured protection claim. The packet retains cold-knee, communication-current,
hot resistor-derating and other unknowns. Referenced manager `led-p15-compatibility.md` is absent here; the
accessible packet and programming contract support the summary above, not a recovered manager report.

## PD15 P15 plus Board B

| Dimension | Recorded state and next gate |
| --- | --- |
| Adopted design/source | Valid pair **`board-p15 + board-b`**. Board B source: `boards/board-b/board-b.kicad_pcb` and `scripts/schgen/board_b_spec.py` at the reviewed revision. AP63201/LM2596 intermediate rails with LT1963A/adjustable LT3015 outputs |
| Targets | +12 V / 1.2 A, −12 V / 0.8 A, +5 V / 0.5 A; design targets, not measured ratings |
| Implementation/artifacts | Current development B includes later C11/R21/R27 substitutions. It is not identical to received S3 hardware |
| Recorded checks | Fixed P15+B package and conditioned power/layout screens are revision-specific; [order packet](https://github.com/Takazudo/zudo-pd/blob/dda9ccc/manufacturing/p15-order-decision-packet.md), [identity record](https://github.com/Takazudo/zudo-pd/blob/dda9ccc/manufacturing/as-built-and-controller.md) and `manufacturing/power-budget-p15.json` retain their conditions |
| Replay limits | Historical r2+B assembly/leg reports still bind r2. P15 stack requalification needs the original local-only STEP; no new replay is claimed |
| Order/received state | Renewal Board B ordered 2026-09-20 and received. Factory BOM matches S3 `f25194f`; full copper/mask/paste/silk identity, LED2 rotation, usable quantity and D1 inspection are not fully established. PD-specific retired input P was never ordered |
| Programming/measurements | P15 acceptance NOT RUN. LED Board P measurements belong only to those earlier LED units. No PD15 whole-stack measured rating is established |
| Remaining gate | [D1 unpowered inspection](https://github.com/Takazudo/zudo-pd/blob/main/manufacturing/board-b-unpowered-check.md), then [PD15 staged bring-up](../verification/renewal-bring-up.md): startup, low-line, load, ripple, thermal, surge and installed mechanical qualification |

## PD20 Board P r3 plus B20

| Dimension | Recorded state and next gate |
| --- | --- |
| Adopted design/source | Valid pair **`board-p + board-b20-draft`**. Current `boards/board-p/board-p.kicad_pcb` is **20 V r3**, bound to `scripts/schgen/board_p_spec.py`. B20: `boards/board-b20-draft/board-b20-draft.kicad_pcb`; inventory input `scripts/schgen/board_b20_components.py` |
| Input intent | 20 V / 5 A, 5 A e-marked cable, no degraded mode; independent of P15's image and voltage policy |
| Implementation/artifacts | Routed r3; four-layer B20 now a **two-sided assembly**: 294 fitted parts in 88 BOM lines, 268 top and 26 bottom. The 26 bottom parts are the D2 sequenced fast-discharge network (PR 307), with RDG12 / RDG5 4.02k 0.1 % and CDG12 / CDG5 27 nF C0G after the 2026-11-20 firing-threshold retiming. Board P r3 has 44 fitted. P1 contacts are NC, PDOK, GND, NC; PD15 retains ATT |
| Recorded checks | On the 2026-11-20 B20 PCB: pinned KiCad 10.0.6 DRC with refill and schematic parity (0 errors, 0 unconnected, four reviewed `lib_footprint_mismatch` warnings), byte-identical double refill, field-sync verifier, 47-pair STEP-datum proof, pair assembly preview and `verify-jlcpcb.py`. The D2 layout has an [independent review](https://github.com/Takazudo/zudo-pd/blob/main/manufacturing/verification/pd20-native-d2-layout-20261114/review-20261120/README.md). Earlier receipts (269 / 270 / 274 fitted) stay historical in Git |
| Replay limits | Source-locked reports apply to their exact inputs. The cloud runs used the same pinned image instead of the selected Mac. Frozen P15 historical replay remains NOT RUN because the required original STEP is absent. The PD20 package's six upload files pass `scripts/pcb/pd20-order/verify-upload-files.py` (UPLOAD FILE INTEGRITY, 2026-11-20 UTC at `e974d710`), which is not a replay. A new full PD20 replay is NOT RUN: `populated-stack.step` (`59b0e220…`) is local-only and current main differs from the source locks in the PESD24 `routing.json`; the prerequisites are in the [order sheet](https://github.com/Takazudo/zudo-pd/blob/main/manufacturing/releases/pd20-prototype-review/ORDER-SHEET.md). No physical check is claimed |
| NVM | `boards/board-p/nvm/stusb4500-20v-intent.json` is intent only, **no program-ready binary**. TDISPAR0V = 15 at 0xCA[7:4] (`dec-pd20-tdispar0v-15`); its reset interaction stays bench T8. DS12499 Rev 8 answers initial lower-current source matching. POWER_ONLY_ABOVE_5V at 0xE6 bit 3 is confirmed by an official-GUI export pair (`dec-pd20-nvm-power-only-gui`, 2026-11-14), not by readback; established-contract downgrade behavior remains open (T8) |
| Order/physical state | Development hardware; no order/received PD20 units, programming/readback acceptance or measurements recorded |
| Desk load cases (2026-11-08) | `scripts/pcb/board-b20/load_cases.py` binds the current, thermal, loop and power reports to the PD20 contract: continuous 1.7 / 1.6 / 0.3 A, 20 ms transient 2.0 / 1.9 / 0.4 A, let-through maximum 2.1 / 2.0 / 0.5 A (+12 / −12 / +5). The former "rated" 1.2 / 0.8 / 0.5 A case is kept only as the legacy PD15 comparison. At continuous load the desk model gives 4.29–4.79 W board loss and D3 TJ 99.0–120.1 °C at maximum RDS (92.9–111.5 °C at typical RDS). At maximum RDS, the transient held steady gives 113.2–139.7 °C; this is not a 20 ms thermal model. Steady-state desk figures, not transient or measured results ([#230](https://github.com/Takazudo/zudo-pd/issues/230)) |
| Remaining gate | **No pre-order design hold** (readiness ledger, 2026-11-20): D1–D12 each have a disposition, and every open item needs an assembled board or a supplier preview. Before ordering, the owner decides quantity, resolves exact-part supply for the six flagged lines (zero stock: U11, U12, R35; stock below the two-pair need, minimum-purchase or least-patch fields: B20 RVX1, R22/R31, R66 and Board P D5; [re-read 2026-11-20 18:16 UTC](https://github.com/Takazudo/zudo-pd/blob/main/manufacturing/verification/pd20-order-closeout-20261121/README.md)) and checks two-sided assembly, bottom-side rotations and via/stencil handling in the supplier preview using the [order sheet](https://github.com/Takazudo/zudo-pd/blob/main/manufacturing/releases/pd20-prototype-review/ORDER-SHEET.md). D2 switch-threshold residuals (cold PA corner, onset floor), D10 Q1 slew, D11 RDY timing, D12 back-feed, installed thermal margin, header seating and HC11 flat-floor interference, and the NVM reset/downgrade questions move to bench T1–T8, all NOT RUN. Electrical acceptance is NOT ESTABLISHED |

## Owner actions, in order

Each step needs the evidence named; record results here with the unit identity. Software checks do not replace them.

| # | Action | Procedure | Evidence to record |
| --- | --- | --- | --- |
| 1 | Order 2 × P15 r1 from the fixed package; check D5/D9 in the JLC placement preview; re-check stock and cost | [Order handoff](https://github.com/Takazudo/zudo-pd/blob/main/manufacturing/p15-order-handoff.md) | Order date and number, preview screenshots for D5/D9, quoted total |
| 2 | Decide the PD20 quantity and resolve exact-part supply for the six flagged lines (zero stock U11 / U12 INA301A3 and R35; low or below-minimum RVX1, R22/R31, R66 and Board P D5), preferring the exact parts through a JLC pre-order or supplier matching (a substitute needs its own review); run the upload-file integrity check, then quote the PD20 pair with two-sided B20 assembly; check bottom-side rotations and via/stencil details in the preview | [PD20 order sheet](https://github.com/Takazudo/zudo-pd/blob/main/manufacturing/releases/pd20-prototype-review/ORDER-SHEET.md) | Quantity, quote total, preview screenshots |
| 3 | P15 incoming inspection, then per-unit NVM provisioning on a current-limited 5 V-only source with L and B disconnected, then no-load PD acceptance on a source also offering 20 V | [P15-NVM-1–7](../architecture/board-p15-programming.md) | Factory dump, power-cycle readback hash `76622e14…`, contract voltage, VBUS_OUT off at 5 V, per unit |
| 4 | Hand the first accepted P15 to the LED lamp stack | [LED prototype preparation](../led-lamp/prototype-preparation.md) | Board L identity, RS1, firmware identity, startup/current/thermal |
| 5 | Received S3 Board B: D1 unpowered inspection, count and condition | [Board B unpowered check](https://github.com/Takazudo/zudo-pd/blob/main/manufacturing/board-b-unpowered-check.md) | Usable count, LED2 rotation, copper/silk identity |
| 6 | PD15 staged qualification with an accepted P15 | [PD15 staged bring-up](../verification/renewal-bring-up.md) | Startup, low-line, load, ripple, thermal, surge, installed mechanics |
| 7 | PD20 after arrival: review and produce the 20 V image (T4), then T1–T8, including the D2 firing-time and DIS_C measurement in T5 | [PD20 verification](../verification/pd20-verification.md) | Image hash and readback, each T-gate result |

Existing Board B units are not yet inspected or cleared to mate.

## Dated record

These dated entries are kept as written; each describes the state at its date. Where one says a hold remains, the
status table above and the readiness ledger supersede it.

**Addendum 2026-11-08** (integration branch `claude/project-thread-bgdr5q` from main `6b08236`, tracker
[#228](https://github.com/Takazudo/zudo-pd/issues/228)): adds the shared P15 source identity record and order handoff
below, binds the B20 desk reports to the PD20 contract load cases, and lists the owner actions in order. Nothing was
ordered, programmed, energized or measured.

**Execution update 2026-11-10 JST (Mac):** [#234](https://github.com/Takazudo/zudo-pd/pull/234)
and [#239](https://github.com/Takazudo/zudo-pd/pull/239) are merged; current main is
`76f807f11d3b97a9625e8cc9dd6835e235bb99df`. Follow-up native layout, simulation
and manufacturing work is tracked separately in the
[revision and blocker ledger](https://github.com/Takazudo/zudo-pd/blob/main/manufacturing/prototype-order-readiness.md).
The two-P15 local packet is ready; supplier placement preview and current
quotation are pending. PD20 remains on a pre-order hold: fresh adjacent-sample
analysis finds modeled no-load slope/current excursions beyond the adopted
exceptions. Native layout corrections and all 14 actual tracking/re-entry cases
are complete. Final pair assembly passed with source-bound native checks;
a fresh DEVELOPMENT REVIEW export and independent manufacturing verification passed at `3f24a3a` after correcting the first export's strict B20 refill-geometry rejection. No source merge or software check constitutes hardware qualification.

**Cloud update 2026-11-11 UTC (2026-11-12 JST):** four campaign PRs under [#228](https://github.com/Takazudo/zudo-pd/issues/228)
are merged; main after them is `db49cfea495e86ceddb280c675fb1f7dafa1b791`. All are digital tooling, record or
documentation changes; none orders, programs, energizes or measures hardware.

| PR (merge) | What it changed | What it does not establish |
| --- | --- | --- |
| [#244](https://github.com/Takazudo/zudo-pd/pull/244) (`caca8f4`), [#241](https://github.com/Takazudo/zudo-pd/issues/241) | Component-spec CI path filters now include the PD20 and P15 gate inputs (Board P 20 V NVM intent, B20 tests/reports, phase33 regressions, fixed P15 package checks), with an event-aware workflow contract test | Any new circuit result |
| [#245](https://github.com/Takazudo/zudo-pd/pull/245) (`a7f6435`), [#242](https://github.com/Takazudo/zudo-pd/issues/242) | The phase33 refinement analyzer also audits the per-attempt model library and `.spiceinit` copies the solver actually executed; receipt schema and numerical limits unchanged | Electrical acceptance of the recorded cases |
| [#246](https://github.com/Takazudo/zudo-pd/pull/246) (`9b68162`), [#202](https://github.com/Takazudo/zudo-pd/issues/202) | Obsolete `l-bump-version-*` skills removed (retired paths asserted absent); stale P r3 layout wording replaced by the PR #240 R1–R4/artwork dispositions | Closure of R5/R7, process or D1–D9 holds |
| [#247](https://github.com/Takazudo/zudo-pd/pull/247) (`db49cfe`), [#243](https://github.com/Takazudo/zudo-pd/issues/243) | Source-bound [D1–D3 interface diagnostics](https://github.com/Takazudo/zudo-pd/blob/main/manufacturing/sim/board-b20-phase33/interface-diagnostics.md): arithmetic hypotheses bound to the generated B20 schematic and phase33 deck, with the missing inputs named | Simulation, physical qualification or any contract/exception/component change; electrical acceptance stays NOT ESTABLISHED |

Unchanged: PD20 D1–D9 interface/evidence holds, NVM and manufacturing-process holds, every physical gate
(P15-NVM, PD15 bring-up, T1–T8), and the records [#97](https://github.com/Takazudo/zudo-pd/issues/97) (no-auto,
needs-human-verify), [#164](https://github.com/Takazudo/zudo-pd/issues/164), [#185](https://github.com/Takazudo/zudo-pd/issues/185),
[#210](https://github.com/Takazudo/zudo-pd/issues/210), [#218](https://github.com/Takazudo/zudo-pd/issues/218),
[#228](https://github.com/Takazudo/zudo-pd/issues/228), [#231](https://github.com/Takazudo/zudo-pd/issues/231) and
[#235](https://github.com/Takazudo/zudo-pd/issues/235). Issue states have since changed; see the 2026-11-13 reconciliation below.

**Cloud reconciliation 2026-11-13 UTC (2026-11-14 JST)**, [#289](https://github.com/Takazudo/zudo-pd/issues/289),
against main `e868593fd46844982db3e9b730170e56ba00ae77`. It records already-integrated work. Nothing was ordered,
programmed, energized, measured or re-run natively.

| PR (merge) | Integrated | Native receipt, bound to its own execution head |
| --- | --- | --- |
| [#262](https://github.com/Takazudo/zudo-pd/pull/262) (`084580b`) | D11 RRDY 2 × 150k C22807 and its field sync | `manufacturing/verification/pd20-native-d11-20261113/`, head `1a4a954`: STEP datum 45 pairs, assembly preview, development export (270 fitted B20) and independent verification PASS |
| [#264](https://github.com/Takazudo/zudo-pd/pull/264) (`d63467b`) | D10 C36 CL31B105KBHNNNE C1848 and the native Board P rebuild | `pd20-native-d10-merged-20261113/`, head `0dbf462`: the same four steps PASS (270 fitted B20) |
| [#282](https://github.com/Takazudo/zudo-pd/pull/282) (`59ef3b6`) | REF5025 load-regulation budget on the full-range row; interface diagnostics regenerated | Calculation only |
| [#283](https://github.com/Takazudo/zudo-pd/pull/283) (`e868593`) | D12 R77–R80 100k 0402 C25741 inserted natively; input RC recomputed on the routed stray | `pd20-native-d12-insert-20261113/` (insertion; open fill-screen exception accepted by Takazudo) and `pd20-native-d12-merged-20261114/`, head `9435b2f`: the four steps PASS with **274 fitted B20** |

These are nominal CAD and package checks, not electrical qualification. The D12 mitigation is implemented, but
electrical acceptance is not established. The D10 and D12 pre-order holds, D11's open verification and the
D1–D9 holds stay.

- **D12 input capacitance.** The D12 decision assumed a 3 pF stray. The insertion receipt calculated a routed UV5_IN
  upper bound of 3.43 pF, and #283 recomputed the input RC with it: UV+5 is 1.435 µs, and the maximum stays 1.802 µs.
  The method and applicability are in the readiness ledger's reconciliation.
- **D1 artifacts.** The completed OSC-bank and ceiling-corners D1 diagnostic artifacts (runs 43221578569 and
  43232694170) were downloaded and verified against their recorded digests. Their result JSON and audit receipts are
  [retained](https://github.com/Takazudo/zudo-pd/blob/main/manufacturing/sim/board-b20-phase33/d1-diagnostic-audit-20261113.md).
  They judge nothing, most rows are matched-variant, and the pre-registered pinned cross-check was not formed.
  A separate cross-check run on 2026-11-13 (43484213339) closed that gap on the identity pair: the abstol variant is
  COMPARABLE (within 0.001 %) and the rshunt step is NOT COMPARABLE (0.1–0.4 %), which is as large as the D1 exceedances
  ([record](https://github.com/Takazudo/zudo-pd/blob/main/manufacturing/sim/board-b20-phase33/d1-variant-cross-check-20261113.md)).
  A follow-up run (43486530273) shows the −12 V failure is not an rshunt artefact: `adv` at rshunt 1e10 under abstol
  gives 1.474663 V/ms and 265.238 mA, 0.008 % below the recorded values. On 2026-11-14 JST the owner chose the OSC
  contract route for D1 and accepted OSC's conditional exception; no ceiling changes until OSC records it as E21.
  The [OSC reply record](https://github.com/Takazudo/zudo-pd/blob/main/manufacturing/sim/board-b20-phase33/osc-reply-20261114.md)
  also shows condition 3 failing as worded (a monotonic lead of up to 208 mV), passive D2 discharge failing 10 of 18
  per-rail load corners (calculated), and D3 needing a let-through envelope.
  OSC recorded E21 at zudo-osc-hole-field `512e1ec` (PR #337, merged as `39f20ef`): ≤ 350 mA on −12 V and ≤ 180 mA on +5 V inside the
  regions, no load only. The simulated peaks are within it; condition 3 holds only if its "ramp start" is the rail's own
  start ([E21 binding record](https://github.com/Takazudo/zudo-pd/blob/main/manufacturing/sim/board-b20-phase33/e21-binding-20261114.md)).
  Electrical acceptance stays NOT ESTABLISHED, and the proposed 350 / 160 mA exception is not adopted.
  OSC recorded the D3 let-through allowance as E23 at zudo-osc-hole-field `ac48836` (PR #351, merged as `38bcb4a`):
  ≤ 0.25 ms above the maximum, ≤ 130 A peak and ≤ 0.1 A²s per fault event, one event per power cycle. The simulated
  envelope (worst 0.226 ms, 123 A, 0.092 A²s) fits it, so D3 is no longer a pre-order hold; a bench detection-to-off
  measurement and a cable re-run stay open
  ([E23 record](https://github.com/Takazudo/zudo-pd/blob/main/manufacturing/sim/board-b20-phase33/e23-binding-20261114.md)).
  On 2026-11-14 JST the owner adopted the D2 discharge into the B20 schematic (`dec-b20-d2-sequenced-fast-discharge`):
  CSD18543Q3A switches into WSL2512R5000FEA C511023 0.5 Ω loads (three in series on −12 V) and the discrete −12 V
  sequencer with BZT52C3V9-7-F C154917, as simulated PASS (SIM) in 972 corner decks
  ([record](https://github.com/Takazudo/zudo-pd/blob/main/manufacturing/sim/board-b20-phase33/d2-sequencer-circuit-20261114.md)).
  KiCad 10.0.6 ERC reports 0 violations and the exported netlist matches the spec.
  Later on 2026-11-14 JST, under Takazudo's delegation, Claude recorded three desk calls: TDISPAR0V = 15 in the
  Board P r3 20 V NVM intent (`dec-pd20-tdispar0v-15`; 0xCA = 0xFC, desk byte only; the POWER_ONLY_ABOVE_5V map was
  then confirmed at 0xE6 bit 3 by Takazudo's official-GUI export pair, `dec-pd20-nvm-power-only-gui`), typical-curve capacitor evidence accepted as the prototype basis
  (`dec-pd20-installed-capacitor-bounds`, D5) and the Q1/Q3 land/paste kept unchanged for the prototype
  (`dec-pd20-land-paste-prototype`, D8). None of these is a measurement, a programmed part or an order.
  D7 followed the same day (`dec-b20-d7-wsl-pulse-margin`): owner-supplied captures of Vishay's WSL2512 0.5 Ω pulse
  calculator give 0.831 J single-pulse energy at 125 °C, about 59× the largest D2 per-part energy; repetitive
  endurance is not given and stays a residual for bench T5.
  D9 then took the PD15 installation (`dec-pd20-stack-support-prototype`): front face down on the 18 mm printed
  adhesive legs at H4–H7, which nominally clears the HC-11 flat-floor conflict; J5 / JOUT1 seating and the leg fit are
  measured on the first assembled pair.
  The D2 PCB layout followed on 2026-11-14 JST (`dec-b20-d2-back-side-layout`, Claude's call under Takazudo's
  delegation). The six swapped lands and 20 new discharge and sequencer parts are on B.Cu, which faces up when
  installed. B20 is therefore a two-sided assembly. At the published JLC Standard price this adds $33.77 in setup and
  stencil per order. Pulse paths are 1.2 mm B.Cu. Pinned KiCad 10.0.6 DRC with schematic parity gives 0 errors and
  0 unconnected items, with only the four reviewed warnings. Two refills are byte-identical, and the extended insert
  verifier bounds the edit. The reports, STEP datums (47 pairs), pair assembly preview and development export were
  re-derived. See the
  [D2 layout record](https://github.com/Takazudo/zudo-pd/blob/main/manufacturing/verification/pd20-native-d2-layout-20261114/README.md).
  D2 is no longer a pre-order hold, and no D-register item now holds the PD20 order. Bottom-side CPL rotations
  in JLC's placement preview, the WSL repetitive-pulse residual and bench T1–T8 stay open, and nothing is measured.
- **Issues.** #97 and #164 were retired as not planned on 2026-11-14 JST (2026-11-13 UTC); their human acceptance maps to #228 and the
  readiness procedures. #218 was already closed. #185 (cross-context Back sidebar restoration) and #210 (0.3.0 checker
  and Mac bridges) stay open, as do #228, #231, #235 and #279.

**Pre-order closeout 2026-11-20 UTC (2026-11-21 JST)**, [#322](https://github.com/Takazudo/zudo-pd/issues/322), from main `e974d710`. Documentation and read-only tooling only; nothing was uploaded, quoted, ordered, programmed, energized or measured.

- **Upload integrity.** `scripts/pcb/pd20-order/verify-upload-files.py` checks the six PD20 upload files against `SHA256SUMS` and the checksum-verified manifest, pinned to the exported manifest `f430a76a…`: PASS 6/6. `sha256sum -c` gives 158 of 159 because the local-only STEP is absent; full replay is NOT RUN.
- **Polarity source.** `cpl.csv` has no pad data. The order sheet now takes pad 1 from the package PCBs (`scripts/pcb/pd20-order/polarity-reference.py`) and its meaning from the owner pin maps; the frozen `ORDER-NOTES.md` wording is clarified outside its locked bytes.
- **Procedures.** The live PD20 verification page and the `pd20-status.md` T4/T5 sheets now carry the adopted TDISPAR0V = 15 and POWER_ONLY_ABOVE_5V bit 3, and T5 binds the fitted WSL2512R5000FEA C511023 loads and the retimed D2 firing network.
- **Stock.** A JLC re-read of all 99 exact codes at 18:16–18:18 UTC gives the same six flagged lines as the 12:14 UTC snapshot, with identical values (other lines' stock moved). Two lines are at zero stock, and four more fall below the two-pair need, minimum-purchase or least-patch fields ([evidence](https://github.com/Takazudo/zudo-pd/blob/main/manufacturing/verification/pd20-order-closeout-20261121/README.md)). No substitution was made.

**Original 2026-11-05 baseline.** Evidence reviewed on **2026-11-05 JST**, against main `dda9ccc9bfdead8884c354c478280baca641cec1` (PRs [219](https://github.com/Takazudo/zudo-pd/pull/219)–[226](https://github.com/Takazudo/zudo-pd/pull/226) merged).
This page owns current status. [Variant architecture](../architecture/index.mdx) owns design responsibilities;
[release readiness](../architecture/release-readiness.md) owns acceptance gates. A software check, CAD result,
export receipt, order plan, received unit and bench measurement establish different things.

## Historical identity boundaries

Root combined-board v0.4.0, Board A and retired 15 V Board P r2 remain history.
The old `board-p` PCB is retained at [revision 6cb02c8](https://github.com/Takazudo/zudo-pd/blob/6cb02c8/boards/board-p/board-p.kicad_pcb).
The PD-specific input was never physically “as-built.” Earlier physical LED Board P units are distinct from P15
and PD20; their measurements cannot qualify either product. [Board P lineage](../architecture/board-p.md)
provides compatible entry points to the earlier record.
