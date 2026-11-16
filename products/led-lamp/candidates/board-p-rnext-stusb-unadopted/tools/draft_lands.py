"""Draft manufacturer-pattern lands for the three r-next parts whose zudo-pd land differs
from the manufacturer drawing (see checks/land-check.json). DRAFT: not fabrication-reviewed.

Each land uses only the dimensions printed in the cited drawing; pad numbering and row
orientation follow the zudo-pd footprint it replaces, so the pin maps are unchanged.
Usage: python3 .../tools/draft_lands.py   (writes footprints/rnext-mfr.pretty/*.kicad_mod)
"""
import os

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(HERE, 'footprints', 'rnext-mfr.pretty')
CRT = 0.25  # courtyard clearance, project convention (IPC-7351 nominal)


def fmt(v):
    return f'{v:.4f}'.rstrip('0').rstrip('.') if v else '0'


def rect(layer, x0, y0, x1, y1, width):
    pts = [(x0, y0), (x1, y0), (x1, y1), (x0, y1), (x0, y0)]
    return [f'\t(fp_line (start {fmt(a[0])} {fmt(a[1])}) (end {fmt(b[0])} {fmt(b[1])}) (stroke (width {width}) (type solid)) (layer "{layer}"))'
            for a, b in zip(pts, pts[1:])]


def land(name, descr, pads, body):
    xs = [p[1] - p[3] / 2 for p in pads] + [p[1] + p[3] / 2 for p in pads] + [-body[0] / 2, body[0] / 2]
    ys = [p[2] - p[4] / 2 for p in pads] + [p[2] + p[4] / 2 for p in pads] + [-body[1] / 2, body[1] / 2]
    cx0, cx1 = round(min(xs) - CRT, 3), round(max(xs) + CRT, 3)
    cy0, cy1 = round(min(ys) - CRT, 3), round(max(ys) + CRT, 3)
    lines = [f'(footprint "{name}"', '\t(version 20240108)', '\t(generator "rnext-draft-lands")', '\t(layer "F.Cu")',
             f'\t(descr "{descr}")', '\t(attr smd)',
             f'\t(property "Reference" "REF**" (at 0 {fmt(cy0 - 0.8)} 0) (layer "F.SilkS") (effects (font (size 0.8 0.8) (thickness 0.12))))',
             f'\t(property "Value" "{name}" (at 0 {fmt(cy1 + 0.8)} 0) (layer "F.Fab") (effects (font (size 0.8 0.8) (thickness 0.12))))']
    lines += rect('F.Fab', -body[0] / 2, -body[1] / 2, body[0] / 2, body[1] / 2, 0.1)
    lines += rect('F.CrtYd', cx0, cy0, cx1, cy1, 0.05)
    p1 = pads[0]
    lines.append(f'\t(fp_circle (center {fmt(p1[1] - p1[3] / 2 - 0.3)} {fmt(p1[2])}) (end {fmt(p1[1] - p1[3] / 2 - 0.2)} {fmt(p1[2])}) (stroke (width 0.12) (type solid)) (fill yes) (layer "F.SilkS"))')
    for num, x, y, w, h in pads:
        lines.append(f'\t(pad "{num}" smd roundrect (at {fmt(x)} {fmt(y)}) (size {fmt(w)} {fmt(h)}) (layers "F.Cu" "F.Paste" "F.Mask") (roundrect_rratio 0.1))')
    lines.append(')')
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, name + '.kicad_mod'), 'w') as f:
        f.write('\n'.join(lines) + '\n')
    return name, (cx1 - cx0, cy1 - cy0)


def testpad_array(name, descr, grid, pitch, dia, labels):
    """Bare round test pads (F.Cu + F.Mask, no paste). grid: rows of pad numbers, '' = empty site."""
    pads = []
    rows, cols = len(grid), len(grid[0])
    for r, row in enumerate(grid):
        for c, num in enumerate(row):
            if num:
                pads.append((num, (c - (cols - 1) / 2) * pitch, (r - (rows - 1) / 2) * pitch))
    hx, hy = (cols - 1) * pitch / 2 + dia / 2, (rows - 1) * pitch / 2 + dia / 2
    cx0, cx1, cy0, cy1 = round(-hx - CRT, 3), round(hx + CRT, 3), round(-hy - CRT, 3), round(hy + CRT, 3)
    lines = [f'(footprint "{name}"', '\t(version 20240108)', '\t(generator "rnext-draft-lands")', '\t(layer "F.Cu")',
             f'\t(descr "{descr}")', '\t(attr smd exclude_from_bom)',
             f'\t(property "Reference" "REF**" (at 0 {fmt(cy0 - 0.8)} 0) (layer "F.SilkS") (effects (font (size 0.8 0.8) (thickness 0.12))))',
             f'\t(property "Value" "{name}" (at 0 {fmt(cy1 + 0.8)} 0) (layer "F.Fab") (effects (font (size 0.8 0.8) (thickness 0.12))))']
    lines += rect('F.CrtYd', cx0, cy0, cx1, cy1, 0.05)
    lines += rect('F.SilkS', cx0, cy0, cx1, cy1, 0.12)
    for num, x, y in pads:
        lines.append(f'\t(pad "{num}" smd circle (at {fmt(x)} {fmt(y)}) (size {fmt(dia)} {fmt(dia)}) (layers "F.Cu" "F.Mask"))')
        lines.append(f'\t(fp_text user "{labels[num]}" (at {fmt(x)} {fmt(y)} 0) (layer "F.Fab") (effects (font (size 0.3 0.3) (thickness 0.05))))')
    lines.append(')')
    with open(os.path.join(OUT, name + '.kicad_mod'), 'w') as f:
        f.write('\n'.join(lines) + '\n')
    return name, (cx1 - cx0, cy1 - cy0)


def main():
    made = []
    # TI DBV0006A (SNOSD17G p34): 6X (1.1) x 6X (0.6), 2X (0.95) pitch, (2.6) row span; body 2.9 x 1.6 (DBV outline).
    made.append(land('SOT-23-6_DBV0006A_TI-EXAMPLE', 'DRAFT TI DBV0006A example land (SNOSD17G PDF p34): pads 0.6 x 1.1, pitch 0.95, row span 2.6. Numbering as zudo-pd SOT-23-6_L2.9-W1.6-P0.95-LS2.8-BL',
                     [('1', -0.95, 1.3, 0.6, 1.1), ('2', 0, 1.3, 0.6, 1.1), ('3', 0.95, 1.3, 0.6, 1.1),
                      ('4', 0.95, -1.3, 0.6, 1.1), ('5', 0, -1.3, 0.6, 1.1), ('6', -0.95, -1.3, 0.6, 1.1)], (2.9, 1.6)))
    # TI DRV0006A (SLVSED5C p19): 6X (0.45) x 6X (0.3), 4X (0.65) pitch, (1.95) row span, EP (1) x (1.6); body 2 x 2.
    made.append(land('WSON-6_DRV0006A_TI-EXAMPLE', 'DRAFT TI DRV0006A example land (SLVSED5C PDF p19): pads 0.3 x 0.45, pitch 0.65, row span 1.95, exposed pad 1.6 x 1.0. Numbering as zudo-pd WSON-6_L2.0-W2.0-P0.65-BL-EP',
                     [('1', -0.65, 0.975, 0.3, 0.45), ('2', 0, 0.975, 0.3, 0.45), ('3', 0.65, 0.975, 0.3, 0.45),
                      ('4', 0.65, -0.975, 0.3, 0.45), ('5', 0, -0.975, 0.3, 0.45), ('6', -0.65, -0.975, 0.3, 0.45),
                      ('7', 0, 0, 1.6, 1.0)], (2.0, 2.0)))
    # Diodes SOD123 (DS18004 PDF p4): X 0.900 x Y 0.950, X1 4.050 outer extent; body E 2.65 x D 1.55 typ.
    made.append(land('SOD-123_DIODES-SUGGESTED', 'DRAFT Diodes SOD123 suggested pad layout (DS18004 Rev. 38-2 PDF p4): pads 0.90 x 0.95, outer extent 4.05. Pad 1 = cathode as zudo-pd SOD-123_L2.8-W1.8-LS3.7-RD',
                     [('1', -1.575, 0, 0.9, 0.95), ('2', 1.575, 0, 0.9, 0.95)], (2.65, 1.55)))
    # J3 debug access (project choice, not a manufacturer land). Pad numbers = J3 pin numbers.
    # VBUS_IN (4) sits at a corner next to GND (5) and VBEN (8) only; the LV pins VREG_2V7 (3)
    # and ATT (6) sit at the far end. Pitch 1.5 mm / pad 1.0 mm are proposed hand-probe values.
    made.append(testpad_array('TestPadArray_2x4_P1.5_D1.0_J3', 'DRAFT J3 debug test-pad array, 2 x 4, pitch 1.5 mm, pad 1.0 mm, bare copper, no paste (project choice)',
                              [['4', '5', '1', '2'], ['8', '7', '6', '3']], 1.5, 1.0,
                              {'1': 'CC1DB', '2': 'CC2DB', '3': 'VREG', '4': 'VBUS_IN', '5': 'GND', '6': 'ATT', '7': 'PDOK', '8': 'VBEN'}))
    for name, crt in made:
        print(f'{name}: courtyard {crt[0]:.2f} x {crt[1]:.2f} mm')


if __name__ == '__main__':
    main()
