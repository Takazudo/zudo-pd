#!/usr/bin/env python3
"""
Remove REF** placeholder text from KiCad footprint SVG exports.
This includes both <text> elements and <g class="stroked-text"> path-based text.

Usage:
    python clean-svg-refs.py <svg_file>
    python clean-svg-refs.py <directory>  # Process all SVG files in directory
"""

import sys
import re
from pathlib import Path
import xml.etree.ElementTree as ET


def clean_svg_references(svg_path):
    """Remove REF** and VAL** reference text elements and stroked-text groups."""

    # Parse SVG
    ET.register_namespace('', 'http://www.w3.org/2000/svg')
    tree = ET.parse(svg_path)
    root = tree.getroot()

    removed_count = 0

    # Remove text elements with REF** or VAL**
    for elem in list(root.iter()):
        # Check text content
        if elem.text and re.search(r'(REF|VAL)\*\*', elem.text):
            parent = find_parent(root, elem)
            if parent is not None:
                parent.remove(elem)
                removed_count += 1
                continue

    # Remove stroked-text groups
    # Strategy: Remove stroked-text groups that:
    # 1. Have a <desc> child with REF** or VAL**
    # 2. OR have no <desc> child (these are usually REF** rendered as paths)
    for elem in list(root.iter()):
        if 'class' in elem.attrib and elem.attrib['class'] == 'stroked-text':
            # Check if it has a desc child
            desc_elem = elem.find('.//{http://www.w3.org/2000/svg}desc')

            should_remove = False

            if desc_elem is not None and desc_elem.text:
                # Has desc - check if it's REF** or VAL**
                if re.search(r'(REF|VAL)\*\*', desc_elem.text):
                    should_remove = True
            else:
                # No desc - likely a REF** rendered as paths
                # Check if it's not the footprint name by looking for specific patterns
                # Footprint names usually have long descriptive text in desc
                # REF** groups typically have no desc or just "REF**"
                should_remove = True

            # Additional check: if the stroked-text has a desc with a long name (footprint name),
            # don't remove it
            if desc_elem is not None and desc_elem.text:
                # If desc contains more than just REF**/VAL** (like actual footprint names),
                # keep it
                if not re.search(r'^(REF|VAL)\*\*$', desc_elem.text.strip()):
                    should_remove = False

            if should_remove:
                parent = find_parent(root, elem)
                if parent is not None:
                    parent.remove(elem)
                    removed_count += 1

    if removed_count > 0:
        # Write back to file
        tree.write(svg_path, encoding='utf-8', xml_declaration=True)
        print(f"✓ {svg_path.name}: Removed {removed_count} reference element(s)")
        return True
    else:
        print(f"  {svg_path.name}: No reference elements found")
        return False


def find_parent(root, elem):
    """Find parent element of a given element."""
    for parent in root.iter():
        if elem in list(parent):
            return parent
    return None


def process_file(file_path):
    """Process a single SVG file."""
    try:
        clean_svg_references(file_path)
    except Exception as e:
        print(f"✗ {file_path.name}: Error - {e}")


def main():
    if len(sys.argv) < 2:
        print("Usage: python clean-svg-refs.py <svg_file_or_directory>")
        sys.exit(1)

    path = Path(sys.argv[1])

    if path.is_file() and path.suffix == '.svg':
        process_file(path)
    elif path.is_dir():
        svg_files = list(path.glob('*.svg'))
        if not svg_files:
            print(f"No SVG files found in {path}")
            sys.exit(1)

        print(f"Processing {len(svg_files)} SVG files...\n")
        for svg_file in sorted(svg_files):
            process_file(svg_file)
    else:
        print(f"Error: {path} is not a valid SVG file or directory")
        sys.exit(1)


if __name__ == '__main__':
    main()
