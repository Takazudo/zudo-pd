---
title: Repository Map
sidebar_position: 3
---

| Path | Responsibility |
| --- | --- |
| `boards/board-p15/board-p15-draft.kicad_pcb` | P15 shared 15 V input layout |
| `boards/board-b/board-b.kicad_pcb` | PD15 development conversion board; distinct from received S3 |
| `boards/board-p/board-p.kicad_pcb` | Current PD20 20 V input r3; retired 15 V r2 is in Git at `6cb02c8` |
| `boards/board-b20-draft/board-b20-draft.kicad_pcb` | Four-layer PD20 conversion board |
| `scripts/schgen/` | Executable specs, B20 inventory projection, decisions and connectivity checks |
| `.claude/skills/component-spec-audit/` | Exact inventory/schema/validation; owner bundles are the evidence authority |
| `.claude/skills/circuit-spec-integration/` | Conditioned cross-component rules and open evidence stages |
| `symbols/`, `footprints/kicad/` | Shared KiCad assets; merge only intended symbols |
| `circuit.config.ts` | Canonical inventory bindings: A/B/P/P15/B20 |
| `circuit/` | Publication policy, checks, [documentation map](https://github.com/Takazudo/zudo-pd/blob/main/circuit/DOCUMENTATION_MAP.md) |
| `doc/src/content/docs/components/` | Generated catalog; never hand-edit |
| `doc/zfb.config.ts` | Supported navigation and category matching |
| [Manufacturing](https://github.com/Takazudo/zudo-pd/blob/main/manufacturing/README.md) | Technical references, dated receipts, research and journals |
| `manufacturing/releases/corner-support-review/` | Fixed P15+B snapshot at base `3b9821b`, not current HEAD or executed order |
| `jlcpcb-order-snapshots/`, root KiCad files | Historical combined-board orders and v0.4.0 |
| `3dp-files/` | Printed adhesive-leg prototype and revision-specific reports |

## Run the documentation locally

```sh
pnpm install --frozen-lockfile
pnpm dev
```

The site runs at `http://localhost:4321`, history at 4322. Use [current procedures](./procedures.mdx) and
`pnpm b4push` for repository verification; these do not program or physically qualify hardware.
