---
sidebar_position: 2
---

# Download KiCad Footprints and Symbols

This guide explains how to download KiCad footprints and symbols from LCSC/EasyEDA using the easyeda2kicad.py tool.

## Overview

This project uses [easyeda2kicad.py](https://github.com/uPesy/easyeda2kicad.py) to download KiCad libraries from the LCSC/EasyEDA database. This ensures we have accurate footprints and symbols matching the actual components from JLCPCB.

**What you can download:**

- **Footprints** (`.kicad_mod`) - Physical PCB pads for PCB layout
- **Symbols** (`.kicad_sym`) - Schematic symbols for circuit design
- **3D Models** (`.step`, `.wrl`) - 3D visualization (optional)

## Important: Footprints vs Symbols

**You need BOTH for KiCad design:**

| Type      | File Format  | Used In          | Purpose                             |
| --------- | ------------ | ---------------- | ----------------------------------- |
| Footprint | `.kicad_mod` | PCB Editor       | Physical component pads on PCB      |
| Symbol    | `.kicad_sym` | Schematic Editor | Electrical connections in schematic |

**Common mistake:** Downloading only `--footprint` without `--symbol`!

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

**🔗 [Download Footprints from GitHub](https://github.com/Takazudo/zudo-pd/tree/main/footprints)**

The `/footprints/kicad/` directory contains all `.kicad_mod` files ready to use in your KiCad project.

---

## Finding LCSC Part Numbers

All component LCSC IDs are listed in the [Bill of Materials](../overview/bom.md). You can also search on:

- [LCSC.com](https://www.lcsc.com/)
- [EasyEDA.com](https://easyeda.com/)

## Download Options

### Option 1: Download Both (Recommended)

Download footprint AND symbol together:

```bash
# Download both footprint and symbol
easyeda2kicad --lcsc_id <LCSC_ID> --footprint --symbol

# Example: STUSB4500 (USB-PD controller)
easyeda2kicad --lcsc_id C2678061 --footprint --symbol

# Example: USB-C connector
easyeda2kicad --lcsc_id C456012 --footprint --symbol
```

### Option 2: Download Only Footprint

For parts where you'll use KiCad standard symbols:

```bash
# Download only footprint
easyeda2kicad --lcsc_id <LCSC_ID> --footprint
```

### Option 3: Download Only Symbol

For parts where you already have the footprint:

```bash
# Download only symbol
easyeda2kicad --lcsc_id <LCSC_ID> --symbol
```

## Output Locations

### Footprints

```
~/Documents/Kicad/easyeda2kicad/easyeda2kicad.pretty/
└── *.kicad_mod
```

### Symbols

```
~/Documents/Kicad/easyeda2kicad/
└── easyeda2kicad.kicad_sym
```

**Important:** Symbols are added to a single `.kicad_sym` file, not separate files like footprints.

## Project Structure

```
footprints/
├── kicad/
│   └── *.kicad_mod          # KiCad footprint files
├── images/
│   └── *.svg                # Exported SVG images (for documentation)
└── scripts/
    └── clean-svg-refs.py    # Script to clean SVG exports

symbols/
└── zudo-pd.kicad_sym        # Project symbol library (copied from download)

~/Documents/Kicad/easyeda2kicad/  (download location)
├── easyeda2kicad.pretty/
│   └── *.kicad_mod          # Downloaded footprints
└── easyeda2kicad.kicad_sym  # Downloaded symbols (all in one file)
```

## Complete Download Workflow

### 1. Download All Project Parts

Download all components with BOTH footprints and symbols:

```bash
# USB-C Connector
easyeda2kicad --lcsc_id C456012 --footprint --symbol

# STUSB4500 - USB PD Controller
easyeda2kicad --lcsc_id C2678061 --footprint --symbol

# LM2596S-ADJ - Buck Converter
easyeda2kicad --lcsc_id C347423 --footprint --symbol

# ICL7660M - Voltage Inverter
easyeda2kicad --lcsc_id C356724 --footprint --symbol

# L7812CV - +12V Regulator
easyeda2kicad --lcsc_id C2914 --footprint --symbol

# L7805ABD2T - +5V Regulator
easyeda2kicad --lcsc_id C86206 --footprint --symbol

# CJ7912 - -12V Regulator
easyeda2kicad --lcsc_id C94173 --footprint --symbol

# SMAJ15A - TVS Diode
easyeda2kicad --lcsc_id C347883 --footprint --symbol

# SD05 - TVS Diode (5V)
easyeda2kicad --lcsc_id C502527 --footprint --symbol
```

### 2. Copy to Project

```bash
# Create symbols directory
mkdir -p /Users/takazudo/repos/personal/zudo-pd/symbols

# Copy footprints
cp ~/Documents/Kicad/easyeda2kicad/easyeda2kicad.pretty/*.kicad_mod \
   /Users/takazudo/repos/personal/zudo-pd/footprints/kicad/

# Copy symbols
cp ~/Documents/Kicad/easyeda2kicad/easyeda2kicad.kicad_sym \
   /Users/takazudo/repos/personal/zudo-pd/symbols/zudo-pd.kicad_sym
```

### 3. Add Libraries to KiCad

**Add Symbol Library:**

1. Preferences → Manage Symbol Libraries
2. Click "Project Specific Libraries" tab
3. Add library:
- Nickname: `zudo-pd`
- Library Path: `${KIPRJMOD}/symbols/zudo-pd.kicad_sym`
- Plugin Type: `KiCad`

**Add Footprint Library** (if not done yet):

1. Preferences → Manage Footprint Libraries
2. Click "Project Specific Libraries" tab
3. Add library:
- Nickname: `zudo-pd`
- Library Path: `${KIPRJMOD}/footprints/kicad/zudo-power.pretty`

### 4. Verify Files

```bash
# Check footprints
ls -l /Users/takazudo/repos/personal/zudo-pd/footprints/kicad/*.kicad_mod

# Check symbols
ls -l /Users/takazudo/repos/personal/zudo-pd/symbols/zudo-pd.kicad_sym
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
