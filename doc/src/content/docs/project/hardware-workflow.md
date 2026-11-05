---
title: Current Hardware Workflow
sidebar_position: 2
---

Start with [current state](./current-state.md), the [variant design](../architecture/index.mdx) and
[release gates](../architecture/release-readiness.md). Record the exact revision and pair before changing hardware.
This procedure describes future authorized hardware work; documentation maintenance alone does not authorize it.

## Establish source ownership

| Stream | Layout | Schematic source |
| --- | --- | --- |
| P15 / PD15 input | `boards/board-p15/board-p15-draft.kicad_pcb` | `scripts/schgen/board_p15_spec.py` |
| PD15 conversion | `boards/board-b/board-b.kicad_pcb` | `scripts/schgen/board_b_spec.py` |
| PD20 input | `boards/board-p/board-p.kicad_pcb` | `scripts/schgen/board_p_spec.py` |
| PD20 conversion | `boards/board-b20-draft/board-b20-draft.kicad_pcb` | `scripts/schgen/board_b20_spec.py`; inventory uses `board_b20_components.py` |

Read `circuit/WORKFLOW.md`, the component audit and integration owner instructions. Run `pnpm circuit:check`
before editing and inspect SCOPE/SKIP output. Resolve each exact identity through the inventory, not archived BOMs.

## Generate only the intended schematic

The generator accepts a `.py` path or importable module name and supports `--help`. For example, when a P15
connectivity change is authorized, from the root:

```sh
python3 scripts/schgen/gen_schematic.py --help
python3 scripts/schgen/gen_schematic.py scripts/schgen/board_p15_spec.py
python3 scripts/schgen/verify_geometry.py scripts/schgen/board_p15_spec.py boards/board-p15/board-p15.kicad_sch
```

Edit executable definitions, not generated schematics. Keep spec/output parity. Use `scripts/schgen/README.md`
for baseline, decisions, native ERC/netlist verification and availability limits. PCB layouts have separate owners;
generation does not review routing, copper capacity, protection, thermal paths or mechanics.

## Validate and maintain the narrative

Run `pnpm b4push` as its complete guarded sequence. The pure-Python regeneration gate covers **A/B/P/P15**;
the inventory provider has **five inputs A/B/P/P15/B20**, with B20 projected by `board_b20_components.py`.
Native CAD/export/physical verification remains revision-specific and separate from documentation checks.

When a decision changes, update the affected variant design page, [current state](./current-state.md) with dated
evidence, and [release readiness](../architecture/release-readiness.md) if acceptance criteria change. Update the
[documentation map](https://github.com/Takazudo/zudo-pd/blob/main/circuit/DOCUMENTATION_MAP.md) for ownership changes.
Use [component assets](./component-assets.md) for imports and [package preparation](./jlcpcb-package.md) for exports.
