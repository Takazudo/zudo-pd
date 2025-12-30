#!/bin/bash
#
# Download PTC footprints from JLCPCB/LCSC using easyeda2kicad
#
# Usage: ./download-ptc-footprints.sh
#

set -e  # Exit on error

echo "========================================="
echo "PTC Footprint Download Script"
echo "========================================="
echo ""

# Define PTC parts (bash 3 compatible - using parallel arrays)
LCSC_IDS=("C7529589" "C70119" "C2830246")
DESCRIPTIONS=(
    "SMD1210P150TF/16 (+12V rail PTC)"
    "mSMD110-33V (+5V rail PTC)"
    "JK-nSMD100/16V (-12V rail PTC)"
)

# Check if easyeda2kicad is installed
if ! command -v easyeda2kicad &> /dev/null; then
    echo "❌ Error: easyeda2kicad is not installed or not in PATH"
    echo ""
    echo "Install using:"
    echo "  pip install easyeda2kicad"
    echo ""
    echo "Or see: https://github.com/uPesy/easyeda2kicad.py"
    exit 1
fi

echo "✅ Found easyeda2kicad"
echo ""

# Download each PTC footprint
for i in 0 1 2; do
    LCSC_ID="${LCSC_IDS[$i]}"
    DESCRIPTION="${DESCRIPTIONS[$i]}"

    echo "Downloading: $DESCRIPTION"
    echo "  LCSC ID: $LCSC_ID"

    easyeda2kicad --lcsc_id "$LCSC_ID" --footprint --overwrite

    if [ $? -eq 0 ]; then
        echo "  ✅ Downloaded successfully"
    else
        echo "  ❌ Download failed"
        exit 1
    fi
    echo ""
done

# Copy footprints to project
EASYEDA_DIR="$HOME/Documents/Kicad/easyeda2kicad/easyeda2kicad.pretty"
PROJECT_DIR="../kicad"

echo "Copying footprints to project..."

if [ ! -d "$EASYEDA_DIR" ]; then
    echo "❌ Error: easyeda2kicad output directory not found: $EASYEDA_DIR"
    exit 1
fi

# Create project kicad directory if it doesn't exist
mkdir -p "$PROJECT_DIR"

# Copy .kicad_mod files
cp -v "$EASYEDA_DIR"/*.kicad_mod "$PROJECT_DIR/"

echo ""
echo "✅ All PTC footprints downloaded and copied!"
echo ""
echo "Next steps:"
echo "  1. Run ./generate-footprint-svgs.sh to create SVG files"
echo "  2. Or manually export using KiCad CLI"
echo ""
