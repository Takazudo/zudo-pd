#!/usr/bin/env python3
"""Generate a conservative ASPI-0630LR visualization envelope, not exact CAD.

Run: uv run --python 3.12 --with cadquery==2.8.0 python scripts/pcb/generate-aspi-envelope.py

Abracon ASPI-0630LR Rev C (2022-11-08), page7, gives A=7.1±0.4,
B=6.6±0.25 and C=2.8±0.2 mm. The visible box uses maximum7.5×6.85×3.0 mm.
No terminal, fillet, marking or internal geometry is invented. The two-terminal
land pattern remains authoritative and is unaffected by this model.
"""
import argparse
from pathlib import Path
import cadquery as cq

ROOT = Path(__file__).resolve().parents[2]
NAME = 'ASPI-0630LR_MaxEnvelope_L7.5-W6.85-H3.0'
SIZE_MM = (7.5, 6.85, 3.0)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-directory', type=Path, default=ROOT/'footprints/kicad/zudo-pd.3dshapes')
    args = parser.parse_args()
    dest = args.output_directory
    dest.mkdir(parents=True, exist_ok=True)
    shape = cq.Workplane('XY').box(*SIZE_MM, centered=(True, True, False))
    cq.exporters.export(shape, str(dest/(NAME+'.step')))
    # KiCad WRL model coordinates use 0.1 inch (2.54 mm) units.
    x, y, z = (value/2.54 for value in SIZE_MM)
    vertices = [(-x/2,-y/2,0),(x/2,-y/2,0),(x/2,y/2,0),(-x/2,y/2,0),
                (-x/2,-y/2,z),(x/2,-y/2,z),(x/2,y/2,z),(-x/2,y/2,z)]
    faces = [(0,3,2),(0,2,1),(4,5,6),(4,6,7),(0,1,5),(0,5,4),
             (1,2,6),(1,6,5),(2,3,7),(2,7,6),(3,0,4),(3,4,7)]
    points = ',\n'.join('      '+' '.join(f'{value:.12g}' for value in vertex) for vertex in vertices)
    indices = ',\n'.join('      '+','.join(map(str,face))+',-1' for face in faces)
    wrl = ('#VRML V2.0 utf8\n'
           '# PROJECT VISUALIZATION ONLY: conservative maximum package envelope.\n'
           '# Abracon ASPI-0630LR Rev C page7; not manufacturer CAD or exact terminal geometry.\n'
           '# Extent: 7.5 x 6.85 x 3.0 mm; centered in XY; seating plane Z=0.\n'
           'Shape {\n  appearance Appearance { material Material { diffuseColor 0.24 0.24 0.24 } }\n'
           '  geometry IndexedFaceSet {\n    ccw TRUE\n    solid TRUE\n'
           '    coord Coordinate { point [\n'+points+'\n    ] }\n'
           '    coordIndex [\n'+indices+'\n    ]\n  }\n}\n')
    (dest/(NAME+'.wrl')).write_text(wrl)
    imported = cq.importers.importStep(str(dest/(NAME+'.step'))).val()
    bounds = imported.BoundingBox()
    actual = (bounds.xlen,bounds.ylen,bounds.zlen)
    if any(abs(a-b)>1e-6 for a,b in zip(actual,SIZE_MM)):
        raise ValueError('STEP readback dimensions differ from the documented envelope')
    print(f'{NAME}: STEP readback {actual} mm; maximum envelope only')


if __name__ == '__main__':
    main()
