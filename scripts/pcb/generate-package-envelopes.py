#!/usr/bin/env python3
"""Generate conservative maximum-envelope package models for the Board P 20 V draft parts.

Run: uv run --python 3.12 --with cadquery==2.8.0 python scripts/pcb/generate-package-envelopes.py

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
    args = parser.parse_args()
    args.output_directory.mkdir(parents=True, exist_ok=True)
    for name, size, source in ENVELOPES:
        write_pair(args.output_directory, name, size, source)


if __name__ == '__main__':
    main()
