# CLAUDE.md - Documentation Guidelines

This file provides guidance to Claude Code when working with documentation in this directory.

## Circuit Diagram Writing Rules

When creating or updating circuit diagrams in the documentation:

### 1. Use ASCII Art in Code Blocks

Always illustrate circuits using ASCII art within markdown code blocks:

```
USB-C 15V ──┬─→ +13.5V (DC-DC) ──→ +12V (LDO) ──→ +12V OUT
            │
            ├─→ +7.5V  (DC-DC) ──→ +5V  (LDO) ──→ +5V OUT
            │
            └─→ -15V (Inverter) ──→ -13.5V (DC-DC) ──→ -12V (LDO) ──→ -12V OUT
```

### 2. Always Include Full Connection List

Under every circuit diagram, provide a detailed connection list showing:
- Component identifiers (U1, R1, C1, etc.)
- Pin numbers and names
- Connection destinations
- Signal names or voltage levels

Example:

```
Connections:
- J1 (USB-C) VBUS → U1 (CH224D) VIN (pin 1)
- J1 (USB-C) CC1 → U1 (CH224D) CC1 (pin 5) via R1 (5.1kΩ)
- J1 (USB-C) CC2 → U1 (CH224D) CC2 (pin 6) via R2 (5.1kΩ)
- U1 (CH224D) VOUT (pin 3) → C1 (10µF) → GND
- U1 (CH224D) VOUT (pin 3) → U2 (LM2596S) VIN (pin 1)
```

### 3. ASCII Art Best Practices

- Use box-drawing characters for clear visual flow: `─ │ ┌ ┐ └ ┘ ├ ┤ ┬ ┴ ┼`
- Use arrows to show signal direction: `→ ←`
- Label all voltage levels and current ratings
- Keep diagrams concise but complete
- Group related components visually

### 4. Component Notation

- **ICs**: Use part numbers (CH224D, LM2596S, etc.)
- **Passives**: Show values with units (10µF, 5.1kΩ, 33µH)
- **Voltages**: Show at each stage (+15V, +13.5V, +12V, etc.)
- **Currents**: Show max ratings (1.2A, 800mA, etc.)

## Integration with Main Documentation

This documentation is part of a Docusaurus site. When referencing circuit diagrams:
- Place diagrams in the appropriate section (overview.md, circuit-diagrams.md, etc.)
- Cross-reference from other documents using relative links
- Keep technical accuracy paramount
- Use English for all text and labels
