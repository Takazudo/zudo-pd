#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11,<3.14"
# dependencies = ["cadquery==2.6.1"]
# ///
"""Align the existing Faston STEP companion with its reviewed WRL datum.

Only a rigid translation is permitted. Shape, volume and terminal pitch remain
unchanged. Already-normalized files are checked and left byte-identical.
"""
from pathlib import Path
import hashlib,json,re
import cadquery as cq

ROOT=Path(__file__).resolve().parents[2]
STEP=ROOT/'footprints/kicad/zudo-pd.3dshapes/CONN-TH_63951-1.step'
WRL=STEP.with_suffix('.wrl')
TRANSLATION=(6.9,.005,5.725)
TARGET=(-3.26,-.40505,-3.8,17.06,.40505,8.9)


def limits(shape):
    b=shape.BoundingBox()
    return [getattr(b,n) for n in ('xmin','ymin','zmin','xmax','ymax','zmax')]


def vertices_wrl():
    result=[]
    for block in re.findall(r'point\s*\[([^]]+)\]',WRL.read_text()):
        n=[float(v) for v in re.findall(r'[-+]?(?:\d*\.\d+|\d+)(?:[Ee][+-]?\d+)?',block)]
        result.extend(tuple(n[i+k]*2.54 for k in range(3)) for i in range(0,len(n),3))
    return result


def leg_center(vertices,sign):
    rows=[v for v in vertices if v[2]<-1.6 and v[0]*sign>0]
    return [(min(v[k] for v in rows)+max(v[k] for v in rows))/2 for k in [0,1]]


def main():
    original_sha=hashlib.sha256(STEP.read_bytes()).hexdigest()
    shape=cq.importers.importStep(str(STEP)).val();old_volume=shape.Volume()
    before=limits(shape);already=all(abs(a-b)<.001 for a,b in zip(before,TARGET))
    if not already:
        expected=[TARGET[i]-TRANSLATION[i%3] for i in range(6)]
        if any(abs(a-b)>.001 for a,b in zip(before,expected)):
            raise ValueError('Unrecognized STEP datum; do not guess another transform')
        shape=shape.translate(TRANSLATION)
    vertices=[v.toTuple() for v in shape.Vertices()];wrl=vertices_wrl()
    checks=[]
    for sign in [-1,1]:
        actual,want=leg_center(vertices,sign),leg_center(wrl,sign)
        if any(abs(a-b)>.001 for a,b in zip(actual,want)):
            raise ValueError('STEP/WRL solder-leg centers differ')
        checks.append({'sign':sign,'step_center_mm':actual,'wrl_center_mm':want})
    if abs(shape.Volume()-old_volume)>1e-5:raise ValueError('Rigid translation changed volume')
    if not already:cq.exporters.export(shape,str(STEP))
    content=STEP.read_text();clean='\n'.join(line.rstrip() for line in content.splitlines())+'\n'
    if content!=clean:STEP.write_text(clean)
    print(json.dumps({'status':'PASS','already_normalized':already,'translation_mm':TRANSLATION,
                      'before_bounds_mm':before,'after_bounds_mm':limits(shape),'leg_checks':checks,
                      'original_sha256':original_sha,'normalized_sha256':hashlib.sha256(STEP.read_bytes()).hexdigest()},indent=2))


if __name__=='__main__':main()
