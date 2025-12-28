# Circuit Diagram Sources

This directory contains Python scripts that generate circuit diagrams using the `schemdraw` library.

## Organization

- **Source files**: Python scripts (`.py`) are stored here
- **Generated files**: SVG outputs are saved to `../docs/_fragments/`
- **Dark theme**: All diagrams use dark theme (black background, white foreground, Arial font)

## Generating Diagrams

Run any Python script to regenerate its corresponding SVG:

```bash
cd diagram-sources
python3 buck-u2-diagram.py
```

Output will be saved to `docs/_fragments/buck-u2-diagram.svg`

## Current Diagrams

- `buck-u2-diagram.py` → LM2596S-ADJ Buck Converter (+15V → +13.5V)

## Adding New Diagrams

1. Create a new `.py` file in this directory
2. Use the existing scripts as templates
3. Set output path to: `../docs/_fragments/your-diagram-name.svg`
4. Run the script to generate the SVG
5. Import and use in MDX files via the `CircuitSvg` component

## Requirements

```bash
pip install schemdraw
```
