# V196 shared Board P candidate — provenance (UNADOPTED)

**Status:** isolated, unadopted engineering candidate. Unvalidated draft. Not canonical
Board P (`boards/board-p/` is the historical STUSB4500 board ordered 2026-09-19).
Not order-ready; no fabrication or assembly output exists or may be generated from
this directory without a separate explicit approval.

## Identity

| Item | Value |
| --- | --- |
| Candidate | V196 "isolated coordinated J1 fanout candidate" |
| Function | HUSB238_006DD 15 V-only PD sink → TPS259474L eFuse → shared 6-pin output; TPS3701 RAW voltage monitor |
| Source commit (local provenance only) | `ef0178d04fb4e614806702c0b35404fcc57feee2` — owner-side local commit; **not on GitHub**, no Git ancestry imported |
| PCB `board-p-COUT1206-TRIAL.kicad_pcb` | SHA256 `c191997b3b34856076bc89df435684de5cd15f7636d6e2a216cc7652f4c02ad2` |
| Schematic `board-p-COUT1206-TRIAL.kicad_sch` | SHA256 `16375e410046f8c11b5e40fa0c74647fcd4dde9e44632d123236b3ad620aee25` |
| Project `board-p-COUT1206-TRIAL.kicad_pro` | SHA256 `ecd79b11e0fe3f2ba49b88046e6c4ccb996e5dfb98655d5308121cf6801cc4ef` (89 bytes, metadata only — no design rules) |
| BOM `BOM-TRIAL.csv` | SHA256 `57e58a4c54a4674622e0db9607723c49be7f6eecc4acad0c09df9fa3cf1cda34` |
| Baseline | V148 PCB SHA256 `ec1207594aaf67c510168e95a84886554283ef2409aa33d58decdb5686caa6d1` (not imported; retained in the handoff archive) |
| Inert follow-up | V197 `124b97d73f4beebbc0c293440e35f7e79eea63ee` (local) — UNAPPLIED exact-feature rule text; **not imported, not active** |
| Content | 27 footprints / 106 pads (25 BOM placements + MH1/MH2 NPTH), 18 named nets + net 0, 281 segments, 67 vias, 0 zones |

Transfer archive: `led/V196-isolated-J1-fanout-candidate.zip`, 1,062,071 bytes,
SHA256 `7008e9307952419edc85d0029e543170706d66ef2711c445169a9cc46bd9b238`
(inside handoff `claude-circuit-handoff-20261031`). All 22 files of
`candidate-UNADOPTED/` were copied byte-for-byte and re-verified against the archive's
`MANIFEST.json` (22/22 SHA256+size match). The original basename is kept so KiCad
library lookups behave as in the source run.

## Missing from this import

| Missing | Effect |
| --- | --- |
| 3D models: 4 library-footprint references to 3 WRL files | Reconciled below; the PCB itself embeds **no** `(model …)` entries, so its 3D view is model-less regardless |
| Full HUSB238 Rev2.5 manufacturer PDF (historical SHA256 `d4dabfe5e6055ec72f14dd2f4ae8f913be80822c14d2d24f910ea4bb777c002a`) | Only retained excerpts (pp4–9 text, p13 outline references) exist in the source packet; U1 land remains an engineered draft, not a manufacturer land pattern |
| V159–V163 startup / hot-SW2 closure assessment | Not transferred; AP63203 EN/UVLO/startup guarantees remain unavailable. Do not infer content from version labels |
| GCT USB4105 STEP and B4 drawing | Retained only as hashes/images in the handoff `primary-evidence/`; not imported |
| Exact J1 orderable | `BOM-TRIAL.csv` row J1 has no MPN/LCSC; CAD evidence names USB4105-GF-A but uses USB4105-15-A geometry (plating-only family bridge, not accepted) |

### 3D model reconciliation (identity only)

The four references are in project-local library footprints
(`zudo-led-lamp.pretty/R0603`, `C0603`, `HDR-TH_6P-P2.54-V-M`, and
`rmh2-candidate.pretty/RMH2_…`), all pointing to
`${KIPRJMOD}/../../footprints/kicad/zudo-led-lamp.3dshapes/`. From this directory that
resolves to the repository's existing models:

| Model | Repo git blob (main `2ab3b5cd`) | Blob in retained candidate-baseline tree `1fc399e2` | Repo SHA256 |
| --- | --- | --- | --- |
| `R0603.wrl` (2 refs) | `7de3c5ac2782ed37d377e68b5c9009b263834e05` | same | `2a125409502d8eb68f2e196ab1c28b180e0918830445364f93a45d9461b4daad` |
| `C0603_L1.6-W0.8-H0.8.wrl` | `b48d1e30e68f3221f976e993500086521b815efc` | same | `125791465c37d0e6cda3b2f45f84e01af226d81a462bfbecb7a4513327e9f22a` |
| `HDR-TH_6P-P2.54-M-LI-1X6P.wrl` | `adbe67bb6960041553995481aa50d345fdc2b3af` | same | `7598d387ea6611b225e6873936fa7289067a2965d4a9a8fa4be5f0790713a522` |

The three local `zudo-led-lamp.pretty` footprints are byte-identical to the repo's
`footprints/kicad/zudo-led-lamp.pretty/` copies. This is file identity only: it is
**not** a mechanical-fit, envelope, or assembly qualification, and no model exists for
U1, U2, UMON, QINH, RBLEED, CSLEW, COUT (1206) or J1.

## Native verification

See [`DRC-CLASSIFICATION.md`](DRC-CLASSIFICATION.md). Summary: pinned KiCad 10.0.6
no-fill DRC reproduces the original 22 findings exactly (exit 5) — regression-equal
to V148, **not DRC PASS**.

## Rules for this directory

- Do not move these files into `boards/` or regenerate canonical outputs from them.
- Do not copy the V197 UNAPPLIED rule text into an active `.kicad_dru` without the
  explicit approval described in `DRC-CLASSIFICATION.md`.
- Any PCB change makes a new candidate revision with new hashes; keep this one intact.
