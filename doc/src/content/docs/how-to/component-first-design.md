---
title: Component-First Design Workflow
sidebar_position: 1
---

Start a part change in `.claude/skills/component-spec-audit/SKILL.md` and its
`references/new-component-workflow.md`. The inventory connects an exact MPN and
LCSC code to an owner record, schematic placements and KiCad assets.

## Record evidence before placing a part

1. Resolve the exact orderable and manufacturer. Keep candidates separate from
   fitted inventory lines.
2. Read sources, facts, conditions, pin map, interactions and coverage. Preserve
   unavailable evidence explicitly when an exact source cannot be obtained.
3. Check symbol pins against footprint pads and the manufacturer's package drawing.
   A catalog footprint or model does not independently prove pin identity.
4. Update the schematic spec and affected integration rules together. Capture DNP
   per placement and retain replaced-part evidence as history.
5. Regenerate schematics, previews and catalog. Review electrical and mechanical
   consequences before changing the PCB.

## Validate records and generated schematics

Run from the repository root:

```sh
python3 .claude/skills/component-spec-audit/scripts/validate.py --strict
python3 -m unittest discover -s .claude/skills/component-spec-audit/scripts -p 'test_*.py'
python3 .claude/skills/circuit-spec-integration/scripts/check_forward_tests.py --strict
python3 scripts/schgen/gen_schematic.py scripts/schgen/board_p_spec.py
python3 scripts/schgen/gen_schematic.py board_a_spec
python3 scripts/schgen/gen_schematic.py board_b_spec
```

See `scripts/schgen/README.md` for complete regeneration and ERC commands. Edit
Python specs for generated schematics, not their `.kicad_sch` output files.

## Publish the human reference

Run from `doc/`:

```sh
pnpm generate:models
pnpm generate:components
pnpm b4push
```

When footprint geometry changes, also regenerate SVG previews using the documented
KiCad toolchain (`pnpm generate:footprint-previews`). Offline checks detect stale
previews but cannot create them.

The [catalog](/docs/components/catalog/) publishes unresolved domains alongside
facts. Publishing a component page does not close its open design questions.
