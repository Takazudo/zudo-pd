# KiCad Schematic File Format Reference

Complete reference for KiCad 6+ S-expression schematic format (.kicad_sch).

## File Structure

KiCad uses S-expression (LISP-like) syntax:

```lisp
(element_type
  (property value)
  (nested_element
    (sub_property sub_value)
  )
)
```

All coordinates in millimeters. All angles in degrees.

## Root Schematic

Top-level structure of .kicad_sch file:

```lisp
(kicad_sch
  (version 20250114)
  (generator "eeschema")
  (generator_version "9.0")
  (uuid "c5ce32ac-bd6d-413c-bfb5-5e9e2f8848d1")
  (paper "A4")

  (lib_symbols
    ;; Auto-managed by KiCad - DO NOT EDIT
  )

  ;; Content: junctions, wires, labels, symbols, sheets...

  (sheet_instances
    (path "/" (page "1"))
  )
)
```

Key fields:
- `version`: Format version (20250114 for KiCad 9.0)
- `uuid`: Unique sheet identifier
- `paper`: Page size (A4, A3, Letter, etc.)

## Symbol Instances

Component placement in schematic:

```lisp
(symbol
  (lib_id "library:SymbolName")           ;; Library:SymbolName
  (at 125.73 69.85 270)                   ;; X Y Rotation
  (unit 1)                                ;; Unit number (multi-unit symbols)
  (exclude_from_sim no)
  (in_bom yes)
  (on_board yes)
  (dnp no)                                ;; Do Not Populate
  (fields_autoplaced yes)
  (uuid "1f637e01-4db3-4c99-836b-c91649c236a4")

  ;; Properties
  (property "Reference" "R11"
    (at 130.81 68.58 90)
    (effects (font (size 1.27 1.27)))
  )
  (property "Value" "56k"
    (at 130.81 71.12 90)
    (effects (font (size 1.27 1.27)))
  )
  (property "Footprint" "library:R0603"
    (at 118.11 69.85 0)
    (effects (font (size 1.27 1.27)) (hide yes))
  )
  (property "Datasheet" ""
    (at 125.73 69.85 0)
    (effects (font (size 1.27 1.27)) (hide yes))
  )
  (property "Description" ""
    (at 125.73 69.85 0)
    (effects (font (size 1.27 1.27)) (hide yes))
  )

  ;; Pin UUIDs (for netlist)
  (pin "1" (uuid "eb3fc881-f6b1-41bf-aeac-f2bff7bfed5f"))
  (pin "2" (uuid "5f7daf29-9b22-405d-9cc9-5484f12cd4ca"))

  ;; Instance tracking
  (instances
    (project "project-name"
      (path "/ROOT-UUID/SHEET-UUID"
        (reference "R11")
        (unit 1)
      )
    )
  )
)
```

### Required Properties

- `Reference`: Component designator (R1, C1, U1, etc.)
- `Value`: Component value (10k, 100nF, etc.)
- `Footprint`: PCB footprint reference
- `Datasheet`: (recommended) Datasheet URL or empty
- `Description`: (recommended) Component description or empty

### Rotation Values

- 0: Default orientation (usually horizontal, left-to-right)
- 90: Rotated 90° counter-clockwise
- 180: Rotated 180°
- 270: Rotated 270° counter-clockwise (or 90° clockwise)

### Instance Path Format

Path format: `/ROOT-UUID/SHEET-UUID`
- Root schematic: `/ROOT-UUID`
- Sub-sheet: `/ROOT-UUID/SHEET-UUID`

**Note**: Project name may be empty string `""` or actual project name - copy from existing components.

## Wires and Connections

### Simple Wire

```lisp
(wire
  (pts
    (xy 104.14 30.48)
    (xy 111.76 30.48)
  )
  (stroke (width 0) (type default))
  (uuid "0546fbb4-a53e-49e0-95b5-e5498352e3ee")
)
```

### Stroke Types

- `default`: Solid line
- `dot`: Dotted line
- `dash`: Dashed line

Width 0 = default wire width.

## Labels

### Local Label

Connects nets within same sheet:

```lisp
(label "SIGNAL_NAME"
  (at 100 50 0)                           ;; X Y Angle
  (effects
    (font (size 1.27 1.27))
    (justify left bottom)
  )
  (uuid "...")
)
```

### Global Label

Connects nets across all sheets:

```lisp
(global_label "GLOBAL_NET"
  (shape input)                           ;; input, output, bidirectional, tri_state, passive
  (at 100 50 180)
  (effects
    (font (size 1.27 1.27))
    (justify right)
  )
  (uuid "...")
)
```

### Hierarchical Label

Connects to parent sheet via sheet pin:

```lisp
(hierarchical_label "SIGNAL_OUT"
  (shape input)
  (at 109.22 40.64 180)
  (effects
    (font (size 1.27 1.27))
    (justify right)
  )
  (uuid "a3ee33ca-d5a4-4092-9703-ec1645f50088")
)
```

**Important**: Hierarchical label name must exactly match the pin name in the parent sheet.

### Label Shapes

- `input`: Arrow pointing in
- `output`: Arrow pointing out
- `bidirectional`: Diamond shape
- `tri_state`: Inverted triangle
- `passive`: Rectangle

### Justify Options

- `left`, `right`, `center` (horizontal)
- `top`, `bottom` (vertical)

## Junctions

Connection point where wires cross:

```lisp
(junction
  (at 105.41 64.77)
  (diameter 0)                            ;; 0 = default
  (color 0 0 0 0)                         ;; RGBA
  (uuid "74275667-45b4-41ba-831b-38813d5dda82")
)
```

## Hierarchical Sheets

### Sheet Definition (in parent)

```lisp
(sheet
  (at 33.02 26.67)                        ;; Position
  (size 31.75 24.13)                      ;; Width Height
  (exclude_from_sim no)
  (in_bom yes)
  (on_board yes)
  (dnp no)
  (fields_autoplaced yes)
  (stroke (width 0.1524) (type solid))
  (fill (color 0 0 0 0.0000))
  (uuid "89c28db7-f9d9-4adf-b951-b9bb069eac97")

  (property "Sheetname" "Sub-Sheet Name"
    (at 33.02 25.9584 0)
    (effects (font (size 1.27 1.27)) (justify left bottom))
  )
  (property "Sheetfile" "sub-sheet.kicad_sch"
    (at 33.02 51.4816 0)
    (effects (font (size 1.27 1.27)) (justify left top))
  )

  ;; Sheet pins (interface with parent)
  (pin "GND" input
    (at 33.02 48.26 180)
    (effects (font (size 1.27 1.27)) (justify right))
    (uuid "74c37bc2-be7f-4995-b896-011d8802f8ff")
  )
  (pin "OUTPUT" output
    (at 64.77 35.56 0)
    (effects (font (size 1.27 1.27)) (justify left))
    (uuid "...")
  )

  (instances
    (project "project-name"
      (path "/ROOT-UUID"
        (page "2")
      )
    )
  )
)
```

### Sheet Pin Directions

- `input`: Signal enters sheet
- `output`: Signal exits sheet
- `bidirectional`: Both directions
- `tri_state`: High-impedance capable
- `passive`: No direction

## Power Symbols

Special symbols for power rails (built-in `power:` library):

```lisp
(symbol
  (lib_id "power:GND")
  (at 134.62 53.34 0)
  (unit 1)
  (exclude_from_sim no)
  (in_bom yes)
  (on_board yes)
  (dnp no)
  (fields_autoplaced yes)
  (uuid "0b0521b3-a114-4fdd-9b90-428d265534a8")

  (property "Reference" "#PWR038"         ;; # prefix = power symbol
    (at 134.62 59.69 0)
    (effects (font (size 1.27 1.27)) (hide yes))
  )
  (property "Value" "GND"
    (at 134.62 58.42 0)
    (effects (font (size 1.27 1.27)))
  )

  (pin "1" (uuid "64ef5ae6-634b-4f9f-9671-a6e1a49186cf"))

  (instances
    (project "..."
      (path "/ROOT-UUID/SHEET-UUID"
        (reference "#PWR038")
        (unit 1)
      )
    )
  )
)
```

Common power symbols:
- `power:GND` - Ground
- `power:+5V` - 5V rail
- `power:+12V` - 12V rail
- `power:-12V` - Negative 12V rail
- `power:VCC` - Generic positive supply
- `power:VDD` - Digital positive supply

## Properties and Effects

### Property Structure

```lisp
(property "NAME" "VALUE"
  (at X Y ANGLE)
  (effects
    (font (size WIDTH HEIGHT))
    (justify HORIZONTAL VERTICAL)
    (hide yes)                            ;; Optional: hide property
  )
)
```

### Font Effects

```lisp
(effects
  (font
    (size 1.27 1.27)                      ;; Width Height (default)
    (thickness 0.254)                     ;; Optional: bold text
    (bold yes)                            ;; Optional
    (italic yes)                          ;; Optional
  )
  (justify left bottom)
  (hide yes)
)
```

## Symbol Library Format

Symbol definitions in .kicad_sym files:

```lisp
(kicad_symbol_lib
  (version 20231120)
  (generator "kicad_symbol_editor")
  (generator_version "8.0")

  (symbol "COMPONENT_NAME"
    (exclude_from_sim no)
    (in_bom yes)
    (on_board yes)

    ;; Default properties
    (property "Reference" "R" ...)
    (property "Value" "COMPONENT_NAME" ...)
    (property "Footprint" "..." ...)

    ;; Graphics and pins (may be in same or separate blocks)
    (symbol "COMPONENT_NAME_0_1"
      (rectangle (start -2.54 1.02) (end 2.54 -1.02)
        (stroke (width 0) (type default))
        (fill (type background))
      )
      ;; Pins may be here or in _1_1 block
      (pin passive line
        (at -5.08 0 0)
        (length 2.54)
        (name "1" (effects (font (size 1.27 1.27))))
        (number "1" (effects (font (size 1.27 1.27))))
      )
    )
  )
)
```

### Symbol Naming Convention

`SymbolName_X_Y`:
- X = 0: Body graphics (shared by all units)
- X = 1+: Unit-specific graphics
- Y = 1: Unit number

Example for dual op-amp:
- `OPAMP_0_1`: Body graphics
- `OPAMP_1_1`: Unit 1 pins
- `OPAMP_2_1`: Unit 2 pins

### Pin Types

- `input`: Input pin
- `output`: Output pin
- `bidirectional`: Bidirectional
- `tri_state`: High-Z capable
- `passive`: Passive component (resistors, capacitors)
- `power_in`: Power input
- `power_out`: Power output
- `unconnected`: No connect
- `free`: Unspecified

### Pin Styles

- `line`: Standard line
- `inverted`: With bubble (NOT)
- `clock`: With clock edge
- `inverted_clock`: Bubble + clock
- `input_low`: Active low input
- `output_low`: Active low output

## UUID Format

Standard 36-character UUID:
```
xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
```

- Lowercase hexadecimal (0-9, a-f)
- 8-4-4-4-12 grouping
- Must be unique within file

Example: `c5ce32ac-bd6d-413c-bfb5-5e9e2f8848d1`

Quick fix for new UUID: Copy existing UUID, change last 4-8 characters.
