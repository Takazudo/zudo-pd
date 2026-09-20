#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11,<3.14"
# dependencies = ["cadquery==2.6.1", "trimesh==4.8.3", "matplotlib==3.10.6", "networkx==3.5"]
# ///
"""Verify the guard against a specific PCB and its populated native STEP export.

Only disposable export copies are modified; the PCB/project remains read-only.
"""
from pathlib import Path
import argparse
import copy
import importlib.util
import json
import math
import os
import uuid
import zipfile
import subprocess
import sys
import tempfile

import cadquery as cq
import trimesh

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
sys.path.insert(0,str(ROOT/'scripts/schgen'))
from sexp import atom,find_all,load
s=importlib.util.spec_from_file_location('guard_generator',HERE/'generate.py')
g=importlib.util.module_from_spec(s);s.loader.exec_module(g)
CLI=Path('/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli')


from contract import field,numbers,require,check_pcb


def serialize(node):
    if isinstance(node,list):return '('+' '.join(serialize(v) for v in node)+')'
    return json.dumps(node[1]) if node[0]=='str' else node[1]


def populated_solids(pcb,tree,project_dir,scratch):
    tree=copy.deepcopy(tree);model_hashes={}
    for fp in find_all(tree,'footprint'):
        for model in list(find_all(fp,'model')):
            name=atom(model[1]).replace('${KIPRJMOD}',str(project_dir))
            path=Path(name)
            if not path.is_absolute():path=project_dir/path
            path=path.resolve()
            # The cover's own board-only presentation model must not collide
            # with itself when this verifier is run after it is attached.
            if HERE in path.parents:fp.remove(model);continue
            require(path.is_file(),'Missing component model: '+str(path))
            companion=path.with_suffix('.step') if path.suffix.lower()=='.wrl' else path
            require(companion.is_file(),'No STEP companion for modeled component: '+str(path))
            model_hashes[str(companion.relative_to(ROOT))]=g.sha(companion)
            model[1]=('str',str(companion))
    temporary=scratch/'guard-check.kicad_pcb';temporary.write_text(serialize(tree)+'\n')
    outputs=[]
    for tag,flags in [('board',['--board-only']),('populated',[])]:
        path=scratch/(tag+'.step')
        result=subprocess.run([str(CLI),'pcb','export','step','--force','--no-dnp','--output',str(path),*flags,str(temporary)],capture_output=True,text=True)
        require(result.returncode==0 and path.is_file(),'Native STEP export failed: '+result.stdout+result.stderr)
        outputs.append(cq.importers.importStep(str(path)).val())
    board,whole=outputs;bb=g.bounds(board)
    stackup=find_all(find_all(tree,'setup')[0],'stackup')
    require(len(stackup)==1,'Explicit stackup required for STEP Z datum')
    layers={atom(l[1]):float(field(l,'thickness')) for l in find_all(stackup[0],'layer') if find_all(l,'thickness')}
    require(abs(sum(layers.values())-1.6)<.001,'Stackup thickness does not sum to1.6mm')
    finish_bottom=layers['B.Cu']+layers['B.Mask'];finish_top=layers['F.Cu']+layers['F.Mask']
    require(abs(bb[5]-bb[2]-(1.6-finish_bottom-finish_top))<.003,'Native core thickness disagrees with stackup')
    shift=-1.6+finish_bottom-bb[2]
    solids=whole.Solids();core=[s for s in solids if all(abs(a-b)<.003 for a,b in zip(g.bounds(s),bb))]
    require(len(core)==1,'Native PCB substrate is not uniquely identifiable')
    parts=[s.translate((0,0,shift)) for s in solids if s not in core]
    return parts,model_hashes,{'native_core_bounds_mm':bb,'world_z_translation_mm':shift,'component_solids':len(parts)},board.translate((0,0,shift))


def main():
    a=argparse.ArgumentParser(description=__doc__);a.add_argument('pcb',type=Path);a.add_argument('--project-dir',type=Path)
    a.add_argument('--output',type=Path,default=HERE/'generated/verification.json');a.add_argument('--geometry-only',action='store_true')
    args=a.parse_args();pcb=args.pcb.resolve();project=(args.project_dir or pcb.parent).resolve()
    c=json.loads((HERE/'pcb-contract.json').read_text());tree=load(pcb)
    result={'verification_script_sha256':g.sha(__file__),'contract_checker_sha256':g.sha(HERE/'contract.py'),'pcb':str(pcb.relative_to(ROOT)) if ROOT in pcb.parents else pcb.name,'pcb_sha256':g.sha(pcb),'contract_sha256':g.sha(HERE/'pcb-contract.json'),
            'placement_and_outline':check_pcb(tree,c)}
    manifest=json.loads((HERE/'generated/manifest.json').read_text())
    require(manifest['source_sha256']['generate.py']==g.sha(HERE/'generate.py') and manifest['source_sha256']['pcb-contract.json']==g.sha(HERE/'pcb-contract.json'),'Regenerate stale guard assets')
    for name,value in manifest['assembly_files'].items():require(g.sha(HERE/'generated'/name)==value,'Assembly file hash differs: '+name)
    for part in manifest['parts']:
        path=HERE/part['file'];require(g.sha(path)==part['sha256'],'Print STL hash differs: '+part['name'])
        m=trimesh.load_mesh(path);require(m.is_watertight and m.volume>0 and len(m.split())==1 and abs(m.bounds[0,2])<1e-5,'Invalid print mesh '+part['name'])
    if args.geometry_only:
        result['populated_model_interference']='SKIPPED by explicit --geometry-only';result['status']='GEOMETRY ONLY'
    else:
        guard,caps=g.make_guard(c,manifest['config']['socket_diameter_mm']);printed=[('guard',guard)]+caps
        with tempfile.TemporaryDirectory(prefix='zudo-pd-guard-check-') as temp:
            solids,hashes,datum,b_core=populated_solids(pcb,tree,project,Path(temp))
            collisions=[];checked=0
            for name,part in printed:
                for i,component in enumerate(solids):
                    if not g.overlaps(part,component):continue
                    volume=part.intersect(component).Volume();checked+=1
                    if volume>.005:collisions.append({'print_part':name,'component_solid_index':i,'intersection_mm3':volume,'component_bounds_mm':g.bounds(component)})
            require(not collisions,'Populated model collisions: '+json.dumps(collisions))
            p_pcb=ROOT/'boards/board-p/board-p.kicad_pcb'
            p_scratch=Path(temp)/'board-p';p_scratch.mkdir()
            p_parts,p_hashes,p_datum,p_core=populated_solids(p_pcb,load(p_pcb),p_pcb.parent,p_scratch)
            def p_to_b(shape):
                return shape.rotate((0,0,0),(0,0,1),90).translate((0,-27,-12.6))
            p_parts=[p_to_b(s) for s in p_parts];p_core=p_to_b(p_core)
            for name,part in printed:
                for i,component in enumerate([p_core,*p_parts]):
                    if not g.overlaps(part,component):continue
                    volume=part.intersect(component).Volume();checked+=1
                    require(volume<=.005,f'{name} intersects stacked P solid{i}: {volume}')
            # Distinguish intended male engagement from interference by
            # unrelated PCB parts. Preserve the initial tall-envelope failure
            # as a diagnostic; require the final segmented envelope to clear.
            native_males={}
            for ref,expected in g.terminal_models(c):
                matches=[i for i,solid in enumerate(solids) if all(abs(x-y)<.1 for x,y in zip(g.bounds(solid),g.bounds(expected))) and abs(solid.Volume()-expected.Volume())<.01]
                require(len(matches)==1,'Cannot identify exact native Faston model '+ref)
                native_males[ref]=matches[0]
            envelope=c['guard']['nominal_mating_envelope'];access=[];initial=[]
            components=[('B',i,s) for i,s in enumerate(solids)]+[('P',i,s) for i,s in enumerate(p_parts)]
            def intrusions(region,ref):
                hits=[]
                for board_name,index,solid in components:
                    if board_name=='B' and index==native_males[ref]:continue
                    if not g.overlaps(region,solid):continue
                    volume=region.intersect(solid).Volume()
                    if volume>.001:hits.append({'board':board_name,'solid_index':index,'intersection_mm3':volume,'bounds_mm':g.bounds(solid)})
                return hits
            for fp in c['fastons']['placements']:
                ref=fp['reference'];y=fp['center_mm'][1];half=envelope['each_row_y_half_mm']
                initial_box=g.box(15,y-4.4,36,y+4.4,-12.1,-2.6)
                initial.append({'reference':ref,'intrusions':intrusions(initial_box,ref)})
                segments=envelope.get('row_overrides',{}).get(ref,[{'x_mm':envelope['x_mm'],'z_mm':envelope['z_mm']}])
                for index,segment in enumerate(segments):
                    region=g.box(segment['x_mm'][0],y-half,segment['x_mm'][1],y+half,*segment['z_mm'])
                    hits=intrusions(region,ref)
                    require(not hits,'Declared access envelope intersects unrelated component: '+json.dumps({'reference':ref,'hits':hits}))
                    for name,part in printed:
                        volume=region.intersect(part).Volume() if g.overlaps(region,part) else 0
                        require(volume<=.001,ref+' access envelope intersects '+name)
                    access.append({'reference':ref,'segment':index+1,'x_mm':segment['x_mm'],'y_mm':[y-half,y+half],'z_mm':segment['z_mm'],'unrelated_model_intrusions':[]})
            female_sweeps=[]
            for fp in c['fastons']['placements']:
                ref=fp['reference'];y=fp['center_mm'][1];half=envelope['each_row_y_half_mm']
                segments=envelope.get('row_overrides',{}).get(ref,[{'x_mm':envelope['x_mm'],'z_mm':envelope['z_mm']}])
                for index,segment in enumerate(segments):
                    swept=g.box(segment['x_mm'][0],y-half,segment['x_mm'][1]+envelope['straight_insertion_distance_mm'],y+half,*segment['z_mm'])
                    require(not intrusions(swept,ref),'Nominal straight female insertion blocked: '+ref)
                    # The separate shutter is installed afterwards. Own male
                    # engagement is excluded; actual receptacle cavity is unknown.
                    for name,part in printed:
                        if name=='j8-exit-shutter':continue
                        volume=swept.intersect(part).Volume() if g.overlaps(swept,part) else 0
                        require(volume<=.001,'Nominal insertion intersects printed '+name)
                    female_sweeps.append({'reference':ref,'segment':index+1,'translation_from_positive_x_mm':envelope['straight_insertion_distance_mm'],'unrelated_model_intrusions':[]})
            sweep=g.shutter(c,sweep=True);sweep_pairs=0
            for board_name,index,solid in components+[('P',-1,p_core),('B',-1,b_core)]:
                if not g.overlaps(sweep,solid):continue
                volume=sweep.intersect(solid).Volume();sweep_pairs+=1
                require(volume<=.001,f'Shutter insertion crosses {board_name} model{index}: {volume}')
            result['mating_access']={'status':'PASS WITH STATED ENVELOPE','female_part_selected':False,'initial_unstepped_envelope':initial,'permitted_segments':access,'nominal_straight_female_insertion':female_sweeps,
                'shutter_insertion':{'status':'PASS','distance_mm':c['guard']['exit_shutter']['insertion_distance_mm'],'direction_pcb':[-1,0],'populated_pairs_checked':sweep_pairs},
                'assembly_order':'Install the guard, mate the terminal while the shutter is removed, then slide shutter from+X. Actual female shape, wire routing and friction require physical checks.'}
            # Keep a review assembly separate from the guard-only model and
            # print meshes. Both real PCB substrates and all exported models
            # appear in their declared world positions.
            assembly=cq.Assembly(name='zudo_pd_guarded_stack_review')
            render_parts=[]
            def add(name,shape,color):
                assembly.add(shape,name=name,color=cq.Color(*color))
                render_parts.append((name,shape,color))
            add('board_b_substrate',b_core,(.10,.38,.20))
            add('board_p_substrate',p_core,(.15,.47,.25))
            for i,part in enumerate(solids):add(f'board_b_component_{i}',part,(.60,.63,.66))
            for i,part in enumerate(p_parts):add(f'board_p_component_{i}',part,(.63,.65,.67))
            add('guard',guard,(.12,.32,.42))
            for name,cap in caps:add(name,cap,(.82,.56,.18))
            preview=HERE/'generated/preview';preview.mkdir(parents=True,exist_ok=True)
            assembly.export(str(preview/'populated-stack.step'));g.clean_step(preview/'populated-stack.step')
            g.render(render_parts,preview/'populated-stack.png','Populated underside stack — nominal CAD fit',elev=-28,azim=-54)
            p_assembly=cq.Assembly(name='zudo_pd_board_p_stacked')
            p_assembly.add(p_core,name='substrate',color=cq.Color(.15,.47,.25))
            for i,part in enumerate(p_parts):p_assembly.add(part,name=f'component_{i}',color=cq.Color(.63,.65,.67))
            p_assembly.export(str(preview/'board-p-stacked.step'));g.clean_step(preview/'board-p-stacked.step')
            preview_tree=copy.deepcopy(tree)
            for fp in find_all(preview_tree,'footprint'):
                for model in find_all(fp,'model'):
                    path=Path(atom(model[1]).replace('${KIPRJMOD}',str(project)))
                    if not path.is_absolute():path=project/path
                    model[1]=('str','${KIPRJMOD}/'+os.path.relpath(path.resolve(),preview))
            mechanical='(footprint "zudo-pd:Mechanical_Preview" (layer "F.Cu") (at 0 0) (uuid "'+str(uuid.uuid5(uuid.NAMESPACE_URL,'zudo-pd/guarded-assembly-preview'))+'") (property "Reference" "MECH_PREVIEW" (at 0 0 0) (layer "F.Fab") (effects (font (size 1 1) (thickness 0.15)) hide)) (property "Value" "COVER_AND_PD_REVIEW_ONLY" (at 0 0 0) (layer "F.Fab") (effects (font (size 1 1) (thickness 0.15)) hide)) (attr board_only exclude_from_pos_files exclude_from_bom) (model "${KIPRJMOD}/../faston-cover.wrl" (offset (xyz 0 0 0)) (scale (xyz 1 1 1)) (rotate (xyz 0 0 0))) (model "${KIPRJMOD}/board-p-stacked.step" (offset (xyz 0 0 0)) (scale (xyz 1 1 1)) (rotate (xyz 0 0 0))))'
            from sexp import parse,tokenize
            preview_tree.append(parse(tokenize(mechanical)))
            preview_path=preview/'guarded-assembly-preview.kicad_pcb';preview_path.write_text(serialize(preview_tree)+'\n')
            # Restore only model filenames and remove the new board-only model
            # footprint: every original geometry/property node must match.
            proof=copy.deepcopy(preview_tree);proof.pop()
            for old_fp,new_fp in zip(find_all(tree,'footprint'),find_all(proof,'footprint')):
                for old_model,new_model in zip(find_all(old_fp,'model'),find_all(new_fp,'model')):new_model[1]=old_model[1]
            require(proof==tree,'Interactive preview changed original board geometry')
            source_project=project/(project.name+'.kicad_pro')
            if source_project.exists():(preview/'guarded-assembly-preview.kicad_pro').write_bytes(source_project.read_bytes())
            result['interactive_preview']={'file':str(preview_path.relative_to(HERE)),'sha256':g.sha(preview_path),'original_pcb_geometry_unchanged':True,'model_only_footprints_added':1,'excluded_from_bom_and_cpl':True,'manufacturing_use':False}
            result.update({'status':'PASS','populated_model_interference':'PASS','solid_pairs_with_overlapping_bounds_checked':checked,'model_sources_sha256':{**hashes,**p_hashes},'step_datum':datum,
                           'board_p':{'pcb_sha256':g.sha(p_pcb),'xy_transform':'(x,y) -> (y,27-x)','top_z_mm':-12.6,'step_datum':p_datum,'guard_interference':'PASS'},
                           'preview_sha256':{name:g.sha(preview/name) for name in ['populated-stack.step','populated-stack.png','board-p-stacked.step','guarded-assembly-preview.kicad_pcb']}})
    result['limits']=['Checks describe nominal CAD geometry. Actual parts, solder, printed dimensions, cap retention, cable fit and powered temperatures remain unmeasured.',
                      'Female receptacle is not selected; the access bay is a stated envelope only.']
    args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(result,indent=2)+'\n')
    if result['status']=='PASS':
        manifest['pcb_instance_check']={'status':'PASS','board_b_sha256':result['pcb_sha256'],'board_p_sha256':result['board_p']['pcb_sha256'],'verification_file':str(args.output.relative_to(HERE)) if HERE in args.output.parents else args.output.name,'verification_sha256':g.sha(args.output)}
        manifest['preview_files_sha256']=result['preview_sha256']
        (HERE/'generated/manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
        with zipfile.ZipFile(HERE/'generated/print-parts.zip','w',zipfile.ZIP_DEFLATED) as archive:
            for part in manifest['parts']:archive.write(HERE/part['file'],Path(part['file']).name)
            for path in [HERE/'pcb-contract.json',HERE/'README.md',HERE/'generated/manifest.json',args.output]:archive.write(path,path.name)
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()
