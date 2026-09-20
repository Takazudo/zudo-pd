#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11,<3.14"
# dependencies = ["cadquery==2.6.1"]
# ///
"""Align the exact socket STEP companion to its existing WRL datum.

Only a rigid translation is applied. Verify all16 solder-tail centers against
the WRL and preserve solid count/volume; already-normalized geometry is kept.
"""
from pathlib import Path
import hashlib,json,re
import cadquery as cq
ROOT=Path(__file__).resolve().parents[2]
STEP=ROOT/'footprints/kicad/zudo-pd.3dshapes/IDC-TH_16P-P2.54_321016RG0ABK00A01.step'
WRL=STEP.with_suffix('.wrl');TRANSLATION=(11.42,-3.276,8.75)
TARGET=(-13.96,-12.076,-3,13.96,1.584,8.701)

def bounds(s):
 b=s.BoundingBox();return [getattr(b,n) for n in ['xmin','ymin','zmin','xmax','ymax','zmax']]

def main():
 old_hash=hashlib.sha256(STEP.read_bytes()).hexdigest();s=cq.importers.importStep(str(STEP)).val();old_volume=s.Volume();old_count=len(s.Solids());before=bounds(s)
 already=all(abs(a-b)<.002 for a,b in zip(before,TARGET))
 if not already:
  expected=[TARGET[i]-TRANSLATION[i%3] for i in range(6)]
  if any(abs(a-b)>.002 for a,b in zip(before,expected)):raise ValueError('Unrecognized socket datum')
  s=s.translate(TRANSLATION)
 raw=[]
 for block in re.findall(r'point\s*\[([^]]+)\]',WRL.read_text()):
  n=[float(v) for v in re.findall(r'[-+]?(?:\d*\.\d+|\d+)(?:[Ee][+-]?\d+)?',block)]
  raw.extend(tuple(n[i+k]*2.54 for k in range(3)) for i in range(0,len(n),3))
 tails=[]
 for solid in s.Solids():
  v=[a.toTuple() for a in solid.Vertices() if a.Z<-1.6]
  if not v:continue
  center=[(min(a[k] for a in v)+max(a[k] for a in v))/2 for k in [0,1]]
  matching=[a for a in raw if a[2]<-1.6 and abs(a[0]-center[0])<.5 and abs(a[1]-center[1])<.5]
  if not matching:raise ValueError('No matching WRL tail')
  want=[(min(a[k] for a in matching)+max(a[k] for a in matching))/2 for k in [0,1]]
  if any(abs(a-b)>.002 for a,b in zip(center,want)):raise ValueError('STEP/WRL tail mismatch')
  tails.append({'step_center_mm':center,'wrl_center_mm':want})
 if len(tails)!=16:raise ValueError('Expected16 solder tails')
 if len(s.Solids())!=old_count or abs(s.Volume()-old_volume)>1e-4:raise ValueError('Rigid correction changed geometry')
 if not already:cq.exporters.export(s,str(STEP))
 content=STEP.read_text();clean='\n'.join(line.rstrip() for line in content.splitlines())+'\n'
 if content!=clean:STEP.write_text(clean)
 print(json.dumps({'status':'PASS','already_normalized':already,'translation_mm':TRANSLATION,'before_bounds_mm':before,'after_bounds_mm':bounds(s),'tail_checks':tails,'solid_count':old_count,'old_sha256':old_hash,'normalized_sha256':hashlib.sha256(STEP.read_bytes()).hexdigest()},indent=2))
if __name__=='__main__':main()
