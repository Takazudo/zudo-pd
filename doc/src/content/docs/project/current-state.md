---
title: Current State — P15, PD15 and PD20
sidebar_position: 2
---

Evidence reviewed on **2026-11-05 JST**, against main `dda9ccc9bfdead8884c354c478280baca641cec1` (PRs [219](https://github.com/Takazudo/zudo-pd/pull/219)–[226](https://github.com/Takazudo/zudo-pd/pull/226) merged).
This page owns current status. [Variant architecture](../architecture/index.mdx) owns design responsibilities;
[release readiness](../architecture/release-readiness.md) owns acceptance gates. A software check, CAD result,
export receipt, order plan, received unit and bench measurement establish different things.

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
(P15-NVM, PD15 bring-up, T1–T8), and the open records [#97](https://github.com/Takazudo/zudo-pd/issues/97) (no-auto,
needs-human-verify), [#164](https://github.com/Takazudo/zudo-pd/issues/164), [#185](https://github.com/Takazudo/zudo-pd/issues/185),
[#210](https://github.com/Takazudo/zudo-pd/issues/210), [#218](https://github.com/Takazudo/zudo-pd/issues/218),
[#228](https://github.com/Takazudo/zudo-pd/issues/228), [#231](https://github.com/Takazudo/zudo-pd/issues/231) and
[#235](https://github.com/Takazudo/zudo-pd/issues/235).

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
| Implementation/artifacts | Routed r3; four-layer B20 includes merged review fixes, probe row and C43. Current fitted count **270**, [PR 226](https://github.com/Takazudo/zudo-pd/pull/226) (`ffffa40`) and component projection/model-body record. P1 contacts are NC, PDOK, GND, NC; PD15 retains ATT |
| Recorded checks | [2026-11-04 disposition](https://github.com/Takazudo/zudo-pd/blob/dda9ccc/manufacturing/pd20-status.md) records native DRC/ERC, nominal interference screens and conditioned simulations. Its older **269-component export receipt stays historical**. PR 226 separately records a 270-fitted scratch export and independent-verifier PASS at `ffffa40`; both stay historical. The 2026-11-10 Mac execution adds source-bound native R1–R4/C35 correction, DRC/parity, ERC/netlist and 45-model datum receipts; final pair assembly and export are tracked separately in the execution ledger. [Independent B20 review](https://github.com/Takazudo/zudo-pd/blob/dda9ccc/manufacturing/pd20-b20-layout-review.md) retains original findings; disposition records subsequent fixes |
| Replay limits | Source-locked reports apply to their exact inputs. Fresh corrected native geometry has been checked; the final assembly/render passed with all 63 artifact hashes verified; DEVELOPMENT REVIEW export and independent manufacturing verification passed at clean `3f24a3a`, with exact staged geometry and current datum/assembly proof. Frozen P15 historical replay remains NOT RUN because the required original STEP is absent. No physical check is claimed |
| NVM | `boards/board-p/nvm/stusb4500-20v-intent.json` is intent only, **no program-ready binary**. TDISPAR0V is located at 0xCA[7:4]; value and reset interaction remain open. DS12499 Rev 8 answers initial lower-current source matching. POWER_ONLY_ABOVE_5V mapping conflicts with the ST draft; established-contract downgrade behavior remains open |
| Order/physical state | Development hardware; no order/received PD20 units, programming/readback acceptance or measurements recorded |
| Desk load cases (2026-11-08) | `scripts/pcb/board-b20/load_cases.py` binds the current, thermal, loop and power reports to the PD20 contract: continuous 1.7 / 1.6 / 0.3 A, 20 ms transient 2.0 / 1.9 / 0.4 A, let-through maximum 2.1 / 2.0 / 0.5 A (+12 / −12 / +5). The former "rated" 1.2 / 0.8 / 0.5 A case is kept only as the legacy PD15 comparison. At continuous load the desk model gives 4.29–4.79 W board loss and D3 TJ 99.0–120.1 °C at maximum RDS (92.9–111.5 °C at typical RDS). At maximum RDS, the transient held steady gives 113.2–139.7 °C; this is not a 20 ms thermal model. Steady-state desk figures, not transient or measured results ([#230](https://github.com/Takazudo/zudo-pd/issues/230)) |
| Remaining gate | R1–R4 and C35 geometry corrections have native evidence and independent review; functional probe/polarity artwork is independently reviewed and final pair assembly passed; manufacturing export verification passed at `3f24a3a`. Installed thermal margin, via/stencil process, capacitor bounds and repetitive-pulse evidence remain limited. The Board P Q1 closure slew/inrush and Q1 SOA conclusions are **reopened** (2026-11-11): manufacturer typical DC-bias data puts C36 below its adopted 0.4–1.1 µF range at the start of the 20 V closure; see readiness D10 and [#231](https://github.com/Takazudo/zudo-pd/issues/231). The B20 servo-settle-before-enable screen is also **reopened** (2026-11-11): at R/C tolerance corners the earliest RDY is 0.18864 s against the 0.1919 s project screen; see readiness D11 and [#235](https://github.com/Takazudo/zudo-pd/issues/235). Nominal 11.1 mm stack clearance does not establish header seating tolerance; the 11.0 mm comparison and HC11 flat-floor mounting retain explicit interference findings. Actual startup analysis exposes a modeled exception exceedance; loaded asymmetric discharge, shutdown/re-entry, maximum delivered current and NVM decisions remain pre-order holds. Thermal/EMI measurements and all physical [T1–T8](../verification/pd20-verification.md) are NOT RUN |

## Owner actions, in order

Each step needs the evidence named; record results here with the unit identity. Software checks do not replace them.

| # | Action | Procedure | Evidence to record |
| --- | --- | --- | --- |
| 1 | Order 2 × P15 r1 from the fixed package; check D5/D9 in the JLC placement preview; re-check stock and cost | [Order handoff](https://github.com/Takazudo/zudo-pd/blob/main/manufacturing/p15-order-handoff.md) | Order date and number, preview screenshots for D5/D9, quoted total |
| 2 | Incoming inspection, then per-unit NVM provisioning on a current-limited 5 V-only source with L and B disconnected, then no-load PD acceptance on a source also offering 20 V | [P15-NVM-1–7](../architecture/board-p15-programming.md) | Factory dump, power-cycle readback hash `76622e14…`, contract voltage, VBUS_OUT off at 5 V, per unit |
| 3 | Hand the first accepted P15 to the LED lamp stack | zudo-led-lamp `firmware/board-l/BEFORE-PROGRAMMING-CHECKLIST.md` | Recorded in zudo-led-lamp |
| 4 | Received S3 Board B: D1 unpowered inspection, count and condition | [Board B unpowered check](https://github.com/Takazudo/zudo-pd/blob/main/manufacturing/board-b-unpowered-check.md) | Usable count, LED2 rotation, copper/silk identity |
| 5 | PD15 staged qualification with an accepted P15 | [PD15 staged bring-up](../verification/renewal-bring-up.md) | Startup, low-line, load, ripple, thermal, surge, installed mechanics |
| 6 | PD20: select TDISPAR0V with reset timing reviewed, resolve POWER_ONLY_ABOVE_5V mapping and established-contract transitions before any binary; close the D1–D9 interface/evidence holds in the [prototype-order ledger](https://github.com/Takazudo/zudo-pd/blob/main/manufacturing/prototype-order-readiness.md) (R1–R4 layout corrections are dispositioned; R5/R7 stay with T7/T3), then T1–T8 | [PD20 verification](../verification/pd20-verification.md) | Program-ready image review, then each T-gate result |

Continue the local Mac execution through the linked ledger and
[#228](https://github.com/Takazudo/zudo-pd/issues/228); the original integration PR
has landed. Existing Board B units are not yet inspected or cleared to mate.

## Historical identity boundaries

Root combined-board v0.4.0, Board A and retired 15 V Board P r2 remain history.
The old `board-p` PCB is retained at [revision 6cb02c8](https://github.com/Takazudo/zudo-pd/blob/6cb02c8/boards/board-p/board-p.kicad_pcb).
The PD-specific input was never physically “as-built.” Earlier physical LED Board P units are distinct from P15
and PD20; their measurements cannot qualify either product. [Board P lineage](../architecture/board-p.md)
provides compatible entry points to the earlier record.
