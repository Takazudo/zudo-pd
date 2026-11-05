# Documentation ownership and migration map

Inventory refreshed 2026-11-05 JST against main `dda9ccc9bfdead8884c354c478280baca641cec1` before edits:
203 site Markdown/MDX pages = 132 generated component pages + 71 authored pages; 24 top-level manufacturing Markdown
files. These are **dated migration observations**, not permanent corpus locks. Use `git ls-files`, configured inventory,
publication selection and generated preflight when refreshing. The tables include new current pages in this migration.

## Canonical owners and maintenance rule

| Concern | Owner | Update when |
| --- | --- | --- |
| Dated implementation/artifact/check/replay/order/received/programmed/measured state | `doc/src/content/docs/project/current-state.md` | A design decision, artifact, receipt or actual verification changes that dimension |
| Stable P15 / PD15 / PD20 source mapping, design responsibilities and interfaces | `architecture/p15-shared-input.md`, `pd15.md`, `pd20.md` | Adopted design/interface/source identity changes |
| Acceptance criteria | `architecture/release-readiness.md` | A per-stream acceptance gate changes |
| Current procedures | `project/hardware-workflow.md`, `component-assets.md`, `jlcpcb-package.md`; P15 programming and per-stream verification | Executable command, evidence or acceptance procedure changes |
| Decision chronology / research | `decisions/index.mdx`, `research/index.mdx` | Adoption/supersession or candidate status changes |
| Site navigation | `doc/zfb.config.ts` | Reading structure changes; preserve categoryMatch for every exposed category and landing children |
| Migration ownership | This map | A document is added, split, reclassified or no longer recommended |

Entry READMEs link owners instead of copying running ledgers. All authored documentation, diagrams and labels are English.
P15 is a shared 15 V module; PD15 = P15+B; PD20 = current P r3+B20. The word “Board P” without a variant is insufficient.

## Reference and byte-preservation rules

Before edits, the full tracked checkout was scanned for path/basename links, SHA-256 source locks and heading locators.
The migration keeps all pre-existing authored routes and heading fragments. Ordinary links are maintained; new indexes
curate current recommendations instead of blanket CategoryNav. Historical pages can still appear in sidebars.

- Current evidence references: owner bundles, inventory, rules, decisions, publication data and generated evidence remain unchanged.
  No source hash is silently re-pinned. Referenced manager `common-controller-block.md`, `led-p15-compatibility.md` and
  `osc-pd-interface-20v.md` are absent here; accessible summaries support only their recorded contracts.
- Historical source/heading constraints: `circuit/tests/compatibility-baseline.json`, the three archived-heading baselines and
  runtime/component evidence anchors are retained unchanged. `overview/`, `inbox/`, `learning/`, `misc/` and already explicitly
  historical project/verification procedures retain original source bytes and URLs.
- Fixed manufacturing source locks: `manufacturing/releases/corner-support-review/manifest.json`, board export-validation
  reports and all package artifacts remain unchanged. Its older `manufacturing/README.md` hash is historical and may differ
  from this current guide. Manifest base `3b9821b`, matching sources at `5a21ab9`, original STEP and 151/151/full-verifier PASS
  retain their historical meaning. Replay compares against the working tree and needs matching historical bytes plus original STEP.
- Current source receipt lock: `boards/board-b20-draft/assembly-preview/README.md` has a stale “no top-edge pogo row” sentence
  but is source-hash-locked by its `verification.json`. Retain it as receipt-associated source, do not re-pin; current disposition
  is `manufacturing/pd20-status.md`, current design `architecture/pd20.md`.
- Other board/support/assembly/printed-leg READMEs bound by source manifests remain revision-specific; nominal CAD does not
  become current hardware qualification. The documentation does not replay, regenerate or replace these artifacts.
- Executable specs/generators remain unchanged. Historical docstrings in `board_p_spec.py`, `board_p15_spec.py` and related
  builders may use earlier “as-built”/draft identities; executable nets/placements plus revision-specific records establish
  identity. Five inventory inputs A/B/P/P15/B20 differ from four A/B/P/P15 schematic regeneration gates.

## Authored site inventory

Paths in this table are relative to `doc/src/content/docs/`. Public routes remain under `/docs/`.
“Retain bytes” means the existing body is untouched. All existing headings are compatibility constraints unless a specific
historical destination is noted. Generated component families are inventoried separately below.

| Path / public route | Purpose / stream | Classification | Authority / canonical replacement | Action / inbound constraints |
| --- | --- | --- | --- | --- |
| `architecture/board-contract.md`<br>`/docs/architecture/board-contract/` | Board Roles and Interface / P15/PD15/PD20 | Current | Exact evidence/specs; current-state status; variant design; release gates | Update/curate; retain route and existing fragments; inbound `#independent-corner-supports`, `#seven-top-edge-contacts` |
| `architecture/board-p-lineage-history.md`<br>`/docs/architecture/board-p-lineage-history/` | Board P Lineage — Superseded Development Record / P15/PD15/PD20 | Historical development | `architecture/board-p.md`, P15/PD20 pages | Split; preserve prior source body verbatim, explicitly superseded |
| `architecture/board-p.md`<br>`/docs/architecture/board-p/` | Board P — Variants and Lineage / P15/PD15/PD20 | Current | Exact evidence/specs; current-state status; variant design; release gates | Refactor lineage; keep every old heading with scoped destination |
| `architecture/board-p15-programming.md`<br>`/docs/architecture/board-p15-programming/` | Board P15 NVM Programming / P15 | Procedure | Exact evidence/specs; current-state status; variant design; release gates | Update/curate; retain route and existing fragments |
| `architecture/component-map.md`<br>`/docs/architecture/component-map/` | Component Map / P15/PD15/PD20 | Current | PD15 executable spec + exact owner evidence; PD20 page for B20 | Update/curate; retain route and existing fragments |
| `architecture/index.mdx`<br>`/docs/architecture/` | Current Architecture / P15/PD15/PD20 | Current | Exact evidence/specs; current-state status; variant design; release gates | Update/curate; retain route and existing fragments |
| `architecture/p15-shared-input.md`<br>`/docs/architecture/p15-shared-input/` | P15 r1 Shared Input Module / P15 | Current | Exact evidence/specs; current-state status; variant design; release gates | Create current owner |
| `architecture/pd15.md`<br>`/docs/architecture/pd15/` | PD15 — P15 plus Board B / P15/PD15/PD20 | Current | Exact evidence/specs; current-state status; variant design; release gates | Create current owner |
| `architecture/pd20.md`<br>`/docs/architecture/pd20/` | PD20 — Board P r3 plus B20 / PD20 | Current | Exact evidence/specs; current-state status; variant design; release gates | Create current owner |
| `architecture/positive-pre-regulator.md`<br>`/docs/architecture/positive-pre-regulator/` | Positive Pre-Regulator / PD15 | Current | PD15 executable spec + exact owner evidence; PD20 page for B20 | Update/curate; retain route and existing fragments |
| `architecture/power-stage-options.md`<br>`/docs/architecture/power-stage-options/` | Renewed Power Stage / PD15 | Current | PD15 executable spec + exact owner evidence; PD20 page for B20 | Update/curate; retain route and existing fragments |
| `architecture/release-readiness.md`<br>`/docs/architecture/release-readiness/` | Release Readiness / P15/PD15/PD20 | Current | Exact evidence/specs; current-state status; variant design; release gates | Update/curate; retain route and existing fragments |
| `archive/index.mdx`<br>`/docs/archive/` | Historical Design Archive / P15/PD15/PD20 | Current | Historical categories at existing URLs | Retain bytes; navigation adds dedicated Archive group |
| `decisions/index.mdx`<br>`/docs/decisions/` | Decisions Register / P15/PD15/PD20 | Current | Exact evidence/specs; current-state status; variant design; release gates | Update/curate; retain route and existing fragments |
| `inbox/board-b-architecture-review.md`<br>`/docs/inbox/board-b-architecture-review/` | Board B Architecture Review (DC-DC + LDO + Output) / Historical | Historical | Current-state / variant pages; original record owns historical evidence | Retain bytes and URL; demote from current recommendations; inbound `#89` |
| `inbox/board-split-decision.md`<br>`/docs/inbox/board-split-decision/` | Board Split Decision — Fix List + A/B Interface Contract / Historical | Historical | Current-state / variant pages; original record owns historical evidence | Retain bytes and URL; demote from current recommendations; inbound `#86`, `#90`, `#93`, `#decision-set-b-`, `#decision-set-c-` |
| `inbox/current-status.md`<br>`/docs/inbox/current-status/` | Project Status and Plan / Historical | Historical | Current-state / variant pages; original record owns historical evidence | Retain bytes and URL; demote from current recommendations; inbound `#failure-history-v1-` |
| `inbox/index.mdx`<br>`/docs/inbox/` | INBOX / Historical | Historical | Current-state / variant pages; original record owns historical evidence | Retain bytes and URL; demote from current recommendations |
| `inbox/nvm-programming.md`<br>`/docs/inbox/nvm-programming/` | STUSB4500 NVM Programming Setup / Historical | Historical | Current-state / variant pages; original record owns historical evidence | Retain bytes and URL; demote from current recommendations; inbound `#src-umw-ao3401a-c347476-datasheet` |
| `inbox/pcba-v1-debug.md`<br>`/docs/inbox/pcba-v1-debug/` | PCBA v1 Debug Report / Historical | Historical | Current-state / variant pages; original record owns historical evidence | Retain bytes and URL; demote from current recommendations |
| `inbox/pcba-v2-debug.md`<br>`/docs/inbox/pcba-v2-debug/` | PCBA v2 Debug Report — STUSB4500 CC1DB Failure / Historical | Historical | Current-state / variant pages; original record owns historical evidence | Retain bytes and URL; demote from current recommendations |
| `inbox/spec-architecture-review.md`<br>`/docs/inbox/spec-architecture-review/` | Spec Architecture Review / Historical | Historical | Current-state / variant pages; original record owns historical evidence | Retain bytes and URL; demote from current recommendations; inbound `#171`, `#src-c22387780-boardbdoc`, `#src-c696190-primary` |
| `inbox/stusb4500-pinout.md`<br>`/docs/inbox/stusb4500-pinout/` | STUSB4500 Pin Cheat-Sheet (beginner) / Historical | Historical | Current-state / variant pages; original record owns historical evidence | Retain bytes and URL; demote from current recommendations |
| `inbox/v3-bringup-test-procedure.md`<br>`/docs/inbox/v3-bringup-test-procedure/` | v3 Bring-Up & Test Procedure / Historical | Historical | Current-state / variant pages; original record owns historical evidence | Retain bytes and URL; demote from current recommendations |
| `inbox/v3-pd-failure-diagnosis.md`<br>`/docs/inbox/v3-pd-failure-diagnosis/` | v3 USB-PD Failure Diagnosis (pin 18 root cause) / Historical | Historical | Current-state / variant pages; original record owns historical evidence | Retain bytes and URL; demote from current recommendations |
| `inbox/v4-asbuilt-audit.md`<br>`/docs/inbox/v4-asbuilt-audit/` | v4 As-Built Order Verification & Footprint Geometry Audit / Historical | Historical | Current-state / variant pages; original record owns historical evidence | Retain bytes and URL; demote from current recommendations; inbound `#87`, `#88` |
| `inbox/v4-pd-failure-diagnosis.md`<br>`/docs/inbox/v4-pd-failure-diagnosis/` | v4 USB-PD Failure Diagnosis (front-end datasheet review) / Historical | Historical | Current-state / variant pages; original record owns historical evidence | Retain bytes and URL; demote from current recommendations; inbound `#87`, `#bench-discrimination-procedure-dead-v4-boards-cheapest-first` |
| `inbox/versioning.md`<br>`/docs/inbox/versioning/` | Versioning Scheme (X.Y.Z) / Historical | Historical | Current-state / variant pages; original record owns historical evidence | Retain bytes and URL; demote from current recommendations |
| `inbox/wave-7-3d-model-coverage.md`<br>`/docs/inbox/wave-7-3d-model-coverage/` | Wave 7 — 3D Package Model Coverage / Historical | Historical | Current-state / variant pages; original record owns historical evidence | Retain bytes and URL; demote from current recommendations |
| `learning/ai-circuit-design-research.md`<br>`/docs/learning/ai-circuit-design-research/` | "AI-Assisted Circuit Design: Workflows for the Idea → KiCad Schematic Handoff" / Historical | Historical | Current-state / variant pages; original record owns historical evidence | Retain bytes and URL; demote from current recommendations |
| `learning/buck-converter-feedback.md`<br>`/docs/learning/buck-converter-feedback/` | "How Buck Converters Work: Feedback Control Explained" / Historical | Historical | Current-state / variant pages; original record owns historical evidence | Retain bytes and URL; demote from current recommendations |
| `learning/ch224d-usb-pd-controller.md`<br>`/docs/learning/ch224d-usb-pd-controller/` | CH224D USB PD Sink Controller / Historical | Historical | Current-state / variant pages; original record owns historical evidence | Retain bytes and URL; demote from current recommendations |
| `learning/esd-protection-tvs-diodes.md`<br>`/docs/learning/esd-protection-tvs-diodes/` | "ESD Protection: How TVS Diodes Save Your Circuit" / Historical | Historical | Current-state / variant pages; original record owns historical evidence | Retain bytes and URL; demote from current recommendations |
| `learning/eurorack-power-distribution.md`<br>`/docs/learning/eurorack-power-distribution/` | Eurorack Power Distribution Best Practices / Historical | Historical | Current-state / variant pages; original record owns historical evidence | Retain bytes and URL; demote from current recommendations |
| `learning/gnd-component-placement.md`<br>`/docs/learning/gnd-component-placement/` | GND and Component Placement Strategy / Historical | Historical | Current-state / variant pages; original record owns historical evidence | Retain bytes and URL; demote from current recommendations |
| `learning/gndd-gnda-split-ground.md`<br>`/docs/learning/gndd-gnda-split-ground/` | GNDD/GNDA Split Ground Design / Historical | Historical | Current-state / variant pages; original record owns historical evidence | Retain bytes and URL; demote from current recommendations |
| `learning/index.mdx`<br>`/docs/learning/` | Learning Notes / Historical | Historical | Current-state / variant pages; original record owns historical evidence | Retain bytes and URL; demote from current recommendations |
| `learning/inductor-voltage-reversal.md`<br>`/docs/learning/inductor-voltage-reversal/` | Inductor Voltage Reversal and Negative Voltage Generation / Historical | Historical | Current-state / variant pages; original record owns historical evidence | Retain bytes and URL; demote from current recommendations |
| `learning/linear-regulator-capacitors.md`<br>`/docs/learning/linear-regulator-capacitors/` | Linear Regulator Capacitor Selection / Historical | Historical | Current-state / variant pages; original record owns historical evidence | Retain bytes and URL; demote from current recommendations |
| `learning/open-drain-pg-pin.md`<br>`/docs/learning/open-drain-pg-pin/` | "Open-Drain Outputs: Understanding the PG Pin" / Historical | Historical | Current-state / variant pages; original record owns historical evidence | Retain bytes and URL; demote from current recommendations |
| `learning/p-channel-mosfet-load-switch.md`<br>`/docs/learning/p-channel-mosfet-load-switch/` | "P-Channel MOSFET Load Switch: Gate Control Explained" / Historical | Historical | Current-state / variant pages; original record owns historical evidence | Retain bytes and URL; demote from current recommendations |
| `learning/pcb-layout-power-circuits.md`<br>`/docs/learning/pcb-layout-power-circuits/` | PCB Layout Guidelines for Power Circuits / Historical | Historical | Current-state / variant pages; original record owns historical evidence | Retain bytes and URL; demote from current recommendations |
| `learning/protection-fuse-strategy.md`<br>`/docs/learning/protection-fuse-strategy/` | "Protection Fuse Strategy: Multi-Stage Design" / Historical | Historical | Current-state / variant pages; original record owns historical evidence | Retain bytes and URL; demote from current recommendations |
| `learning/trace-width-copper-weight.md`<br>`/docs/learning/trace-width-copper-weight/` | PCB Trace Width and Copper Weight / Historical | Historical | Current-state / variant pages; original record owns historical evidence | Retain bytes and URL; demote from current recommendations |
| `learning/transformer-polarity-flyback.md`<br>`/docs/learning/transformer-polarity-flyback/` | "Transformer Polarity & Phasing: Why Direction Matters in Flyback Converters" / Historical | Historical | Current-state / variant pages; original record owns historical evidence | Retain bytes and URL; demote from current recommendations |
| `learning/two-stage-dc-dc-ldo-architecture.md`<br>`/docs/learning/two-stage-dc-dc-ldo-architecture/` | Two-Stage DC-DC + LDO Power Supply Architecture for Low-Noise Audio / Historical | Historical | Current-state / variant pages; original record owns historical evidence | Retain bytes and URL; demote from current recommendations |
| `learning/usb-pd-vs-traditional-usb.md`<br>`/docs/learning/usb-pd-vs-traditional-usb/` | "USB-PD vs Traditional USB: Why Power Hubs Don't Exist" / Historical | Historical | Current-state / variant pages; original record owns historical evidence | Retain bytes and URL; demote from current recommendations |
| `learning/usb-type-c-pinout.md`<br>`/docs/learning/usb-type-c-pinout/` | USB Type-C Pinout and Power Delivery / Historical | Historical | Current-state / variant pages; original record owns historical evidence | Retain bytes and URL; demote from current recommendations |
| `misc/index.mdx`<br>`/docs/misc/` | Misc / Historical | Historical | Current-state / variant pages; original record owns historical evidence | Retain bytes and URL; demote from current recommendations |
| `overview/board-a-usb-pd-core.md`<br>`/docs/overview/board-a-usb-pd-core/` | Board A — USB-PD Core / Historical | Historical | Current-state / variant pages; original record owns historical evidence | Retain bytes and URL; demote from current recommendations; inbound `#90`, `#a`, `#component-list-lcsc-parts-and-rough-cost`, `#component-list-lcsc-parts-and-rough-cost-j1-substitution-options`, `#deltas-vs-the-current-single-board-circuit` |
| `overview/board-b-synth-power.md`<br>`/docs/overview/board-b-synth-power/` | Board B — Synth Power Conversion / Historical | Historical | Current-state / variant pages; original record owns historical evidence | Retain bytes and URL; demote from current recommendations; inbound `#117`, `#136`, `#171`, `#90`, `#93` |
| `overview/bom.md`<br>`/docs/overview/bom/` | Bill of Materials (BOM) / Historical | Historical | Current-state / variant pages; original record owns historical evidence | Retain bytes and URL; demote from current recommendations; inbound `#jlcpcb-assembly-cost-structure`, `#x` |
| `overview/circuit-diagrams.mdx`<br>`/docs/overview/circuit-diagrams/` | Circuit Diagrams / Historical | Historical | Current-state / variant pages; original record owns historical evidence | Retain bytes and URL; demote from current recommendations; inbound `#dc-dc-conversion-stage`, `#diagram2-usb-pd-15v-`, `#diagram3-15v-`, `#diagram4-15v-`, `#diagram5-13-5v-` |
| `overview/index.mdx`<br>`/docs/overview/` | Overview / Historical | Historical | Current-state / variant pages; original record owns historical evidence | Retain bytes and URL; demote from current recommendations |
| `overview/mechanical-design.md`<br>`/docs/overview/mechanical-design/` | Mechanical Design / Historical | Historical | Current-state / variant pages; original record owns historical evidence | Retain bytes and URL; demote from current recommendations |
| `overview/overview.md`<br>`/docs/overview/overview/` | Project Overview / Historical | Historical | Current-state / variant pages; original record owns historical evidence | Retain bytes and URL; demote from current recommendations |
| `overview/two-board-plan.md`<br>`/docs/overview/two-board-plan/` | Two-Board Plan (USB-PD Core + Synth Power) / Historical | Historical | Current-state / variant pages; original record owns historical evidence | Retain bytes and URL; demote from current recommendations |
| `overview/usb-pd-adapter.md`<br>`/docs/overview/usb-pd-adapter/` | USB-PD AC Adapter / Historical | Historical | Current-state / variant pages; original record owns historical evidence | Retain bytes and URL; demote from current recommendations; inbound `#multi-case-setup-multiple-zudo-pd-units` |
| `project/component-assets.md`<br>`/docs/project/component-assets/` | Current Component Asset Procedure / P15/PD15/PD20 | Procedure | Exact evidence/specs; current-state status; variant design; release gates | Create current owner |
| `project/component-first-design.md`<br>`/docs/project/component-first-design/` | Component-First Design Workflow / P15/PD15/PD20 | Procedure | Exact evidence/specs; current-state status; variant design; release gates | Update/curate; retain route and existing fragments |
| `project/current-state.md`<br>`/docs/project/current-state/` | Current State — P15, PD15 and PD20 / P15/PD15/PD20 | Current | Exact evidence/specs; current-state status; variant design; release gates | Create current owner |
| `project/dcdc-converter-design.md`<br>`/docs/project/dcdc-converter-design/` | DC-DC Converter Stage Design (LM2596S-ADJ) / Historical | Historical procedure | Current-state / variant pages; original record owns historical evidence | Retain bytes and URL; demote from current recommendations |
| `project/hardware-workflow.md`<br>`/docs/project/hardware-workflow/` | Current Hardware Workflow / P15/PD15/PD20 | Procedure | Exact evidence/specs; current-state status; variant design; release gates | Create current owner |
| `project/index.mdx`<br>`/docs/project/` | Start Here / P15/PD15/PD20 | Current | Exact evidence/specs; current-state status; variant design; release gates | Update/curate; retain route and existing fragments |
| `project/jlcpcb-package.md`<br>`/docs/project/jlcpcb-package/` | JLCPCB Package Preparation / P15/PD15/PD20 | Procedure | Exact evidence/specs; current-state status; variant design; release gates | Update/curate; retain route and existing fragments |
| `project/kicad-jlcpcb-tools.md`<br>`/docs/project/kicad-jlcpcb-tools/` | Generate JLCPCB Files with kicad-jlcpcb-tools / Historical | Historical procedure | Current-state / variant pages; original record owns historical evidence | Retain bytes and URL; demote from current recommendations |
| `project/kicad-parts-download.md`<br>`/docs/project/kicad-parts-download/` | Download KiCad Footprints and Symbols / P15/PD15/PD20 | Historical procedure | `project/hardware-workflow.md`, `component-assets.md` | Demote; add scope banner only; original body/anchors retained |
| `project/kicad-workflow.md`<br>`/docs/project/kicad-workflow/` | KiCad Project Workflow / P15/PD15/PD20 | Historical procedure | `project/hardware-workflow.md`, `component-assets.md` | Demote; add scope banner only; original body/anchors retained |
| `project/linear-regulator-layout.md`<br>`/docs/project/linear-regulator-layout/` | Linear Regulator PCB Layout and Thermal Design / Historical | Historical procedure | Current-state / variant pages; original record owns historical evidence | Retain bytes and URL; demote from current recommendations; inbound `#terminal-functions`, `#thermal-budget` |
| `project/net-table-convention.md`<br>`/docs/project/net-table-convention/` | Net-Table + Mermaid Convention / Historical | Historical procedure | Current-state / variant pages; original record owns historical evidence | Retain bytes and URL; demote from current recommendations |
| `project/procedures.mdx`<br>`/docs/project/procedures/` | Design and Verification Workflows / P15/PD15/PD20 | Procedure | Exact evidence/specs; current-state status; variant design; release gates | Update/curate; retain route and existing fragments |
| `project/project-brief.md`<br>`/docs/project/project-brief/` | Project Brief / P15/PD15/PD20 | Current | Exact evidence/specs; current-state status; variant design; release gates | Update/curate; retain route and existing fragments |
| `project/repository-map.md`<br>`/docs/project/repository-map/` | Repository Map / P15/PD15/PD20 | Current | Exact evidence/specs; current-state status; variant design; release gates | Update/curate; retain route and existing fragments |
| `research/index.mdx`<br>`/docs/research/` | Research and Candidate Comparisons / P15/PD15/PD20 | Research | Exact evidence/specs; current-state status; variant design; release gates | Update/curate; retain route and existing fragments |
| `verification/index.mdx`<br>`/docs/verification/` | Verification / P15/PD15/PD20 | Procedure | Exact evidence/specs; current-state status; variant design; release gates | Update/curate; retain route and existing fragments |
| `verification/pd20-verification.md`<br>`/docs/verification/pd20-verification/` | PD20 Verification — Blocked NVM and T1–T8 / PD20 | Procedure | Exact evidence/specs; current-state status; variant design; release gates | Create current owner |
| `verification/power-rail-bench-test.md`<br>`/docs/verification/power-rail-bench-test/` | Power Rail Bench Test Procedure / Historical | Historical procedure | Current-state / variant pages; original record owns historical evidence | Retain bytes and URL; demote from current recommendations |
| `verification/regulator-assembly-and-inspection.md`<br>`/docs/verification/regulator-assembly-and-inspection/` | Regulator Assembly, Soldering, and Inspection / Historical | Historical procedure | Current-state / variant pages; original record owns historical evidence | Retain bytes and URL; demote from current recommendations |
| `verification/renewal-bring-up.md`<br>`/docs/verification/renewal-bring-up/` | PD15 Renewal Prototype Bring-Up / PD15 | Procedure | Exact evidence/specs; current-state status; variant design; release gates | Update/curate; retain route and existing fragments |

## Generated family — retain all bytes and evidence anchors

| Path / route family | Purpose and stream | Classification / authority | Action / constraints |
| --- | --- | --- | --- |
| `doc/src/content/docs/components/**` / `/docs/components/**` (132 pages at baseline) | Catalog, inventory placements, source/fact and integration views across A/B/P/P15/B20 | Generated current/historical exact evidence, not physical acceptance; owner bundles + inventory + rules + publication selection | Retain generated bytes/anchors; no manual edits or publication changes |
| `circuit/generated/preflight.json`, `doc/public/assets/component-previews/**` | Generated counts, selected SVG/WRL previews | Generated projection of configured evidence/assets | Retain bytes, hashes, exclusions/allowlists and scanner contracts |

## Manufacturing narrative inventory

All paths below are under `manufacturing/` and have repository URLs, not authored site routes.
Long journals remain in source; site indexes link their disposition rather than copying them wholesale.

| Path | Purpose / stream | Classification | Canonical authority / action / constraints |
| --- | --- | --- | --- |
| `README.md` | Fabrication review package | Current technical/reference guidance | Update entry/export guidance; older bytes remain source-locked in fixed package, never re-pin |
| `as-built-and-controller.md` | As-built identity, LED Board P bring-up findings and PD controller options (research) | Revision-specific verification/order-decision record | Correct/add scope above chronology; retain dated decisions, results and existing headings |
| `b1-gates.md` | B1 gate screens: ripple, voltage bands, loss, transient path and input clamp | Research/candidate comparison | Retain dated body, heading/locator/revision boundary; current-state and variant/gate owners for present interpretation |
| `board-b-20v-switcher-direct-draft.md` | Board B 20 V switcher-direct draft (unvalidated paper draft) | Historical development journal | Correct/add scope above chronology; retain dated decisions, results and existing headings |
| `board-b-protection-20v.md` | Board B protection concept at 20 V input: interface limiter, reverse blocking, all-rail shutdown and NVM (draft) | Research/candidate comparison | Retain dated body, heading/locator/revision boundary; current-state and variant/gate owners for present interpretation |
| `board-b-unpowered-check.md` | Board B unpowered visual and continuity check (D1 plan, not authorized) | Current technical/reference guidance | Retain dated body, heading/locator/revision boundary; current-state and variant/gate owners for present interpretation |
| `design-gaps-20v.md` | Design gaps for any 20 V input option | Research/candidate comparison | Retain dated body, heading/locator/revision boundary; current-state and variant/gate owners for present interpretation |
| `heat-spreader-concept.md` | Aluminum heat-spreader concept for Board B (screen) | Research/candidate comparison | Retain dated body, heading/locator/revision boundary; current-state and variant/gate owners for present interpretation |
| `input-clamp-fix.md` | Board P input clamp vs the STUSB4500 absolute maximum: fix proposal (screen) | Research/candidate comparison | Retain dated body, heading/locator/revision boundary; current-state and variant/gate owners for present interpretation |
| `input-protection-20v.md` | 20 V input protection for Board P: clamp vs STUSB4500 limits (L7 screen) | Research/candidate comparison | Correct/add scope above chronology; retain dated decisions, results and existing headings |
| `multiport-chargers.md` | Multiport chargers: Anker A2683 screen | Research/candidate comparison | Retain dated body, heading/locator/revision boundary; current-state and variant/gate owners for present interpretation |
| `osc-supply-options.md` | OSC supply options: comparison for a later user decision | Research/candidate comparison | Retain dated body, heading/locator/revision boundary; current-state and variant/gate owners for present interpretation |
| `p15-order-decision-packet.md` | P15 r1 first prototype order: decision packet (2026-11-03) | Revision-specific verification/order-decision record | Retain dated body, heading/locator/revision boundary; current-state and variant/gate owners for present interpretation |
| `package-notes-b20.md` | Package notes: Board P r3 (board-p) + Board B 20 V switcher-direct draft (board-b20-draft) | Current technical/reference guidance | Retain dated body, heading/locator/revision boundary; current-state and variant/gate owners for present interpretation |
| `package-notes-p15.md` | Package notes: Board P 15 V (board-p15) + Board B | Current technical/reference guidance | Retain bytes; fixed-package source locks; current manufacturing guide qualifies old path meaning |
| `pd-ab-readiness.md` | PD A/B readiness matrix: Board P r3 + B20 (unvalidated drafts) | Historical development journal | Correct/add scope above chronology; retain dated decisions, results and existing headings |
| `pd20-b20-layout-review.md` | B20 draft layout: independent review of hot loops, Kelvin sensing, returns and D3 heat | Revision-specific verification/order-decision record | Retain original findings/bytes; link later disposition in pd20-status.md |
| `pd20-status.md` | PD20 status: Board P r3 + B20 (20 V / 5 A pair) | Current technical/reference guidance | Retain dated 269-component export receipt; current-state separately cites PR 226/current 270 |
| `power-budget.md` | Renewal power-chain screening | Revision-specific verification/order-decision record | Retain bytes; fixed-package source locks; current manufacturing guide qualifies old path meaning |
| `power-limit-60w.md` | 60 W-class input with a usage limit (screen) | Research/candidate comparison | Retain dated body, heading/locator/revision boundary; current-state and variant/gate owners for present interpretation |
| `product-comparison.md` | Product comparison: current model vs a 60 W-input-class model (screen) | Research/candidate comparison | Retain dated body, heading/locator/revision boundary; current-state and variant/gate owners for present interpretation |
| `product-lineup.md` | Product lineup screen (PD-003) | Research/candidate comparison | Correct/add scope above chronology; retain dated decisions, results and existing headings |
| `supply-alternatives.md` | Supply alternatives for the OSC demand | Research/candidate comparison | Retain dated body, heading/locator/revision boundary; current-state and variant/gate owners for present interpretation |
| `supply-capability.md` | Supply-capability screen | Research/candidate comparison | Retain dated body, heading/locator/revision boundary; current-state and variant/gate owners for present interpretation |

## Repository, board and developer entry points

| Path/family | Purpose / stream | Classification / authority | Action / constraints |
| --- | --- | --- | --- |
| `readme.md` | Short repository entry, all streams | Current; links canonical current-state/design/gates | Update; retain entry headings |
| `AGENTS.md` | Agent routing | Procedure; circuit/WORKFLOW and evidence instructions | Retain bytes |
| `CLAUDE.md` | Hardware overview, evidence/storage rules | Current/procedure | Reconcile factual overview; preserve safety/publication/storage rules |
| `boards/README.md`, `boards/board-p/README.md`, `boards/board-p15/README.md` | Active variant source entry points | Current/procedure; executable sources + revision records | Update P r3/P15 identity; qualify P15 chronology's retired r2 “as-built” terminology |
| `boards/board-b/{artwork,routing,supports,assembly-preview,assembly-preview-p15}/README.md` | Revision-specific PD15 geometry, artwork and preview records | Historical/revision-specific technical evidence | Retain source-hash-locked bytes and locators; current docs explain replay limits |
| `boards/board-b20-draft/assembly-preview/README.md` | Nominal PD20 stack preview | Receipt-associated technical record | Retain source lock; stale pogo sentence superseded by PD20 disposition (see reference rules) |
| Root and board KiCad/symbol/footprint/model files | Hardware sources and historical artifacts | Executable/evidence authority | Unchanged; no redesign or regenerated hardware |
| `scripts/schgen/README.md` | Generator CLI, scope and verification | Procedure; executable CLI and run-python-gates | Update factual source identity/four-generator scope; source Python unchanged |
| `scripts/pcb/**`, `footprints/scripts/**`, `scripts/schgen/**` Python docstrings | Executable generation/export/verifier contracts | Procedure/reference | Retain Python; historical wording is not physical evidence; use current procedures |
| `circuit/WORKFLOW.md`, `circuit/ARCHITECTURE.md` | Canonical agent/evidence/developer contract | Procedure/current reference; config/inventory/preflight | Reconcile five inventory inputs versus four generation gates, nav and maintenance owners |
| `doc/README.md`, `doc/CLAUDE.md` | Site development/authoring entry | Procedure/current reference | Update nav, ownership and corpus-count policy |
| `doc/SCAFFOLD.md`, `ZUDO_DEPS_PINS.md`, `patches/README.md` | Imported framework/package provenance | Revision-specific technical reference | Retain; dependency versions, patches and scanner contracts unchanged |
| `circuit/templates/README.md`, `circuit/agent-task-examples.md`, `circuit/templates/project-docs/**` | Unpublished request/document examples | Procedure templates, not live-page claims | Qualify README/example language and owner routing; preserve raw-skill publication exclusions |
| `circuit/checks/README.md`, `circuit/cad-receipts/**` | Check scope and acquisition receipts | Technical/procedure/record | Retain; commands and receipts keep actual scope |
| `.claude/skills/**` | Exact component/integration evidence and instructions | Evidence authority, not public authored pages | Retain bytes and all IDs/hashes; never copy raw skills to assets |
| `jlcpcb-order-snapshots/**`, root KiCad project | Earlier combined-board orders | Historical evidence | Retain bytes, URLs and order identity |
| `manufacturing/releases/corner-support-review/**` | Fixed P15+B package and internal guides | Revision-specific export/verification evidence, not an order | Retain all package bytes/checksums/source locks; no replay in this task |
| `manufacturing/readiness/**`, `manufacturing/sim/**`, `manufacturing/*.json` | Dated cost, stock, calculation, simulation and source locks | Revision-specific machine evidence | Retain bytes and dates; no freshness or physical-test inference |
| `3dp-files/**`, `footprints/**/README.md`, `diagram-sources/**` | Mechanical/model/artwork reference | Revision-specific technical evidence | Retain locked sources/physical limits; no regenerated artifacts |

## Migration verification receipt

The final focused receipt is [documentation-migration-verification.md](documentation-migration-verification.md).
It records actual checks, preserved routes/fragments and desktop/mobile navigation results separately from hardware evidence.
