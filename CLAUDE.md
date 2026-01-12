# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a hardware project for designing a USB-PD powered modular synthesizer power supply that converts USB-C PD 15V to +12V/1.2A, -12V/0.8A, and +5V/0.5A outputs for modular synthesizers. The project uses a multi-stage design with DC-DC converters followed by linear regulators for low-noise output.

## Deployment

The documentation is automatically deployed to Netlify:

- **Production URL**: https://takazudomodular.com/pj/zudo-pd/
- **Netlify URL**: https://zudopd.netlify.app/pj/zudo-pd/ (rewritten to production URL)
- **Base Path**: `/pj/zudo-pd/`
- **Deployment**: Automatic on every push to `main` branch
- **Technology**: Docusaurus static site deployed via Netlify CLI on GitHub Actions
- **Configuration**: See `.github/workflows/main-deploy.yml` for deployment workflow

## Repository Structure

### Documentation
- `/doc/docs/` - **Primary documentation** (Docusaurus-based, organized)
  - `overview/` - Project overview, circuit diagrams, BOM
  - `components/` - Individual component datasheets and specifications
  - `learning/` - Circuit design learning notes
  - `how-to/` - How-to guides (KiCad workflow, parts download, SVG export, circuit diagrams)
  - `inbox/` - Quick reference and miscellaneous docs
  - `misc/` - Miscellaneous documentation
  - `_fragments/` - Reusable fragments (footprint SVGs for React imports)
- `/doc/static/` - **Documentation assets** (images, PDFs, SVGs)
  - `circuits/` - Circuit diagram SVGs
  - `footprints/` - Component package preview images (PNG)
  - `datasheets/` - Component datasheets and package specs (PDF)
  - `kicad/` - KiCad setup screenshots

### KiCad Libraries
- `/footprints/` - **KiCad footprint library**
  - `kicad/` - KiCad footprint source files (.kicad_mod)
  - `images/` - Exported SVG files (source for documentation)
  - `scripts/` - Processing scripts (clean-svg-refs.py)
- `/symbols/` - **KiCad symbol library**
  - `zudo-pd.kicad_sym` - Project schematic symbols (USB-C, CH224D, regulators, etc.)

### KiCad Project Files (repository root)
- `zudo-pd.kicad_pro` - Project configuration
- `zudo-pd.kicad_sch` - Root schematic (hierarchical sheet structure)
- `usb-pd-input.kicad_sch` - USB-PD input stage sub-sheet
- `dc-dc-conversion.kicad_sch` - DC-DC converters sub-sheet
- `linear-regulation.kicad_sch` - Linear regulators + protection sub-sheet
- `output.kicad_sch` - Output connectors sub-sheet
- `zudo-pd.kicad_pcb` - PCB layout file
- `fp-lib-table` - Footprint library configuration
- `sym-lib-table` - Symbol library configuration

### Other Directories
- `/diagram-sources/` - Python schemdraw scripts for circuit diagram generation
- `/3dp-files/` - 3D printable files (component guards, enclosures)
- `/jlcpcb-templates/` - JLCPCB BOM/CPL template files
- `/jlcpcb-order-snapshots/` - Historical order snapshots for reference
- `/__inbox/` - **Temporary files** (gitignored, use for working files)

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

When the user provides URLs starting with `http://localhost:3800/pj/zudo-pd/` or `http://zudopd.localhost:3800/pj/zudo-pd/` in the conversation:

- **DO NOT fetch the URL** - These are local documentation URLs served by Docusaurus
- **Instead, find and read the corresponding markdown file** in the `/doc/` directory
- Map URLs to file paths following Docusaurus routing (note: `/pj/zudo-pd/` is the base path):
  - `http://localhost:3800/pj/zudo-pd/` or `http://zudopd.localhost:3800/pj/zudo-pd/` → `/doc/docs/` (root pages)
  - `http://zudopd.localhost:3800/pj/zudo-pd/docs/inbox/overview` → `/doc/docs/inbox/overview.md`
  - `http://zudopd.localhost:3800/pj/zudo-pd/docs/inbox/circuit-diagrams` → `/doc/docs/inbox/circuit-diagrams.md`
- Use the Read tool to access the actual markdown source files
- This provides the raw content without HTML rendering, making it easier to edit and understand

Example:
- User mentions: `http://zudopd.localhost:3800/pj/zudo-pd/docs/inbox/current-status`
- Read file: `/doc/docs/inbox/current-status.md`

## File Types

- `.md` files contain technical specifications and circuit diagrams in text format
- `.html` files provide styled visualizations of the circuit design
- `.kicad_pro` - KiCad project configuration file
- `.kicad_sch` - KiCad schematic files (circuit diagrams)
- `.kicad_pcb` - KiCad PCB layout files
- `.kicad_mod` - KiCad footprint files (physical component pads)
- `.kicad_sym` - KiCad symbol library files (schematic symbols)
- `fp-lib-table` - Footprint library configuration
- `sym-lib-table` - Symbol library configuration
- No code compilation or testing is required - this is a hardware design project

## KiCad Library Management

This project uses [easyeda2kicad.py](https://github.com/uPesy/easyeda2kicad.py) to download KiCad footprints and symbols from LCSC/EasyEDA.

### File Organization

**Footprints (PCB physical pads):**
- **KiCad source files**: `/footprints/kicad/*.kicad_mod` (individual footprint files)
- **SVG exports**: `/footprints/images/*.svg` (intermediate)
- **Documentation SVGs**: `/doc/docs/_fragments/footprints/*.svg` (final destination)
- **Package previews**: `/doc/static/footprints/*.png` (datasheet images)
- **Datasheets**: `/doc/static/datasheets/*.pdf` (component specs)

**Symbols (schematic symbols):**
- **Symbol library**: `/symbols/zudo-pd.kicad_sym` (single file containing all project symbols)

### Downloading Footprints and Symbols

**For detailed instructions, see:**
- **[Download KiCad Footprints and Symbols Guide](/doc/docs/how-to/kicad-parts-download.md)**

**Quick reference:**
```bash
# Download BOTH footprint and symbol (recommended)
easyeda2kicad --lcsc_id <LCSC_ID> --footprint --symbol

# Copy footprints to project
cp ~/Documents/Kicad/easyeda2kicad/easyeda2kicad.pretty/*.kicad_mod ./footprints/kicad/

# Copy symbols to project
cp ~/Documents/Kicad/easyeda2kicad/easyeda2kicad.kicad_sym ./symbols/zudo-pd.kicad_sym
```

**For users**: Download directly from GitHub:
- [Footprints](https://github.com/Takazudo/zudo-pd/tree/main/footprints)
- [Symbols](https://github.com/Takazudo/zudo-pd/tree/main/symbols)

### Exporting SVG Files for Documentation (Manual Workflow)

When footprints are added or updated, export SVGs manually for documentation:

**For detailed instructions, see:**
- **[Create Footprint SVG Files](/doc/docs/how-to/create-footprint-svg.md)**

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