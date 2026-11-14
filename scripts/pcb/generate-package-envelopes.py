#!/usr/bin/env python3
"""Generate conservative maximum-envelope package models for the Board P 20 V and B20 draft parts.

Run: uv run --python 3.12 --with cadquery==2.6.1 --with vtk==9.3.1 python scripts/pcb/generate-package-envelopes.py [--only NAME ...]

Each model is a plain box at the package's maximum body length, width and height, read
from the manufacturer package outline. The box is centered on the footprint origin with
the seating plane at Z=0. No lead, exposed pad, fillet, marking or internal geometry is
invented; these are visualization envelopes, not manufacturer CAD. The land patterns
remain authoritative and are unaffected.
"""
import argparse
from pathlib import Path
import cadquery as cq

ROOT = Path(__file__).resolve().parents[2]

# (model name, (length, width, height) in mm, outline source); maxima from each outline.
ENVELOPES = [
    ('VQFN-24_RGE_MaxEnvelope_L4.1-W4.1-H1.0', (4.1, 4.1, 1.0),
     'TI TPS2663 SLVSE94G RGE0024H outline: 3.9-4.1 x 3.9-4.1 mm, 1 mm max height'),
    ('WSON-6_DRV_MaxEnvelope_L2.1-W2.1-H0.8', (2.1, 2.1, 0.8),
     'TI TVS2200 DRV0006A outline: 1.9-2.1 x 1.9-2.1 mm, 0.8 mm max height'),
    ('SON-8_Q3A_MaxEnvelope_L3.25-W3.25-H0.9', (3.25, 3.25, 0.9),
     'TI CSD18543Q3A SLPS633 7.1 Q3A outline: 2.9-3.1 and 3.05-3.25 mm body, 0.9 mm max; both sides use the 3.25 mm maximum'),
    ('PowerDI3333-8_MaxEnvelope_L3.35-W3.35-H0.85', (3.35, 3.35, 0.85),
     'Diodes DMP3036SFG DS37038 PowerDI3333-8 outline: D and E 3.25-3.35 mm, A 0.75-0.85 mm'),
    # Footprint pins run along Y, so the box is X 4.5 (body width) by Y 6.6 (body length).
    ('HTSSOP-20_PWP_MaxEnvelope_W4.5-L6.6-H1.2', (4.5, 6.6, 1.2),
     'TI TPS1663 SLVSET9G PWP0020T outline 4224598/A: body 6.4-6.6 x 4.3-4.5 mm, 1.2 mm max height'),
    ('SOT-23-6_DBV_MaxEnvelope_L3.05-W1.75-H1.45', (3.05, 1.75, 1.45),
     'TI LM74700-Q1 SNOSD17G DBV0006A outline 4214840/G: body 2.75-3.05 x 1.45-1.75 mm, 1.45 mm max height'),
    # Footprint pins 1/2 and 3 face X, so the box is X 1.4 (E1 body width) by Y 3.0 (D body length).
    ('SOT-23_DS30144_MaxEnvelope_W1.4-L3.0-H1.15', (1.4, 3.0, 1.15),
     'Diodes BSS138 DS30144 Rev. 25-2 SOT23 (Standard) outline: D 2.80-3.00, E1 1.20-1.40 mm, A 0.90-1.15 mm'),
    # B20 draft lands (phase 32). IC pad rows face X, so X is the body width and Y the body length.
    ('HSOP-8_DDA_MaxEnvelope_W4.0-L5.0-H1.7', (4.0, 5.0, 1.7),
     'TI TPS54560 SLVSBN0C DDA0008B outline 4214849/B: body 4.8-5.0 x 3.8-4.0 mm (flash excluded), 1.7 mm max height'),
    ('VSSOP-8_DGK_MaxEnvelope_W3.1-L3.1-H1.1', (3.1, 3.1, 1.1),
     'TI OPA2187 SBOS807E DGK0008A outline 4214862/A: body 2.9-3.1 x 2.9-3.1 mm (flash excluded), 1.1 mm max height'),
    ('SOIC-8_D_MaxEnvelope_W3.98-L5.0-H1.75', (3.98, 5.0, 1.75),
     'TI REF5025 SBOS410O D0008A outline 4214825/C: body 4.81-5.00 x 3.81-3.98 mm (flash excluded), 1.75 mm max height'),
    # Two-terminal lands have their pads on X.
    ('R1206_MaxEnvelope_L3.45-W1.85-H0.89', (3.45, 1.85, 0.89),
     'YAGEO PE1206FRF470R02L sheet: L 3.2 +/-0.25, W 1.6 +/-0.25, T 0.64 +/-0.25 mm (it also covers the UNI-ROYAL 1206 3.10 +/-0.15 x 1.55 +0.15 x 0.55 +/-0.10 mm body)'),
    ('R2512_PCSR2512_MaxEnvelope_L6.6-W3.4-H0.9', (6.6, 3.4, 0.9),
     'RESI PCSR2512 sheet V8 (distributor-hosted copy, UNSOURCED): L 6.4 +/-0.2, W 3.2 +/-0.2, T 0.8 +/-0.1 mm'),
    ('R2512_WSL_MaxEnvelope_L6.61-W3.44-H0.89', (6.61, 3.44, 0.89),
     'Vishay WSL doc 30100 (23-Nov-2023) WSL2512 0.007-0.5 ohm row: L 0.250 +/-0.010 in, W 0.125 +/-0.010 in, H 0.025 +/-0.010 in'),
    ('C1206_HCN_C5451690_MaxEnvelope_L3.5-W1.8-H1.8', (3.5, 1.8, 1.8),
     'Holy Stone HCN catalog (source identity retained in the CAD evidence receipt): PDF page3 1206 L3.20+/-0.30 W1.60+/-0.20 Tmax1.80; PDF page6 exact C1206N473J050T thickness E1.6+/-0.2 mm'),
    ('SMC_MaxEnvelope_L8.13-W6.22-H2.5', (8.13, 6.22, 2.5),
     'Diodes DS13012 Rev. 19-2 SMC outline: E 7.75-8.13 mm over the leads, A 5.59-6.22 mm body width, J 2.00-2.50 mm height'),
]


def write_pair(dest, name, size, source):
    shape = cq.Workplane('XY').box(*size, centered=(True, True, False))
    cq.exporters.export(shape, str(dest/(name+'.step')))
    # KiCad WRL model coordinates use 0.1 inch (2.54 mm) units.
    x, y, z = (value/2.54 for value in size)
    vertices = [(-x/2,-y/2,0),(x/2,-y/2,0),(x/2,y/2,0),(-x/2,y/2,0),
                (-x/2,-y/2,z),(x/2,-y/2,z),(x/2,y/2,z),(-x/2,y/2,z)]
    faces = [(0,3,2),(0,2,1),(4,5,6),(4,6,7),(0,1,5),(0,5,4),
             (1,2,6),(1,6,5),(2,3,7),(2,7,6),(3,0,4),(3,4,7)]
    points = ',\n'.join('      '+' '.join(f'{value:.12g}' for value in vertex) for vertex in vertices)
    indices = ',\n'.join('      '+','.join(map(str,face))+',-1' for face in faces)
    extent = ' x '.join(f'{value:g}' for value in size)
    wrl = ('#VRML V2.0 utf8\n'
           '# PROJECT VISUALIZATION ONLY: conservative maximum package envelope.\n'
           f'# {source}; not manufacturer CAD or exact terminal geometry.\n'
           f'# Extent: {extent} mm; centered in XY; seating plane Z=0.\n'
           'Shape {\n  appearance Appearance { material Material { diffuseColor 0.24 0.24 0.24 } }\n'
           '  geometry IndexedFaceSet {\n    ccw TRUE\n    solid TRUE\n'
           '    coord Coordinate { point [\n'+points+'\n    ] }\n'
           '    coordIndex [\n'+indices+'\n    ]\n  }\n}\n')
    (dest/(name+'.wrl')).write_text(wrl)
    bounds = cq.importers.importStep(str(dest/(name+'.step'))).val().BoundingBox()
    actual = (bounds.xlen, bounds.ylen, bounds.zlen)
    if any(abs(a-b) > 1e-6 for a, b in zip(actual, size)):
        raise ValueError(f'{name}: STEP readback dimensions differ from the documented envelope')
    print(f'{name}: STEP readback {actual} mm; maximum envelope only')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-directory', type=Path, default=ROOT/'footprints/kicad/zudo-pd.3dshapes')
    parser.add_argument('--only', nargs='+', metavar='NAME', help='write only these model names')
    args = parser.parse_args()
    args.output_directory.mkdir(parents=True, exist_ok=True)
    known = {name for name, _, _ in ENVELOPES}
    if args.only and not set(args.only) <= known:
        parser.error(f'unknown model names: {sorted(set(args.only) - known)}')
    for name, size, source in ENVELOPES:
        if args.only and name not in args.only:
            continue
        write_pair(args.output_directory, name, size, source)


if __name__ == '__main__':
    main()
