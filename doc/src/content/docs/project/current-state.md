---
title: Current State — P15, PD15 and PD20
sidebar_position: 2
---

Evidence reviewed on **2026-11-05 JST**, against main `dda9ccc9bfdead8884c354c478280baca641cec1` (PRs [219](https://github.com/Takazudo/zudo-pd/pull/219)–[226](https://github.com/Takazudo/zudo-pd/pull/226) merged).
This page owns current status. [Variant architecture](../architecture/index.mdx) owns design responsibilities;
[release readiness](../architecture/release-readiness.md) owns acceptance gates. A software check, CAD result,
export receipt, order plan, received unit and bench measurement establish different things.

## P15 r1 shared input module

| Dimension | Recorded state and next gate |
| --- | --- |
| Adopted design/source | Common STUSB4500 15 V / 3 A input for LED first, then PD15; 27 × 40 mm. `boards/board-p15/board-p15-draft.kicad_pcb`, `scripts/schgen/board_p15_spec.py` at the reviewed revision. Same hardware, population and NVM image for both uses |
| Implementation/artifacts | RESET strapped to GND, J2.4 NC; jig owns I2C pull-ups; board pull-downs and local VDD feed/clamp/decoupling implemented. Desk binary `boards/board-p15/nvm/stusb4500-15v.bin`, SHA-256 `76622e14862e53cf318b24eb662f7dc9f34d48134867cf954b30c195c26e8eeb` |
| Recorded checks | [2026-11-03 packet](https://github.com/Takazudo/zudo-pd/blob/dda9ccc/manufacturing/p15-order-decision-packet.md): net parity/CAD screens and fixed-package full verifier PASS, 151/151 checksums with original STEP; manifest base `3b9821b`, source matches at `5a21ab9`. LED enclosure interference PASS is a CAD result, not physical fit |
| Replay limits | Fixed package does not verify later HEAD. Verifier checks the working tree and requires matching historical sources plus the original local-only STEP. Regenerated NVM file is not a physical write/readback |
| Order/physical state | Plan is **two assembled P15**, reuse two existing Board Ls, then existing Board B. No later executed-order receipt found. No P15 physical programming, acceptance or measurements recorded |
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
| Recorded checks | [2026-11-04 disposition](https://github.com/Takazudo/zudo-pd/blob/dda9ccc/manufacturing/pd20-status.md) records native DRC/ERC, nominal interference screens and conditioned simulations. Its older **269-component export receipt stays historical**. PR 226 separately records a 270-fitted scratch export and independent-verifier PASS at `ffffa40`; neither is a new export/replay by this documentation session. [Independent B20 review](https://github.com/Takazudo/zudo-pd/blob/dda9ccc/manufacturing/pd20-b20-layout-review.md) retains original findings; disposition records subsequent fixes |
| Replay limits | Source-locked reports apply to their revisions; no new export or physical check is claimed by this documentation work |
| NVM | `boards/board-p/nvm/stusb4500-20v-intent.json` is intent only, **no program-ready binary**. TDISPAR0V encoding unavailable; lower-current 20 V source behavior unresolved |
| Order/physical state | Development hardware; no order/received PD20 units, programming/readback acceptance or measurements recorded |
| Remaining gate | Independent P r3 review; component evidence and pulse/SOA gaps; thermal/EMI, sequencing, let-through and [T1–T8](../verification/pd20-verification.md) all NOT RUN |

## Historical identity boundaries

Root combined-board v0.4.0, Board A and retired 15 V Board P r2 remain history.
The old `board-p` PCB is retained at [revision 6cb02c8](https://github.com/Takazudo/zudo-pd/blob/6cb02c8/boards/board-p/board-p.kicad_pcb).
The PD-specific input was never physically “as-built.” Earlier physical LED Board P units are distinct from P15
and PD20; their measurements cannot qualify either product. [Board P lineage](../architecture/board-p.md)
provides compatible entry points to the earlier record.
