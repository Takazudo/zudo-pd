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

## Dual-location sync rule

> Every `.kicad_mod` file must exist in BOTH `footprints/kicad/*.kicad_mod` (source of truth) AND `footprints/kicad/zudo-power.pretty/*.kicad_mod` (KiCad library resolution path). A file only in the master dir will NOT resolve when KiCad opens the PCB. The Quick Workflow `cp *.kicad_mod zudo-power.pretty/` step is mandatory, not optional.

## Hand-created footprints

Some parts do not exist in LCSC or EasyEDA. For those, create the footprint by hand rather than running `easyeda2kicad`.

### When to hand-create

Create a footprint manually when the component is not a standard LCSC part:

- Bare test pads
- Card-edge / board-edge pads
- Mechanical mounting features
- Fiducial marks
- Logos and silkscreen art
- Pogo pin arrays for programming jigs

### File format

Use the legacy `(module ...)` S-expression format. Copy the style and layer assignments from an existing neighbor such as `footprints/kicad/R0603.kicad_mod` for consistency with the rest of the library.

### Library prefix convention

- **Hand-created footprints** can use the library tag `zudo-pd:<Name>` — this matches the `fp-lib-table` library name `zudo-pd`.
- **Downloaded footprints** (via `easyeda2kicad`) keep their original `easyeda2kicad:<Name>` tag.

Both prefix styles resolve correctly because the single `fp-lib-table` entry `zudo-pd` points at the `footprints/kicad/zudo-power.pretty/` directory. The library prefix stored inside the `.kicad_mod` file itself is documentation only — KiCad resolves footprints by directory, not by the prefix string inside the file.

### Where to save

Write the new footprint to **two locations**:

1. `footprints/kicad/<Name>.kicad_mod` — master / source of truth
2. `footprints/kicad/zudo-power.pretty/<Name>.kicad_mod` — KiCad library resolution path

Then run the SVG export workflow above so documentation stays up to date.

## Hand-created inventory

The following footprints in this library were created by hand (not downloaded from LCSC/EasyEDA):

- `PogoPad_1x04_P2.54mm` — 4P 2.54 mm pogo pad array for STUSB4500 NVM I2C programming (see `doc/docs/inbox/nvm-programming.md`)
