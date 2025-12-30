#!/bin/bash
#
# Generate SVG files from KiCad footprints
#
# Usage: ./generate-footprint-svgs.sh
#

set -e  # Exit on error

echo "========================================="
echo "Footprint SVG Generation Script"
echo "========================================="
echo ""

# Directories
KICAD_DIR="../kicad"
PRETTY_DIR="../kicad/zudo-power.pretty"
IMAGES_DIR="../images"
DOCS_DIR="../../doc/docs/_fragments/footprints"

# Check if kicad-cli is available
if ! command -v kicad-cli &> /dev/null; then
    echo "❌ Error: kicad-cli is not installed or not in PATH"
    echo ""
    echo "KiCad CLI is required to export SVG files."
    echo "Install KiCad 7.0 or later from: https://www.kicad.org/download/"
    exit 1
fi

echo "✅ Found kicad-cli"
echo ""

# Create .pretty directory if needed
echo "Creating .pretty directory..."
mkdir -p "$PRETTY_DIR"

# Copy .kicad_mod files to .pretty directory
echo "Copying .kicad_mod files to .pretty directory..."
cp -v "$KICAD_DIR"/*.kicad_mod "$PRETTY_DIR/"
echo ""

# Export SVGs using KiCad CLI
echo "Exporting SVG files..."
mkdir -p "$IMAGES_DIR"

kicad-cli fp export svg "$PRETTY_DIR" -o "$IMAGES_DIR" --black-and-white

if [ $? -eq 0 ]; then
    echo "✅ SVG export successful"
else
    echo "❌ SVG export failed"
    exit 1
fi
echo ""

# Clean SVG files (remove REF** text)
CLEAN_SCRIPT="./clean-svg-refs.py"

if [ -f "$CLEAN_SCRIPT" ]; then
    echo "Cleaning SVG files (removing REF** labels)..."
    python3 "$CLEAN_SCRIPT" "$IMAGES_DIR/"

    if [ $? -eq 0 ]; then
        echo "✅ SVG cleaning successful"
    else
        echo "⚠️  SVG cleaning failed, but SVGs are still usable"
    fi
else
    echo "⚠️  Warning: clean-svg-refs.py not found, skipping SVG cleaning"
    echo "   SVGs may contain REF** text labels"
fi
echo ""

# Copy to documentation
echo "Copying SVG files to documentation..."
mkdir -p "$DOCS_DIR"
cp -v "$IMAGES_DIR"/*.svg "$DOCS_DIR/"
echo ""

echo "✅ All done!"
echo ""
echo "Generated files:"
echo "  - SVG files: $IMAGES_DIR/"
echo "  - Documentation SVGs: $DOCS_DIR/"
echo ""
echo "Next steps:"
echo "  1. Verify SVG files in $DOCS_DIR/"
echo "  2. Update component documentation to include footprint images"
echo "  3. Commit changes to git"
echo ""
