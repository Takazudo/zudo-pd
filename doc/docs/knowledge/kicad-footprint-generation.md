---
sidebar_position: 2
---

# KiCad Footprint Generation

This guide explains how to download KiCad footprints from LCSC/EasyEDA using the easyeda2kicad.py tool.

## Overview

This project uses [easyeda2kicad.py](https://github.com/uPesy/easyeda2kicad.py) to download KiCad footprints from the LCSC/EasyEDA database. This ensures we have accurate footprints matching the actual components from JLCPCB.

## Prerequisites

### Install easyeda2kicad.py

```bash
pip install easyeda2kicad
```

The tool should be available in your PATH after installation.

### Verify Installation

```bash
easyeda2kicad --version
```

## Quick Start: Download Pre-Generated Footprints

**Don't want to generate footprints yourself?** Download the complete footprint library directly from GitHub:

**🔗 [Download Footprints from GitHub](https://github.com/Takazudo/zudo-power-usb-pd/tree/main/footprints)**

The `/footprints/kicad/` directory contains all `.kicad_mod` files ready to use in your KiCad project.

---

## Finding LCSC Part Numbers

All component LCSC IDs are listed in the [Bill of Materials](../parts/bom.md). You can also search on:

- [LCSC.com](https://www.lcsc.com/)
- [EasyEDA.com](https://easyeda.com/)

## Generating Footprints Yourself

### Download by LCSC ID

```bash
# Download footprint by LCSC ID
easyeda2kicad --lcsc_id <LCSC_ID> --footprint

# Example: Download CH224D footprint
easyeda2kicad --lcsc_id C3975094 --footprint
```

### Output Location

Footprints are saved to:
```
~/Documents/Kicad/easyeda2kicad/easyeda2kicad.pretty/
```

### Copy to Project

```bash
# Copy all downloaded footprints to the project
cp ~/Documents/Kicad/easyeda2kicad/easyeda2kicad.pretty/*.kicad_mod /path/to/project/footprints/kicad/
```

## Project Structure

```
footprints/
├── kicad/
│   └── *.kicad_mod          # KiCad footprint files
├── images/
│   └── *.svg                # Exported SVG images (for documentation)
└── scripts/
    └── clean-svg-refs.py    # Script to clean SVG exports
```

## Example Workflow

### 1. Download Multiple Footprints

```bash
# CH224D - USB PD Controller
easyeda2kicad --lcsc_id C3975094 --footprint

# LM2596S-ADJ - Buck Converter
easyeda2kicad --lcsc_id C347423 --footprint

# ICL7660M - Voltage Inverter
easyeda2kicad --lcsc_id C356724 --footprint

# L7812CV - +12V Regulator
easyeda2kicad --lcsc_id C2914 --footprint

# L7805ABD2T - +5V Regulator
easyeda2kicad --lcsc_id C86206 --footprint

# CJ7912 - -12V Regulator
easyeda2kicad --lcsc_id C94173 --footprint
```

### 2. Copy to Project

```bash
cd ~/Documents/Kicad/easyeda2kicad/easyeda2kicad.pretty/
cp *.kicad_mod /Users/takazudo/repos/personal/zudo-power-usb-pd/footprints/kicad/
```

### 3. Verify Files

```bash
cd /Users/takazudo/repos/personal/zudo-power-usb-pd/footprints/kicad/
ls -l *.kicad_mod
```

## Footprint File Format

KiCad footprint files (`.kicad_mod`) are text files in S-expression format:

```lisp
(footprint "QFN-20_L3.0-W3.0-P0.40-BL-EP1.7"
  (layer "F.Cu")
  (attr smd)
  (fp_text reference "REF**" (at 0 -2.5) (layer "F.SilkS"))
  (fp_text value "CH224D" (at 0 2.5) (layer "F.Fab"))
  (pad "1" smd rect (at -1.4 -1.0) (size 0.25 0.6) (layers "F.Cu" "F.Paste" "F.Mask"))
  ...
)
```

## Troubleshooting

### Problem: "easyeda2kicad: command not found"

**Solution**: Ensure pip installed the package correctly and it's in your PATH:

```bash
which easyeda2kicad
# Should show: /path/to/python/bin/easyeda2kicad
```

If not found, try:
```bash
python -m easyeda2kicad --version
```

### Problem: "Part not found"

**Solution**:
- Verify the LCSC ID is correct
- Check if the part exists on LCSC.com
- Try using the EasyEDA part number instead

### Problem: Download fails or times out

**Solution**:
- Check internet connection
- Try again (server might be temporarily down)
- Use `--full` flag for more detailed error messages:
  ```bash
  easyeda2kicad --lcsc_id C3975094 --footprint --full
  ```

## Advanced Options

### Download Symbol and 3D Model

```bash
# Download footprint, symbol, and 3D model
easyeda2kicad --lcsc_id C3975094 --footprint --symbol --3d
```

### Specify Output Directory

```bash
easyeda2kicad --lcsc_id C3975094 --footprint --output /custom/path/
```

### Download by EasyEDA ID

```bash
easyeda2kicad --easyeda_id <EASYEDA_ID> --footprint
```

## Next Steps

After downloading footprints:
1. [Create Footprint SVG Files](./create-footprint-svg.md) - Export SVGs for documentation
2. Review footprints in KiCad PCB editor
3. Add footprints to your PCB design

## References

- [easyeda2kicad.py GitHub](https://github.com/uPesy/easyeda2kicad.py)
- [LCSC Component Search](https://www.lcsc.com/)
- [EasyEDA Component Library](https://easyeda.com/)
- [KiCad Documentation](https://docs.kicad.org/)
