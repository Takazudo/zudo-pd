---
sidebar_position: 3
---

# Create Footprint SVG Files for Documentation

This guide explains how to export KiCad footprints to SVG format and prepare them for use in the documentation.

## Overview

The documentation displays clickable footprint previews on each component page. This workflow converts KiCad `.kicad_mod` files to clean SVG images.

## Prerequisites

- KiCad 9.0.6 or later (with `kicad-cli` command)
- Python 3 (for cleanup script)
- KiCad footprints downloaded (see [KiCad Parts Download Guide](./kicad-parts-download.md))

## Verify KiCad CLI

```bash
kicad-cli --version
# Should show: Version: 9.0.6 or later
```

If `kicad-cli` is not found, you need to add it to your PATH:

**macOS:**

```bash
export PATH="/Applications/KiCad/KiCad.app/Contents/MacOS:$PATH"
```

**Linux:**

```bash
# Usually already in PATH after KiCad installation
```

**Windows:**

```powershell
# Add KiCad installation directory to PATH
# Typically: C:\Program Files\KiCad\bin
```

## Workflow

### Step 1: Prepare .pretty Directory

KiCad CLI requires footprints in a `.pretty` directory structure:

```bash
cd /Users/takazudo/repos/personal/zudo-power-usb-pd/footprints/kicad

# Create .pretty directory
mkdir -p zudo-power.pretty

# Copy .kicad_mod files
cp *.kicad_mod zudo-power.pretty/
```

### Step 2: Export to SVG

Export all footprints to SVG format with black-and-white rendering:

```bash
cd /Users/takazudo/repos/personal/zudo-power-usb-pd/footprints

# Export SVGs
kicad-cli fp export svg kicad/zudo-power.pretty -o images --black-and-white
```

**Output:** SVG files are saved to `footprints/images/`

### Step 3: Clean SVG Files

Remove KiCad placeholder text (REF**, VAL**) from SVGs using the cleanup script:

```bash
cd /Users/takazudo/repos/personal/zudo-power-usb-pd/footprints

# Run cleanup script
python3 scripts/clean-svg-refs.py images/
```

The script removes:

- `REF**` placeholder text
- `VAL**` placeholder text
- Both text elements and stroked-text path groups

### Step 4: Copy to Documentation

```bash
cd /Users/takazudo/repos/personal/zudo-power-usb-pd/footprints

# Copy cleaned SVGs to documentation fragments
cp images/*.svg ../doc/docs/_fragments/footprints/
```

### Step 5: Verify Results

Check that SVGs are clean:

```bash
cd /Users/takazudo/repos/personal/zudo-power-usb-pd/doc/docs/_fragments/footprints

# Quick check: should find NO instances of REF** in SVG files
grep -l "REF\*\*" *.svg
# (No output = success)
```

## Directory Structure

```
project/
├── footprints/
│   ├── kicad/
│   │   ├── *.kicad_mod              # Original KiCad footprints
│   │   └── zudo-power.pretty/       # .pretty directory for export
│   │       └── *.kicad_mod
│   ├── images/
│   │   └── *.svg                    # Exported and cleaned SVGs
│   └── scripts/
│       └── clean-svg-refs.py        # Cleanup script
└── doc/
    └── docs/
        └── _fragments/
            └── footprints/
                └── *.svg            # Final SVGs for documentation
```

## Cleanup Script Details

### Location

`/Users/takazudo/repos/personal/zudo-power-usb-pd/footprints/scripts/clean-svg-refs.py`

### What It Does

The script processes SVG files to remove KiCad placeholders:

1. **Text Elements**: Removes `<text>` elements containing `REF**` or `VAL**`
2. **Stroked-Text Groups**: Removes path-based text rendered as vector shapes
3. **Preserves**: All footprint geometry, pads, and silkscreen

### Usage

```bash
# Clean all SVGs in a directory
python3 clean-svg-refs.py /path/to/svg/directory/

# The script modifies files in-place
# Creates no backup - commit to git first!
```

### Verification

The script reports how many elements were removed:

```
Processing: QFN-20_L3.0-W3.0-P0.40-BL-EP1.7.svg - Removed 2 elements
Processing: TO-263-5_L10.2-W8.9-P1.70-BR.svg - Removed 2 elements
...
✓ Processed 28 SVG files
```

## Using Footprints in Documentation

### Import and Use FootprintSvg Component

In MDX files (e.g., component pages):

```jsx
import FootprintSvg from '@site/src/components/FootprintSvg';
import CH224D from '@site/static/footprints-svg/QFN-20_L3.0-W3.0-P0.40-BL-EP1.7.svg';

<FootprintSvg src={CH224D} alt="CH224D QFN-20 Package" minWidth="300px" minHeight="300px" />;
```

### Component Features

- Click-to-enlarge (90vw × 90vh fullscreen dialog)
- Background color: `oklch(86.9% 0.005 56.366)`
- Padding: 20px
- Maintains aspect ratio

## Troubleshooting

### Problem: kicad-cli not found

**Solution**: Add KiCad to PATH (see "Verify KiCad CLI" above)

### Problem: Export fails with "Library not found"

**Solution**: Ensure footprints are in a `.pretty` directory:

```bash
# Correct structure:
footprints/kicad/zudo-power.pretty/QFN-20_L3.0-W3.0-P0.40-BL-EP1.7.kicad_mod

# Wrong structure:
footprints/kicad/QFN-20_L3.0-W3.0-P0.40-BL-EP1.7.kicad_mod
```

### Problem: SVG still shows REF\*\* after cleanup

**Solution**:

1. Check that cleanup script ran successfully
2. Some SVGs may have additional text elements - inspect manually:
   ```bash
   grep "REF\*\*" problem-file.svg
   ```
3. Update cleanup script if needed

### Problem: SVG appears blank in documentation

**Solution**:

1. Verify SVG file is not corrupted:
   ```bash
   head -5 footprint.svg
   # Should show valid SVG header
   ```
2. Check import path is correct
3. Verify file was copied to `docs/_fragments/footprints/`

## Complete Example Workflow

```bash
# 1. Navigate to footprints directory
cd /Users/takazudo/repos/personal/zudo-power-usb-pd/footprints

# 2. Create .pretty directory structure
mkdir -p kicad/zudo-power.pretty
cp kicad/*.kicad_mod kicad/zudo-power.pretty/

# 3. Export to SVG
kicad-cli fp export svg kicad/zudo-power.pretty -o images --black-and-white

# 4. Clean SVG files
python3 scripts/clean-svg-refs.py images/

# 5. Verify cleanup
grep -l "REF\*\*" images/*.svg
# (No output = success)

# 6. Copy to documentation
cp images/*.svg ../doc/docs/_fragments/footprints/

# 7. Verify in documentation
cd ../doc
npm start
# Open browser to http://localhost:3000/docs/components
```

## Next Steps

- [View Footprint Preview](../inbox/footprint-preview.md) - See all footprints in the documentation
- Update component pages to include new footprints
- Commit changes to git

## References

- [KiCad CLI Documentation](https://docs.kicad.org/master/en/cli/cli.html)
- [SVG Specification](https://www.w3.org/TR/SVG2/)
