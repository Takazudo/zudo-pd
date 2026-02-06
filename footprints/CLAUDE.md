# CLAUDE.md - KiCad Library Management

This project uses [easyeda2kicad.py](https://github.com/uPesy/easyeda2kicad.py) to download KiCad footprints and symbols from LCSC/EasyEDA.

## File Organization

**Footprints (PCB physical pads):**
- **KiCad source files**: `/footprints/kicad/*.kicad_mod` (individual footprint files)
- **SVG exports**: `/footprints/images/*.svg` (intermediate)
- **Documentation SVGs**: `/doc/docs/_fragments/footprints/*.svg` (final destination)
- **Package previews**: `/doc/static/footprints/*.png` (datasheet images)
- **Datasheets**: `/doc/static/datasheets/*.pdf` (component specs)

**Symbols (schematic symbols):**
- **Symbol library**: `/symbols/zudo-pd.kicad_sym` (single file containing all project symbols)

## Downloading Footprints and Symbols

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

## Exporting SVG Files for Documentation (Manual Workflow)

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
