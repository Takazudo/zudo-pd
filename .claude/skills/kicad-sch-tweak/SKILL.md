---
name: kicad-sch-tweak
description: Edit and create KiCad schematic (.kicad_sch) files. Use when user says "edit schematic", "modify kicad", "add component", "change resistor value", "update schematic", or similar. Capabilities: (1) Modify existing schematics (change values, add/remove components, update connections), (2) Create new schematic content from specifications or ASCII diagrams, (3) Analyze schematic file structure. Works with KiCad 6+ S-expression format. Can generate draft schematics that may need layout adjustment in KiCad GUI.
---

# KiCad Schematic Editor

Edit KiCad 6+ schematic files (.kicad_sch) using S-expression text format.

## Quick Reference

- **Format docs**: See [references/kicad-sch-format.md](references/kicad-sch-format.md) for complete S-expression syntax

## Workflow

### 1. Safety Check & Discover Project

Before editing, always:

1. **Verify file is version-controlled**: Run `git status` to confirm changes can be reverted
2. **Read the target .kicad_sch file** to understand current structure
3. **Find symbol libraries**: Read `sym-lib-table` for available symbol library names
4. **Find available symbols**: Read the project's `.kicad_sym` file(s) referenced in sym-lib-table
5. **Get sheet UUIDs**: Read root `.kicad_sch` for sheet hierarchy and UUIDs

### 2. Understand User Request

Clarify with user if needed:
- Which components to add/modify/remove
- Component values (resistance, capacitance, etc.)
- Connection requirements (what connects to what)
- For new circuits: reference documentation or ASCII diagram

### 3. Make Edits

Use the Edit tool for targeted changes. **Always copy patterns from existing components in the same file.**

**Change component value:**
```lisp
(property "Value" "10k"   ;; Change to new value
```

**Add new component:** Copy existing symbol block from same file, then update:
- `uuid` (generate new unique UUID)
- `(at X Y rotation)` coordinates
- `(property "Reference" "R99"` - next available designator
- `(property "Value" "..."` - component value
- Pin UUIDs (generate new unique ones)
- Instance path (copy from similar component, update reference)

**Add wire:**
```lisp
(wire
  (pts (xy X1 Y1) (xy X2 Y2))
  (stroke (width 0) (type default))
  (uuid "a1b2c3d4-e5f6-7890-abcd-ef1234567890")
)
```

**Add net label:**
```lisp
(label "SIGNAL_NAME"
  (at X Y rotation)
  (effects (font (size 1.27 1.27)) (justify left bottom))
  (uuid "a1b2c3d4-e5f6-7890-abcd-ef1234567890")
)
```

### 4. Validate

After editing:
- Ensure all UUIDs are unique (36-char format, lowercase hex: `a1b2c3d4-e5f6-7890-abcd-ef1234567890`)
- Check S-expression syntax (balanced parentheses)
- Verify library references exist (`lib_id` matches library in sym-lib-table)
- **Suggest user open in KiCad** to visually verify - Claude cannot confirm connectivity
- **For complex edits**: Recommend running KiCad ERC (Electrical Rules Check)

## Project Discovery

For any KiCad project, find these key files:

| File | Purpose | Key Info |
|------|---------|----------|
| `*.kicad_pro` | Project config | Project name, settings |
| `sym-lib-table` | Symbol libraries | Library names and paths |
| `fp-lib-table` | Footprint libraries | Footprint library names |
| Root `.kicad_sch` | Main schematic | Sheet UUIDs, hierarchy |
| `*.kicad_sym` | Symbol definitions | Available component symbols |

**Get library prefix**: Read `sym-lib-table` to find `(name "...")` - use as `lib_id` prefix (e.g., `"mylib:ComponentName"`).

**Get sheet UUID**: Read root schematic's `(uuid "...")` field for root UUID. For sub-sheets, find `(sheet ... (uuid "..."))` blocks.

## Symbol Template

Copy from existing component in same file, or use this minimal template:

```lisp
(symbol
  (lib_id "LIBRARY:SYMBOL_NAME")
  (at X Y ROTATION)
  (unit 1)
  (exclude_from_sim no)
  (in_bom yes)
  (on_board yes)
  (dnp no)
  (fields_autoplaced yes)
  (uuid "UNIQUE-UUID-HERE")
  (property "Reference" "R1" (at X Y 0) (effects (font (size 1.27 1.27))))
  (property "Value" "10k" (at X Y 0) (effects (font (size 1.27 1.27))))
  (property "Footprint" "LIBRARY:FOOTPRINT" (at X Y 0) (effects (font (size 1.27 1.27)) (hide yes)))
  (property "Datasheet" "" (at X Y 0) (effects (font (size 1.27 1.27)) (hide yes)))
  (property "Description" "" (at X Y 0) (effects (font (size 1.27 1.27)) (hide yes)))
  (pin "1" (uuid "PIN1-UUID"))
  (pin "2" (uuid "PIN2-UUID"))
  (instances
    (project "PROJECT_NAME_OR_EMPTY"
      (path "/ROOT-UUID/SHEET-UUID" (reference "R1") (unit 1))
    )
  )
)
```

**Notes**:
- `PROJECT_NAME_OR_EMPTY`: Check existing components - may be `""` or project name
- `ROTATION`: 0, 90, 180, or 270 degrees
- Pin count varies by component - check symbol definition

## Power Symbols

Use built-in `power:` library:

```lisp
(symbol
  (lib_id "power:GND")
  (at X Y 0)
  (unit 1)
  (exclude_from_sim no)
  (in_bom yes)
  (on_board yes)
  (dnp no)
  (fields_autoplaced yes)
  (uuid "UNIQUE-UUID")
  (property "Reference" "#PWR01" (at X Y 0) (effects (font (size 1.27 1.27)) (hide yes)))
  (property "Value" "GND" (at X Y 0) (effects (font (size 1.27 1.27))))
  (pin "1" (uuid "PIN-UUID"))
  (instances
    (project "..."
      (path "/..." (reference "#PWR01") (unit 1))
    )
  )
)
```

Common power symbols: `power:GND`, `power:+5V`, `power:+12V`, `power:-12V`, `power:VCC`, `power:VDD`

## Coordinate System

- Origin: top-left of page
- Units: millimeters
- Rotation: degrees (0, 90, 180, 270)
- Grid: 2.54mm (0.1 inch) typical spacing
- **Tip**: Look at nearby components for reasonable coordinates

## Reference Designators

| Prefix | Component |
|--------|-----------|
| R | Resistors |
| C | Capacitors |
| L | Inductors |
| D | Diodes |
| U | ICs/Modules |
| J | Connectors |
| TP | Test points |
| F | Fuses |
| #PWR | Power symbols (hidden) |

## Limitations

- **Layout quality**: Components placed programmatically may overlap. User adjusts in KiCad GUI.
- **Wire routing**: Prefer net labels over complex wire routing for drafts.
- **Pin positions**: Estimated from symbol definitions; may need adjustment.
- **lib_symbols section**: Do NOT edit - KiCad auto-manages this section.

## Error Recovery

If schematic won't open in KiCad:

**Parenthesis mismatch**: Check line-by-line for missing `)`. Common: deleted symbol block with dangling reference.

**Invalid UUID**: Must be exactly 36 chars, lowercase hex (0-9, a-f). Quick fix: copy existing UUID and change last 4 digits.

**Missing lib_id**: Symbol not in library. Check project's `.kicad_sym` files for available symbols.

**Revert changes**:
```bash
git checkout -- path/to/file.kicad_sch
```

**Required properties**: Reference, Value, Footprint (Datasheet and Description recommended).
