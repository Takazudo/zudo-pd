#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11,<3.14"
# dependencies = ["cadquery==2.6.1"]
# ///
"""Create a portable review-only B+P assembly without modifying either source PCB.

Native KiCad STEP exports establish PCB Z datums. Board P is stacked using the
reviewed in-plane transform and nominal spacing. Terminal/PD clearance includes
a conservative 4.7 mm tail envelope because the catalog terminal mesh is shorter.
This is nominal CAD screening, not physical fit or electrical qualification.
"""
import argparse
import copy
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import uuid

import cadquery as cq

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'scripts/schgen'))
from sexp import atom,find_all,load,parse,tokenize


def require(ok,message):
    if not ok:raise ValueError(message)


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def serialize(node):
    if isinstance(node,list):return '('+' '.join(serialize(v) for v in node)+')'
    return json.dumps(node[1],ensure_ascii=False) if node[0]=='str' else node[1]


def properties(node):return {atom(item[1]):atom(item[2]) for item in find_all(node,'property')}


def bounds(shape):
    b=shape.BoundingBox();return [b.xmin,b.ymin,b.zmin,b.xmax,b.ymax,b.zmax]


def overlaps(a,b):
    aa,bb=bounds(a),bounds(b)
    return all(aa[k]<bb[k+3]-.0001 and aa[k+3]>bb[k]+.0001 for k in range(3))


def resolve_model(model,project):
    path=Path(atom(model[1]).replace('${KIPRJMOD}',str(project)))
    if not path.is_absolute():path=project/path
    path=path.resolve()
    require(path.is_file() and path.is_relative_to(ROOT),'Unavailable/nonlocal model: '+str(path))
    return path


def command(args):
    result=subprocess.run([str(v) for v in args],capture_output=True,text=True)
    require(result.returncode==0,'Command failed: '+result.stdout+result.stderr)
    return result.stdout


def native_parts(tree,project,scratch,cli):
    work=copy.deepcopy(tree);sources={}
    for footprint in find_all(work,'footprint'):
        for model in find_all(footprint,'model'):
            path=resolve_model(model,project)
            step=path.with_suffix('.step') if path.suffix.lower()=='.wrl' else path
            require(step.is_file(),'Missing STEP companion: '+str(step))
            for source in (path,step):sources[str(source.relative_to(ROOT))]=sha(source)
            model[1]=('str',str(step))
    temporary=scratch/'native-export.kicad_pcb';temporary.write_text(serialize(work)+'\n')
    exported=[]
    for tag,flags in [('core',['--board-only']),('populated',[])]:
        output=scratch/(tag+'.step')
        command([cli,'pcb','export','step','--force','--no-dnp','--output',output,*flags,temporary])
        exported.append(cq.importers.importStep(str(output)).val())
    core,whole=exported;bb=bounds(core)
    stackup=find_all(find_all(tree,'setup')[0],'stackup')
    require(len(stackup)==1,'Explicit PCB stackup required')
    thickness={atom(layer[1]):float(atom(find_all(layer,'thickness')[0][1])) for layer in find_all(stackup[0],'layer') if find_all(layer,'thickness')}
    require(abs(sum(thickness.values())-1.6)<.001,'Expected 1.6 mm complete PCB stackup')
    lower=thickness['B.Cu']+thickness['B.Mask'];upper=thickness['F.Cu']+thickness['F.Mask']
    require(abs(bb[5]-bb[2]-(1.6-lower-upper))<.003,'Native STEP core disagrees with stackup')
    shift=-1.6+lower-bb[2]
    solids=whole.Solids();cores=[part for part in solids if all(abs(a-b)<.003 for a,b in zip(bounds(part),bb))]
    require(len(cores)==1,'Native substrate is not uniquely identifiable')
    parts=[part.translate((0,0,shift)) for part in solids if part not in cores]
    return core.translate((0,0,shift)),parts,sources,{'native_core_bounds_mm':bb,'world_z_translation_mm':shift,'component_solids':len(parts)}


def clean_step(path):path.write_text('\n'.join(line.rstrip() for line in path.read_text().splitlines())+'\n')


def without_models(tree):
    result=copy.deepcopy(tree)
    for footprint in find_all(result,'footprint'):
        for model in list(find_all(footprint,'model')):footprint.remove(model)
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--board-b',type=Path,default=ROOT/'boards/board-b/board-b.kicad_pcb')
    parser.add_argument('--project-dir',type=Path)
    parser.add_argument('--output',type=Path,default=ROOT/'boards/board-b/assembly-preview')
    parser.add_argument('--kicad-cli',default=shutil.which('kicad-cli'))
    parser.add_argument('--kicad-python',default='/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3')
    args=parser.parse_args();require(args.kicad_cli,'kicad-cli is required')
    b_pcb=args.board_b.resolve();p_pcb=ROOT/'boards/board-p/board-p.kicad_pcb';project=(args.project_dir or b_pcb.parent).resolve()
    output=args.output.resolve();require(not output.exists(),'Choose a new preview output directory; never overwrite an existing review')
    b_tree,p_tree=load(b_pcb),load(p_pcb);source_hashes={'board-b':sha(b_pcb),'board-p':sha(p_pcb)}
    contract_path=ROOT/'boards/board-b/mechanical.json';contract=json.loads(contract_path.read_text())
    contract_hash=sha(contract_path);generator_hash=sha(Path(__file__))
    verification_sources={str(path.relative_to(ROOT)):sha(path) for path in
                          [ROOT/'scripts/pcb/verify-board-b.py',ROOT/'scripts/pcb/verify-compact-mechanics.py',ROOT/'scripts/pcb/board_b_layout.py']}
    require(contract['terminal_blocks']['maximum_tail_projection_mm']==4.7,'Unreviewed terminal tail envelope')
    output.mkdir(parents=True)
    command([args.kicad_python,ROOT/'scripts/pcb/verify-board-b.py',b_pcb,'--project-dir',project,'--output',output/'mechanical-check.json'])
    with tempfile.TemporaryDirectory(prefix='zudo-pd-assembly-') as temporary:
        scratch=Path(temporary);(scratch/'b').mkdir();(scratch/'p').mkdir()
        b_core,b_parts,b_sources,b_datum=native_parts(b_tree,project,scratch/'b',args.kicad_cli)
        p_core,p_parts,p_sources,p_datum=native_parts(p_tree,p_pcb.parent,scratch/'p',args.kicad_cli)
        def place_p(shape):return shape.rotate((0,0,0),(0,0,1),90).translate((0,-27,contract['pd_stack']['nominal_board_p_top_z_mm']))
        p_core=place_p(p_core);p_parts=[place_p(part) for part in p_parts]
        terminal_screens=[]
        for item in contract['terminal_blocks']['placements']:
            ref=item['reference'];fp=next(f for f in find_all(b_tree,'footprint') if properties(f).get('Reference')==ref)
            model=find_all(fp,'model')[0];model_path=resolve_model(model,project)
            local=cq.importers.importStep(str(model_path.with_suffix('.step'))).val()
            fx,fy=item['center_mm'];shape=local.rotate((0,0,0),(0,0,1),90).translate((fx,-fy,0))
            # A 1 x 1 mm box around each pin exceeds the drawing's maximum
            # 0.95 x 0.85 mm pin section.
            tails=[]
            for lx,ly in contract['terminal_blocks']['pad_centers_local_mm'].values():
                px,py=fx+ly,fy-lx
                tails.append(cq.Workplane('XY').box(1,1,4.7).translate((px,-py,-2.35)).val())
            compared=0;worst=0
            for candidate in [shape,*tails]:
                for part in [p_core,*p_parts]:
                    if not overlaps(candidate,part):continue
                    volume=candidate.intersect(part).Volume();compared+=1;worst=max(worst,volume)
                    require(volume<=.005,f'{ref}: terminal or conservative tail envelope intersects Board P')
            terminal_screens.append({'reference':ref,'status':'PASS','maximum_tail_projection_mm':4.7,'tail_cross_section_envelope_mm':[1,1],
                                     'overlapping_bbox_pairs_checked':compared,'maximum_intersection_mm3':worst,'terminal_world_bounds_mm':bounds(shape)})
        stacked=cq.Assembly(name='zudo_pd_board_p_stacked')
        stacked.add(p_core,name='substrate',color=cq.Color(.15,.47,.25))
        for i,part in enumerate(p_parts):stacked.add(part,name=f'component_{i}',color=cq.Color(.63,.65,.67))
        stacked.export(str(output/'board-p-stacked.step'));clean_step(output/'board-p-stacked.step')
        assembly=cq.Assembly(name='zudo_pd_terminal_stack_review')
        assembly.add(b_core,name='board_b_substrate',color=cq.Color(.10,.38,.20));assembly.add(p_core,name='board_p_substrate',color=cq.Color(.15,.47,.25))
        for tag,parts in [('b',b_parts),('p',p_parts)]:
            for i,part in enumerate(parts):assembly.add(part,name=f'board_{tag}_component_{i}',color=cq.Color(.63,.65,.67))
        assembly.export(str(output/'populated-stack.step'));clean_step(output/'populated-stack.step')
    preview=copy.deepcopy(b_tree);models=output/'models';models.mkdir()
    for fp in find_all(preview,'footprint'):
        for model in find_all(fp,'model'):
            path=resolve_model(model,project)
            for asset in (path,path.with_suffix('.step')):
                require(asset.is_file(),'Missing preview companion: '+str(asset));target=models/asset.name
                if target.exists():require(sha(target)==sha(asset),'Conflicting preview model basename')
                else:shutil.copyfile(asset,target)
            model[1]=('str','${KIPRJMOD}/models/'+path.name)
    mechanical='(footprint "zudo-pd:Mechanical_Preview" (layer "F.Cu") (at 0 0) (uuid "'+str(uuid.uuid5(uuid.NAMESPACE_URL,'zudo-pd/terminal-assembly-preview'))+'") (property "Reference" "PD_PREVIEW" (at 0 0) (layer "F.Fab") (effects (font (size 1 1)) hide)) (property "Value" "PD_STACK_REVIEW_ONLY" (at 0 0) (layer "F.Fab") (effects (font (size 1 1)) hide)) (attr board_only exclude_from_pos_files exclude_from_bom) (model "${KIPRJMOD}/board-p-stacked.step" (offset (xyz 0 0 0)) (scale (xyz 1 1 1)) (rotate (xyz 0 0 0))))'
    preview.append(parse(tokenize(mechanical)))
    restored=copy.deepcopy(preview);restored.pop()
    require(without_models(restored)==without_models(b_tree),'Preview changed original B non-model geometry')
    preview_path=output/'preview.kicad_pcb';preview_path.write_text(serialize(preview)+'\n')
    source_project=project/'board-b.kicad_pro'
    if source_project.exists():shutil.copyfile(source_project,output/'preview.kicad_pro')
    command([sys.executable,ROOT/'scripts/pcb/check-model-paths.py',preview_path,'--output',output/'model-paths.json'])
    for side in ('top','bottom'):
        command([args.kicad_cli,'pcb','render','--side',side,'--rotate','20,0,-15','--width','1800','--height','1400','--quality','high','--zoom','.8','--output',output/(side+'.png'),preview_path])
    sources={**b_sources,**p_sources}
    for name,expected in sources.items():require(sha(ROOT/name)==expected,'Component model changed during preview generation')
    require(sha(b_pcb)==source_hashes['board-b'] and sha(p_pcb)==source_hashes['board-p'],'Source PCB changed during preview generation')
    require(sha(contract_path)==contract_hash and sha(Path(__file__))==generator_hash,'Preview generator or mechanical contract changed during generation')
    for name,expected in verification_sources.items():require(sha(ROOT/name)==expected,'Mechanical verifier changed during generation')
    (output/'README.md').write_text('Review-only assembly. Open preview.kicad_pcb in KiCad and use its 3D viewer. Component models are bundled locally; no global model path is needed. This file adds one BOM/CPL-excluded display footprint for Board P and must not be used for fabrication. The source PCBs are unchanged. Nominal CAD fit does not qualify installed hardware, wire/screwdriver access or powered behavior.\n')
    report={'schema_version':1,'status':'PASS','pcb_sha256':source_hashes,'generator_sha256':generator_hash,
            'mechanical_spec_sha256':contract_hash,'model_sources_sha256':sources,'verification_sources_sha256':verification_sources,
            'original_B_nonmodel_geometry_unchanged':True,'model_only_footprints_added':1,'manufacturing_use':False,
            'pd_transform':'P(x,y) -> B(y,27-x)','board_p_top_z_mm':contract['pd_stack']['nominal_board_p_top_z_mm'],
            'native_step_datums':{'board-b':b_datum,'board-p':p_datum},'terminal_to_pd_clearance':terminal_screens,
            'limits':['Catalog model geometry is illustrative; physical fit remains unmeasured.','The 4.7 mm tail envelopes address the catalog mesh/drawing tail-length difference.','Only the new terminals versus stacked Board P were screened; this is not a full all-pairs collision or electrical qualification.'],
            'artifact_sha256':{str(path.relative_to(output)):sha(path) for path in sorted(output.rglob('*')) if path.is_file()}}
    (output/'verification.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'status':'PASS','output':str(output),'pcb_sha256':source_hashes}))


if __name__=='__main__':main()
