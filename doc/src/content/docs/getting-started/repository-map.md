---
title: Repository Map
sidebar_position: 3
---

| Path | Responsibility |
| --- | --- |
| `boards/` | Independent KiCad board projects |
| `scripts/schgen/` | Generated schematic specs, locked decisions and connectivity checks |
| `.claude/skills/component-spec-audit/` | Exact component inventory, schema and validation |
| `.claude/skills/component-*/` | Evidence bundles for parts and owned subordinate records |
| `.claude/skills/circuit-spec-integration/` | Cross-component rules and open validation domains |
| `symbols/`, `footprints/kicad/` | Canonical symbols, footprints and models |
| `doc/component-docs/` | Component catalog and preview generation |
| `doc/src/content/docs/` | Current documentation and historical references |
| [Manufacturing guide](https://github.com/Takazudo/zudo-pd/blob/main/manufacturing/README.md) | Fabrication stack, assembly scope and qualification limits |
| [Corner-support review destination](https://github.com/Takazudo/zudo-pd/tree/main/manufacturing/releases/corner-support-review) | Current prototype export destination and reports; native PCB layout and power-path checks pass |
| `boards/board-b/supports/` | Retained HC-11 drawing and the earlier 11 mm support's height conflict |
| `jlcpcb-order-snapshots/` | Historical as-ordered files |
| Root `zudo-pd.kicad_*` and sheet files | Historical v0.4.0 combined-board project |
| [Printed accessories](https://github.com/Takazudo/zudo-pd/blob/main/3dp-files/README.md) | Current 18 mm adhesive-leg prototype |

## Run the documentation locally

```sh
cd doc
pnpm install
pnpm dev
```

The site runs at `http://localhost:4321`. A component watcher regenerates the catalog
when source evidence changes; the history service runs on port 4322.

Use `pnpm b4push` for documentation checks. Hardware checks are separate; see the
[component-first workflow](../how-to/component-first-design.md).
