---
sidebar_position: 4
---

# Create Circuit SVG Files for Documentation

This guide explains how to create professional circuit diagrams using schemdraw and integrate them into the documentation.

## Overview

Circuit diagrams are generated using the schemdraw Python library with a systematic workflow that ensures electrical accuracy and visual clarity.

## Prerequisites

- Python 3.7 or later
- schemdraw library installed (`pip install schemdraw`)
- `/schemdraw-circuit-generator` skill configured

## Design Workflow

### Step 1: Collect Parts Data

Use the `/jlcpcb` skill to search for and verify component availability:

```bash
# Example: Search for buck converter
/jlcpcb LM2596S
```

Document:
- Part numbers
- Specifications (voltage ratings, current ratings, package types)
- JLCPCB stock codes
- Key specifications (resistance, capacitance, inductance, etc.)

### Step 2: Create ASCII Art Draft

Start with ASCII art circuit diagram in markdown code blocks. This serves as the specification for the final diagram.

**Example:**

```
+15V ─────┬─── L1: 100µH ──┬─── D1 ──┬─── C3: 470µF ──┬─→ +13.5V
          │    (4.5A)      │   SS34  │    (25V)       │
          │                │    ↓    │                │
          │           ┌────┴─────────┴──┐             │
          │           │5  VIN      OUT │4────────────┤
          └───────────┤3  ON        FB │2─────┬──────┘
                      │1  GND          │      │
                      └────────────────┘      │
                              │               │
                             GND          ┌───┴───┐
                                          │ R1    │ 10kΩ
                                          │ 10kΩ  │
                                          └───┬───┘
                                          ┌───┴───┐
                                          │ R2    │ 1kΩ
                                          │ 1kΩ   │
                                          └───┬───┘
                                              │
                                             GND
```

**Create Connection List:**

```
Connections:
- +15V input → U2 (LM2596S) pin 5 (VIN)
- +15V input → C5 (100µF) → GND
- U2 pin 3 (ON) → +15V (always enabled)
- U2 pin 4 (VOUT) → Switching node
- Switching node → L1 (100µH) → +13.5V Output
- Switching node → D1 (SS34 cathode)
- D1 (SS34 anode) → GND
- +13.5V → C3 (470µF) → GND
- U2 pin 2 (FB) → R1 (10kΩ) → Tap
- Tap → R2 (1kΩ) → GND
- Tap → +13.5V (feedback sense)
- U2 pin 1 (GND) → GND
```

### Step 3: Generate Schemdraw Diagram

Use the `/schemdraw-circuit-generator` skill to create professional circuit diagram:

```bash
/schemdraw-circuit-generator
```

Provide the connection list from Step 2 as the specification.

**Configuration:**
- **Theme**: Black foreground with transparent background (default)
- **Font**: Arial, 11pt
- **Color**: Black lines and text
- **Background**: Transparent (allows container background to show through)

**Example Python Code:**

```python
#!/usr/bin/env python3
"""
LM2596S-ADJ Buck Converter: +15V → +13.5V
Complete circuit with transparent background, black foreground, Arial font
"""

import schemdraw
from schemdraw import elements as elm

with schemdraw.Drawing(
    font='Arial',         # Sans-serif font
    fontsize=11,
    color='black',        # Foreground: black
    transparent=True      # Transparent background
) as d:
    d.config(unit=3)

    # IC definition
    ic = elm.Ic(
        pins=[
            elm.IcPin(name='GND', pin='3', side='left', slot='1/3'),
            elm.IcPin(name='ON', pin='5', side='left', slot='2/3'),
            elm.IcPin(name='VIN', pin='1', side='left', slot='3/3'),
            elm.IcPin(name='FB', pin='4', side='right', slot='1/2'),
            elm.IcPin(name='VOUT', pin='2', side='right', slot='2/2'),
        ],
        edgepadW=2.5,
        edgepadH=0.8,
        pinspacing=1.0,
        leadlen=1.0
    ).label('U2\nLM2596S', loc='center', fontsize=10)

    # Add all other components following the connection list...

    # Save to docs/_fragments
    import os
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_path = os.path.join(script_dir, '../docs/_fragments/buck-u2-diagram.svg')
    d.save(output_path)

print("✓ Buck converter diagram generated with transparent background")
```

### Step 4: Execute and Save

```bash
# Run the Python script
cd /Users/takazudo/repos/personal/zudo-power-usb-pd/diagram-sources
python3 buck-u2-diagram.py

# Output: SVG saved to /doc/docs/_fragments/buck-u2-diagram.svg
```

### Step 5: Integrate into Documentation

Import and use the SVG in MDX files using the `CircuitSvg` component:

```jsx
import CircuitSvg from '@site/src/components/CircuitSvg';
import BuckU2Diagram from '@site/static/circuits/buck-u2-diagram.svg';

<CircuitSvg src={BuckU2Diagram} alt="LM2596S Buck Converter U2" />
```

### Step 6: Hide ASCII Art (Optional)

Keep the ASCII art draft but collapse it using HTML `<details>` element:

```html
<details>
<summary>View ASCII art version</summary>

```
[ASCII diagram here]
```

</details>
```

Keep the connection list visible for reference.

## Directory Structure

```
project/
├── diagram-sources/
│   └── *.py                        # Schemdraw Python source files
├── doc/
│   └── docs/
│       └── _fragments/
│           ├── CircuitSvg.jsx      # Click-to-enlarge component
│           ├── CircuitDialog.jsx   # Fullscreen dialog
│           └── *.svg               # Generated circuit diagrams
```

## Schemdraw Configuration

### Default Settings

```python
with schemdraw.Drawing(
    font='Arial',         # Sans-serif font
    fontsize=11,
    color='black',        # Black foreground
    transparent=True      # Transparent background
) as d:
    d.config(unit=3)      # Scale factor
    # ... circuit elements ...
```

### Why Transparent Background with Black Foreground?

- Allows HTML container background (`oklch(86.9% 0.005 56.366)`) to show through
- Black lines and text are visible on light container backgrounds
- Works seamlessly with web-based documentation (Docusaurus)
- Professional appearance with clean contrast
- Integrates with any light-themed documentation

### Alternative: Solid Background (If Needed)

```python
# Dark theme with solid black background
with schemdraw.Drawing(
    font='Arial',
    fontsize=11,
    color='white',
    bgcolor='black'
) as d:
    # ... circuit elements ...
```

## Best Practices

### 1. Consistent Label Positioning

For vertical components (resistors, capacitors going up/down):

```python
# For components going upward
elm.Capacitor().up(2.0).label('C3\n470µF\n25V', loc='bot', ofst=0.5)
elm.Ground().flip()  # Flipped ground at top

# For components going downward
elm.Resistor().down().label('R1\n10kΩ', loc='bot', ofst=0.5)
elm.Ground()  # Normal ground at bottom
```

### 2. IC Edge Padding

Use adequate `edgepadW` parameter to prevent label overlap:

```python
ic = elm.Ic(
    pins=[...],
    edgepadW=2.5,  # Wider box prevents label overlap
    edgepadH=0.8,
    pinspacing=1.0,
    leadlen=1.0
).label('U2\nLM2596S', loc='center', fontsize=10)
```

### 3. Precise Junction Positioning

Calculate position mathematically for symmetrical connections:

```python
# For horizontal rail between two pins
junction_y = (ic.VIN[1] + ic.ON[1]) / 2

# Build entire rail at calculated height
elm.Dot(open=True).at((x_position, junction_y)).label('+15V', loc='left')
elm.Line().right(2.0)
elm.Dot()
```

### 4. Ground Symbol Orientation

```python
# Component going UP - flip ground
elm.Capacitor().up(2.0)
elm.Ground().flip()  # Ground symbol at top, points down

# Component going DOWN - normal ground
elm.Resistor().down()
elm.Ground()  # Ground symbol at bottom, points down
```

## Using CircuitSvg Component

The `CircuitSvg` component provides click-to-enlarge functionality:

```jsx
<CircuitSvg src={DiagramSvg} alt="Circuit Description" />
```

**Features:**
- Click to open fullscreen (90vw × 90vh)
- Background color: `oklch(86.9% 0.005 56.366)`
- Padding: 20px (both thumbnail and dialog)
- Maintains aspect ratio
- Keyboard accessible (Enter/Space to open)

## Troubleshooting

### Problem: Import errors in Python

**Solution**: Install schemdraw:
```bash
pip install schemdraw
```

### Problem: SVG has black background

**Solution**: Ensure you're using `transparent=True` instead of `bgcolor='black'`:

```python
# ✅ Correct
with schemdraw.Drawing(transparent=True) as d:

# ❌ Wrong
with schemdraw.Drawing(bgcolor='black') as d:
```

### Problem: Lines or text appear white on light background

**Solution**: Use `color='black'` for foreground:

```python
# ✅ Correct for transparent background
with schemdraw.Drawing(color='black', transparent=True) as d:

# ❌ Wrong (white lines invisible on light background)
with schemdraw.Drawing(color='white', transparent=True) as d:
```

### Problem: Labels overlap component symbols

**Solution**: Increase spacing and adjust label positions:

```python
# Increase overall spacing
d.config(unit=3)  # or larger

# Adjust individual spacing
HORIZONTAL_SPACING = 1.5  # Increase from 1.0
VERTICAL_SPACING = 1.5

# Adjust label positions
elm.Resistor().label('R1\n10kΩ', loc='top', ofst=0.2)
```

## Complete Example Workflow

```bash
# 1. Create connection list (ASCII art + detailed connections)
# Document in markdown: circuit-diagrams.md

# 2. Use schemdraw skill to generate Python code
/schemdraw-circuit-generator

# 3. Save Python code to /diagram-sources/
# Example: /diagram-sources/buck-u2-diagram.py

# 4. Execute Python script
cd /Users/takazudo/repos/personal/zudo-power-usb-pd/diagram-sources
python3 buck-u2-diagram.py

# 5. Verify SVG output
ls -l doc/docs/_fragments/buck-u2-diagram.svg

# 6. Test in documentation
cd /Users/takazudo/repos/personal/zudo-power-usb-pd/doc
npm start
# Open: http://localhost:3000/docs/parts/lm2596s-adj

# 7. Commit both Python source and SVG
git add diagram-sources/buck-u2-diagram.py
git add doc/docs/_fragments/buck-u2-diagram.svg
git commit -m "Add LM2596S buck converter circuit diagram"
```

## Quality Checklist

Before considering a circuit diagram complete:

- ✅ Parts verified in JLCPCB database
- ✅ Connection list is accurate and complete
- ✅ ASCII art draft follows all golden rules
- ✅ Schemdraw SVG generated with transparent background and black foreground
- ✅ Click-to-enlarge works correctly
- ✅ ASCII art hidden in `<details>` element (optional)
- ✅ Connection list remains visible
- ✅ Both SVG and Python source committed

## References

- [schemdraw Documentation](https://schemdraw.readthedocs.io/)
- [schemdraw-circuit-generator Skill](~/.claude/skills/schemdraw-circuit-generator/SKILL.md)
- [CircuitSvg Component](../../_fragments/CircuitSvg.jsx)
- [Circuit Diagrams Page](../inbox/circuit-diagrams.md)
