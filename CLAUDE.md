# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a hardware project for designing a USB-PD powered modular synthesizer power supply that converts USB-C PD 15V to +12V/1.2A, -12V/0.8A, and +5V/0.5A outputs for modular synthesizers. The project uses a multi-stage design with DC-DC converters followed by linear regulators for low-noise output.

## Repository Structure

### Current Documentation (Use These)
- `/doc/docs/` - **Primary documentation** (Docusaurus-based, organized)
  - `inbox/` - Main documentation (overview, parts list, quick reference, current status)
  - `parts/` - Individual component datasheets and specifications
  - `learning/` - Circuit design learning notes
  - `knowledge/` - How-to guides (footprint generation, SVG export, circuit diagrams)
- `/doc/static/` - **Documentation assets** (images, PDFs, SVGs)
  - `footprints/` - Component package preview images (PNG)
  - `datasheets/` - Component datasheets and package specs (PDF)
- `/doc/docs/_fragments/footprints/` - **Footprint SVGs** (for React imports in documentation)
- `/footprints/` - **KiCad design files** (not for documentation)
  - `kicad/` - KiCad footprint source files (.kicad_mod)
  - `images/` - Exported SVG files (source for documentation)
  - `scripts/` - Processing scripts (clean-svg-refs.py)
- `/__inbox/` - **Temporary files** (gitignored, use for working files)

### Legacy Documentation (Outdated)
- `/notes/` - Old documentation (outdated, do not use)
- `/generated-docs/` - Old generated docs (outdated, do not use)
- `/inbox/` - Old working directory (outdated, use `__inbox/` instead)

## Technical Architecture

The power supply uses a 4-stage architecture:

1. **USB-PD Stage**: CH224Q IC negotiates 15V from USB-C PD
2. **DC-DC Stage**: Multiple LM2596S-ADJ converters create intermediate voltages
   - +15V → +13.5V (for +12V rail)
   - +15V → +7.5V (for +5V rail)  
   - +15V → -15V (ICL7660 voltage inverter) → -13.5V (for -12V rail)
3. **Linear Regulator Stage**: LM78xx/LM79xx series for final low-noise outputs
   - LM7812: +13.5V → +12V
   - LM7805: +7.5V → +5V
   - LM7912: -13.5V → -12V
4. **Protection Stage**: Fuses and TVS diodes for overcurrent/overvoltage protection

## Key Design Features

- **Low-noise design**: DC-DC + Linear regulator combination for <1mVp-p ripple
- **JLCPCB compatibility**: All parts selected for JLCPCB SMT assembly
- **Safety margins**: 150%+ current capacity on all circuits
- **Modular synth optimized**: Voltage and current specifications match typical modular synthesizer requirements

## Documentation Language

**All documentation must be written in English.** This includes:
- Circuit diagrams and annotations
- Technical specifications
- README files
- Code comments
- Commit messages

Use English for all text to ensure international accessibility and collaboration. ASCII art diagrams should use English labels to avoid encoding issues.

## URL Reference Guidelines

When the user provides URLs starting with `http://localhost:3000/` in the conversation:

- **DO NOT fetch the URL** - These are local documentation URLs served by Docusaurus
- **Instead, find and read the corresponding markdown file** in the `/doc/` directory
- Map URLs to file paths following Docusaurus routing:
  - `http://localhost:3000/` → `/doc/docs/` (root pages)
  - `http://localhost:3000/docs/inbox/overview` → `/doc/docs/inbox/overview.md`
  - `http://localhost:3000/docs/inbox/circuit-diagrams` → `/doc/docs/inbox/circuit-diagrams.md`
- Use the Read tool to access the actual markdown source files
- This provides the raw content without HTML rendering, making it easier to edit and understand

Example:
- User mentions: `http://localhost:3000/docs/inbox/current-status`
- Read file: `/doc/docs/inbox/current-status.md`

## File Types

- `.md` files contain technical specifications and circuit diagrams in text format
- `.html` files provide styled visualizations of the circuit design
- `.kicad_mod` files are KiCad footprint files for PCB design
- No code compilation or testing is required - this is a hardware design project

## Footprint Management

This project uses [easyeda2kicad.py](https://github.com/uPesy/easyeda2kicad.py) to download KiCad footprints from LCSC/EasyEDA.

### File Organization

- **KiCad source files**: `/footprints/kicad/*.kicad_mod` (design workspace)
- **SVG exports**: `/footprints/images/*.svg` (intermediate)
- **Documentation SVGs**: `/doc/docs/_fragments/footprints/*.svg` (final destination)
- **Package previews**: `/doc/static/footprints/*.png` (datasheet images)
- **Datasheets**: `/doc/static/datasheets/*.pdf` (component specs)

### Downloading Footprints

**For detailed instructions, see:**
- **[KiCad Footprint Generation Guide](/doc/docs/knowledge/kicad-footprint-generation.md)**

**Quick reference:**
```bash
# Download footprint by LCSC ID
easyeda2kicad --lcsc_id <LCSC_ID> --footprint

# Copy to project
cp ~/Documents/Kicad/easyeda2kicad/easyeda2kicad.pretty/*.kicad_mod ./footprints/kicad/
```

**For users**: Download footprints directly from [GitHub](https://github.com/Takazudo/zudo-power-usb-pd/tree/main/footprints)

### Exporting SVG Files for Documentation (Manual Workflow)

When footprints are added or updated, export SVGs manually for documentation:

**For detailed instructions, see:**
- **[Create Footprint SVG Files](/doc/docs/knowledge/create-footprint-svg.md)**

**Quick workflow:**
```bash
# 1. Create .pretty directory if needed
cd footprints/kicad
mkdir -p zudo-power.pretty
cp *.kicad_mod zudo-power.pretty/

# 2. Export SVGs using KiCad CLI
kicad-cli fp export svg zudo-power.pretty -o ../images --black-and-white

# 3. Clean SVG files (remove REF** text)
python3 ../scripts/clean-svg-refs.py ../images/

# 4. Copy to documentation
cp ../images/*.svg ../../doc/docs/_fragments/footprints/
```

**Note**: This is a manual process. Run after adding/updating footprints. Future automation may be added via CI/CD.