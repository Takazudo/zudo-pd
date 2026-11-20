#!/usr/bin/env python3
"""Non-replay subset of scripts/pcb/verify-jlcpcb.py for board-p15 only.
Skips: SHA256SUMS entries for the absent local-only STEP (reported), and the manifest source-hash lock
(fixed snapshot; checked separately by verify-shared-reference.py). Writes nothing in the repository."""
import csv,hashlib,importlib,json,math,re,sys,warnings,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4]
sys.path.insert(0,str(ROOT/'scripts/pcb')); sys.path.insert(0,str(ROOT/'scripts/schgen'))
from sexp import atom,find_all,load
from gerbonara import LayerStack
rel=ROOT/'manufacturing/releases/corner-support-review'; name='board-p15'; dest=rel/name
out={'board':name,'checks':{}}
def req(k,ok,msg=''):
    out['checks'][k]='PASS' if ok else f'FAIL {msg}'
def props(n): return {atom(x[1]):atom(x[2]) for x in find_all(n,'property')}
def rows(p):
    with p.open() as f: return list(csv.DictReader(f))
missing=[];bad=[];ok=0
for line in (rel/'SHA256SUMS').read_text().splitlines():
    sha,r=line.split('  ',1); p=rel/r
    if not p.exists(): missing.append(r); continue
    if hashlib.sha256(p.read_bytes()).hexdigest()!=sha: bad.append(r)
    else: ok+=1
out['sha256sums']={'ok':ok,'mismatch':bad,'absent':missing}
man=json.loads((rel/'manifest.json').read_text())
am=[r for r,s in man['artifact_hashes'].items() if (rel/r).exists() and hashlib.sha256((rel/r).read_bytes()).hexdigest()!=s]
out['manifest_artifact_hashes']={'checked':len(man['artifact_hashes']),'mismatch':am,'absent':[r for r in man['artifact_hashes'] if not (rel/r).exists()]}
rec=[r for r in man['boards'] if r['board']==name][0]
req('copper_layers',tuple(rec.get('copper_layers',()))==('F.Cu','B.Cu'))
spec=importlib.import_module('board_p15_spec')
expected={ref:c[2] for ref,c in spec.COMPONENTS.items() if c[2] and not c[4]}
bom={}
for row in rows(dest/'bom.csv'):
    for ref in row['Designator'].split(','): bom[ref]=row['JLCPCB Part #']
req('bom_vs_HEAD_spec',bom==expected,str(set(bom.items())^set(expected.items())))
cpl=rows(dest/'cpl.csv')
req('cpl_vs_bom',len(cpl)==len(expected) and {r['Designator'] for r in cpl}==set(expected))
board=load(dest/'source'/(name+'.kicad_pcb'))
fps={props(fp)['Reference']:fp for fp in find_all(board,'footprint')}
raw={r['Ref']:r for r in rows(dest/'raw/positions.csv')}
ox,oy=rec['origin_mm']; errs=[]
for row in cpl:
    ref=row['Designator'];fp=fps[ref];at=find_all(fp,'at')[0]
    x,y=float(row['Mid X'].removesuffix('mm')),float(row['Mid Y'].removesuffix('mm'))
    if not(abs(x-(float(atom(at[1]))-ox))<1e-4 and abs(y-(oy-float(atom(at[2]))))<1e-4): errs.append(ref+' coord')
    layer=atom(find_all(fp,'layer')[0][1])
    if row['Layer']!=('Top' if layer=='F.Cu' else 'Bottom'): errs.append(ref+' side')
    if not math.isclose(float(row['Rotation']),float(raw[ref]['Rot'])%360,abs_tol=1e-4): errs.append(ref+' rot')
    if props(fp)['LCSC']!=expected[ref]: errs.append(ref+' lcsc')
req('cpl_vs_package_source_pcb',not errs,str(errs))
drc=json.loads((dest/'checks/drc.json').read_text()); erc=json.loads((dest/'checks/erc.json').read_text())
req('drc_unconnected_zero',not drc['unconnected_items'])
req('drc_no_errors',not any(v['severity']=='error' for k in ('violations','schematic_parity') for v in drc[k]))
req('erc_no_errors',not any(v['severity']=='error' for s in erc['sheets'] for v in s['violations']))
arc=dest/(name+'-gerbers.zip')
with zipfile.ZipFile(arc) as z:
    req('zip_integrity',z.testzip() is None)
    req('zip_equals_gerbers_dir',set(z.namelist())=={p.name for p in (dest/'gerbers').iterdir()} and all(z.read(p.name)==p.read_bytes() for p in (dest/'gerbers').iterdir()))
    out['zip_members']=sorted(z.namelist())
with warnings.catch_warnings(record=True) as caught:
    warnings.simplefilter('always'); st=LayerStack.open(arc)
notes=[re.sub(r'\S*/input/','',str(w.message)) for w in caught if not issubclass(w.category,ResourceWarning)]
req('gerber_parser_warnings_expected_only',all('G90 header statement found after end of header' in n for n in notes),str(notes))
req('two_copper_plus_pth_npth',len(st.copper_layers)==2 and st.drill_pth is not None and st.drill_npth is not None)
w,h=st.outline.size('mm'); out['outline_mm']=[round(w,3),round(h,3)]
req('outline_27x40',abs(w-27)<.06 and abs(h-40)<.06)
# PCB at HEAD vs package source PCB
head=hashlib.sha256((ROOT/'boards/board-p15/board-p15-draft.kicad_pcb').read_bytes()).hexdigest()
lock=rec['source_hashes'].get('boards/board-p15/board-p15-draft.kicad_pcb')
out['head_pcb_sha256']=head; out['lock_pcb_sha256']=lock
req('head_pcb_equals_lock',head==lock)
sl=rec['source_hashes']; ch=[p for p,s in sl.items() if not (ROOT/p).exists() or hashlib.sha256((ROOT/p).read_bytes()).hexdigest()!=s]
out['source_lock_at_HEAD']={'paths':len(sl),'changed':len(ch),'changed_paths':ch}
out['overall']='PASS' if all(v=='PASS' for v in out['checks'].values()) and not bad and not am else 'FAIL'
print(json.dumps(out,indent=1))
