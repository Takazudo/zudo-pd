#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11,<3.14"
# dependencies = ["cadquery==2.6.1"]
# ///
"""Create a portable review-only B+P assembly without modifying either source PCB.

Native KiCad STEP exports establish PCB Z datums. Board P faces down above Board
B, with P(x,y) mapping to B(y-0.5,x+12). All fitted parts are screened across the boards;
only the six mating contact columns may contain J5/JOUT1 overlap. Conservative
C5 and terminal envelopes supplement the illustrative catalog models.
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
    return bounds_overlap(aa,bb)


def bounds_overlap(aa,bb):
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


class NativeAssembly(cq.Assembly):
    """Retain repeated vendor subassembly names without dropping any instance.

    CadQuery 2.6.1 imports an assembled model under its vendor name instead of the
    KiCad refdes, then rejects a second same-package component. Unique display
    labels fix that importer limitation; placements and solids remain untouched.
    """
    def add(self,arg,**kwargs):
        if isinstance(arg,cq.Assembly):
            name=kwargs.get('name') or arg.name
            if name in self.objects:
                i=2
                while f'{name}__instance_{i}' in self.objects:i+=1
                kwargs['name']=f'{name}__instance_{i}'
        return super().add(arg,**kwargs)


def native_parts(tree,project,scratch,cli):
    work=copy.deepcopy(tree);sources={};expected={}
    for footprint in find_all(work,'footprint'):
        ref=properties(footprint)['Reference']
        attrs=[atom(v) for node in find_all(footprint,'attr') for v in node[1:]]
        fitted='dnp' not in attrs
        for model in find_all(footprint,'model'):
            path=resolve_model(model,project)
            step=path.with_suffix('.step') if path.suffix.lower()=='.wrl' else path
            require(step.is_file(),'Missing STEP companion: '+str(step))
            for source in (path,step):sources[str(source.relative_to(ROOT))]=sha(source)
            model[1]=('str',str(step))
            if fitted:
                require(ref not in expected,'Multiple models per fitted component need explicit grouping')
                require(atom(find_all(footprint,'layer')[0][1])=='F.Cu','Front-stack screen requires all component models on F.Cu')
                at=[float(atom(v)) for v in find_all(footprint,'at')[0][1:]]
                theta=math.radians(at[2] if len(at)>2 else 0)
                offset=[float(atom(v)) for v in find_all(find_all(model,'offset')[0],'xyz')[0][1:]]
                expected[ref]=(at[0]+offset[0]*math.cos(theta)-offset[1]*math.sin(theta),
                               -at[1]+offset[0]*math.sin(theta)+offset[1]*math.cos(theta))
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
    # Preserve native assembly hierarchy: imported STEP models may contain many
    # solids and lose their reference name, but each top-level component keeps
    # its native placement. Match that origin to the exact footprint/model node.
    imported=NativeAssembly.load(str(scratch/'populated.step'));parts={};cores=[];native_solids=[]
    for child in imported.children:
        shape=child.toCompound()
        native_solids.extend(shape.Solids())
        if all(abs(a-b)<.003 for a,b in zip(bounds(shape),bb)):
            cores.append(shape);continue
        origin=child.loc.toTuple()[0]
        matches=[ref for ref,point in expected.items() if math.dist(origin[:2],point)<.001]
        require(len(matches)==1,'Native component cannot be uniquely attributed: '+child.name+' '+str(origin))
        ref=matches[0];require(ref not in parts,'Duplicate native component '+ref)
        parts[ref]=shape.translate((0,0,shift))
    require(len(cores)==1,'Native substrate is not uniquely identifiable')
    require(set(parts)==set(expected),'Native export omitted/added fitted model references')
    # Integrate each solid separately. OpenCascade's compound-level integration
    # gives different numeric results for equivalent nested/flat compounds.
    # The same 270 B solids agree exactly when integrated individually.
    flat_solids=whole.Solids();attributed_volume=sum(part.Volume() for part in native_solids)
    flat_volume=sum(part.Volume() for part in flat_solids)
    require(len(native_solids)==len(flat_solids) and abs(attributed_volume-flat_volume)<.01,
            f'Native hierarchy count/volume differs from flat native solids: {len(native_solids)}/{len(flat_solids)}, {attributed_volume}/{flat_volume}')
    native_boxes=sorted(tuple(round(v,5) for v in bounds(part)) for part in native_solids)
    flat_boxes=sorted(tuple(round(v,5) for v in bounds(part)) for part in flat_solids)
    require(all(max(abs(x-y) for x,y in zip(a,b))<.003 for a,b in zip(native_boxes,flat_boxes)),
            'Native hierarchy solid bounds differ from flat native geometry')
    return core.translate((0,0,shift)),parts,sources,{'native_core_bounds_mm':bb,'world_z_translation_mm':shift,
            'fitted_components':len(parts),'component_solids':sum(len(part.Solids()) for part in parts.values()),
            'hierarchy_geometry_check':{'status':'PASS','solid_count_including_core':len(native_solids),
                                        'sum_individual_volume_mm3':attributed_volume,'flat_sum_individual_volume_mm3':flat_volume,
                                        'every_solid_bounds_match':True},
            'component_bounds_mm':{ref:bounds(shape) for ref,shape in parts.items()}}


def place_board_p(shape,contract):
    stack=contract['pd_stack']
    require(stack['point_transform']=='P(x,y) -> B(y-0.5,x+12)' and stack['cad_rotation_axis']==[1,-1,0]
            and stack['cad_rotation_deg']==180 and stack['nominal_board_p_top_z_mm']==11.1
            and stack['board_b_offset_mm']==[-.5,12],
            'Unreviewed face-to-face stack transform')
    return shape.rotate((0,0,0),(1,-1,0),180).translate((-.5,-12,11.1))


def cross_board_screen(b_core,b_parts,p_core,p_parts,contract):
    policy=contract['pd_stack']['collision_policy'];tolerance=policy['maximum_unintended_intersection_mm3']
    require(tolerance==.005 and policy['allowed_mating_pair']==['board-b/J5','board-p/JOUT1'],
            'Unreviewed collision policy')
    half=policy['mating_contact_xy_half_width_mm'];zmin,zmax=policy['mating_contact_z_interval_mm']
    require(half==.5 and [zmin,zmax]==[2.3,8.7],'Unreviewed contact exclusion envelope')
    columns=[]
    for pad in contract['pd_stack']['pads']:
        x,y=pad['center_mm']
        columns.append(cq.Workplane('XY').box(2*half,2*half,zmax-zmin).translate((x,-y,(zmin+zmax)/2)).val())
    left={'substrate':b_core,**b_parts};right={'substrate':p_core,**p_parts}
    left_bounds={ref:bounds(shape) for ref,shape in left.items()};right_bounds={ref:bounds(shape) for ref,shape in right.items()}
    contacts=[];failures=[];comparisons=0;max_unintended=0
    for br,bshape in left.items():
        for pr,pshape in right.items():
            if not bounds_overlap(left_bounds[br],right_bounds[pr]):continue
            intersection=bshape.intersect(pshape);raw=intersection.Volume();comparisons+=1
            if raw<=tolerance:continue
            unintended=raw
            if (br,pr)==('J5','JOUT1'):
                intersection=intersection.cut(*columns)
                unintended=intersection.Volume()
                contacts.append({'board_b':br,'board_p':pr,'total_intersection_mm3':raw,
                                 'intersection_outside_contact_columns_mm3':unintended})
            max_unintended=max(max_unintended,unintended)
            if unintended>tolerance:
                failures.append({'board_b':br,'board_p':pr,'intersection_mm3':unintended,
                                 'board_b_bounds_mm':left_bounds[br],'board_p_bounds_mm':right_bounds[pr]})
    result={'status':'FAIL' if failures else 'PASS','cross_board_pairs':len(left)*len(right),
            'overlapping_bbox_pairs_checked':comparisons,'maximum_unintended_intersection_mm3':max_unintended,
            'allowed_mating_contact_intersections':contacts,'failures':failures,
            'scope':'Every fitted component and the substrate against every opposite-board fitted component and substrate; own-board interfaces excluded'}
    return result


def support_collar_screen(b_parts,p_core,p_parts,contract):
    """Screen project clearance columns; do not invent a supplier support model."""
    support=contract['corner_supports']
    require(support['assumed_collar_diameter_mm']==6.0,'Unreviewed support collar assumption')
    objects={**{'board-b/'+ref:shape for ref,shape in b_parts.items()},
             **{'board-p/'+ref:shape for ref,shape in p_parts.items()},'board-p/substrate':p_core}
    boxes={ref:bounds(shape) for ref,shape in objects.items()};rows=[]
    for ref,(x,y) in support['placements'].items():
        column=cq.Workplane('XY').circle(3).extrude(16).translate((x,-y,0)).val();bb=bounds(column)
        collisions=[]
        for name,shape in objects.items():
            if not bounds_overlap(bb,boxes[name]):continue
            volume=column.intersect(shape).Volume()
            if volume>.005:collisions.append({'component':name,'intersection_mm3':volume})
        require(not collisions,ref+': project clearance column intersects populated assembly '+str(collisions))
        rows.append({'reference':ref,'center_mm':[x,y],'status':'PASS','assumed_diameter_mm':6,
                     'project_screen_z_interval_mm':[0,16],'collisions':collisions})
    evidence=json.loads((ROOT/support['evidence_path']).read_text())
    return {'status':'PASS','scope':'Project-only diameter6mm clearance columns throughz0..16mm, not actual supplier head/column/base dimensions',
            'corners':rows,'actual_support_fit':'NOT MEASURED','HC11_flat_floor_screen':evidence['flat_floor_screen'],
            'limits':['The supplier drawing does not dimension the complete support XY envelope.',
                      'A clear assumed column does not resolve the11mm HC11/flat-floor height conflict or establish adhesive-base fit.']}


def clean_step(path):path.write_text('\n'.join(line.rstrip() for line in path.read_text().splitlines())+'\n')


def without_models(tree):
    result=copy.deepcopy(tree)
    for footprint in find_all(result,'footprint'):
        for model in list(find_all(footprint,'model')):footprint.remove(model)
    return result


def self_test():
    contract=json.loads((ROOT/'boards/board-b/mechanical.json').read_text())
    def cube(x,y,z,side=.4):return cq.Workplane('XY').box(side,side,side).translate((x,y,z)).val()
    core_b=cube(100,100,0);core_p=cube(100,100,11.1)
    for x,y,z in [(6.55,-37.7,0),(19.25,-37.7,0),(4,-4,0),(23,-4,0),(12.8,-32.6,0),(0,0,1)]:
        point=place_board_p(cq.Vertex.makeVertex(x,y,z),contract).Center()
        require(math.dist((point.x,point.y,point.z),(-y-.5,-x-12,11.1-z))<1e-8,'Face-to-face point transform failed')
    a=cube(37.2,-18.55,6)
    require(cross_board_screen(core_b,{'J5':a},core_p,{'JOUT1':a},contract)['status']=='PASS','Contact allowance rejected')
    cases=[('non-mating component collision',{'C5':a},{'Q1':a}),
           ('connector-body collision outside contact columns',{'J5':cube(34.5,-18.55,6)},{'JOUT1':cube(34.5,-18.55,6)}),
           ('connector collision beyond mating depth',{'J5':cube(37.2,-18.55,10)},{'JOUT1':cube(37.2,-18.55,10)}),
           ('opposite-board component strikes substrate',{'C5':core_p},{})]
    for label,left,right in cases:
        require(cross_board_screen(core_b,left,core_p,right,contract)['status']=='FAIL','Negative control accepted: '+label)
    wrong=copy.deepcopy(contract);wrong['pd_stack']['cad_rotation_axis']=[0,0,1]
    try:place_board_p(a,wrong)
    except ValueError:pass
    else:raise ValueError('Wrong CAD rotation accepted')
    wrong=copy.deepcopy(contract);wrong['pd_stack']['board_b_offset_mm']=[0,0]
    try:place_board_p(a,wrong)
    except ValueError:pass
    else:raise ValueError('Old untranslated P placement accepted')
    support_collar_screen({},core_p,{},contract)
    try:support_collar_screen({'COLLISION':cube(4,-4,5)},core_p,{},contract)
    except ValueError:pass
    else:raise ValueError('Obstacle in the assumed upper-left support column accepted')
    return {'status':'PASS','positive_contact_and_transform_checks':3,'negative_controls':[v[0] for v in cases]+[
            'wrong CAD rotation','old untranslated PD placement','obstacle in assumed corner-support column']}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--board-b',type=Path,default=ROOT/'boards/board-b/board-b.kicad_pcb')
    parser.add_argument('--project-dir',type=Path)
    parser.add_argument('--output',type=Path,default=ROOT/'boards/board-b/assembly-preview')
    parser.add_argument('--kicad-cli',default=shutil.which('kicad-cli'))
    parser.add_argument('--kicad-python',default='/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3')
    parser.add_argument('--self-test',action='store_true')
    args=parser.parse_args()
    if args.self_test:print(json.dumps(self_test(),indent=2));return
    require(args.kicad_cli,'kicad-cli is required')
    b_pcb=args.board_b.resolve();p_pcb=ROOT/'boards/board-p/board-p.kicad_pcb';project=(args.project_dir or b_pcb.parent).resolve()
    output=args.output.resolve();require(not output.exists(),'Choose a new preview output directory; never overwrite an existing review')
    b_tree,p_tree=load(b_pcb),load(p_pcb);source_hashes={'board-b':sha(b_pcb),'board-p':sha(p_pcb)}
    contract_path=ROOT/'boards/board-b/mechanical.json';contract=json.loads(contract_path.read_text())
    contract_hash=sha(contract_path);generator_hash=sha(Path(__file__))
    verification_sources={str(path.relative_to(ROOT)):sha(path) for path in
                          [ROOT/'scripts/pcb/verify-board-b.py',ROOT/'scripts/pcb/verify-compact-mechanics.py',ROOT/'scripts/pcb/board_b_layout.py',
                           ROOT/'scripts/pcb/check-model-bodies.py',
                           ROOT/'boards/board-p/mechanical.json',ROOT/'boards/board-b/supports/hc11-evidence.json',ROOT/'.claude/skills/component-project-passives/facts.json',
                           ROOT/'.claude/skills/component-kangnex-wj500v-5-08-2p-c8465/facts.json']}
    require(contract['terminal_blocks']['maximum_tail_projection_mm']==4.7,'Unreviewed terminal tail envelope')
    output.mkdir(parents=True)
    command([args.kicad_python,ROOT/'scripts/pcb/verify-board-b.py',b_pcb,'--project-dir',project,'--output',output/'mechanical-check.json'])
    for name,pcb,directory in [('board-b',b_pcb,project),('board-p',p_pcb,p_pcb.parent)]:
        command([sys.executable,ROOT/'scripts/pcb/check-model-bodies.py',pcb,'--project-dir',directory,'--output',output/(name+'-model-bodies.json')])
    with tempfile.TemporaryDirectory(prefix='zudo-pd-assembly-') as temporary:
        scratch=Path(temporary);(scratch/'b').mkdir();(scratch/'p').mkdir()
        b_core,b_parts,b_sources,b_datum=native_parts(b_tree,project,scratch/'b',args.kicad_cli)
        p_core,p_parts,p_sources,p_datum=native_parts(p_tree,p_pcb.parent,scratch/'p',args.kicad_cli)
        p_core=place_board_p(p_core,contract);p_parts={ref:place_board_p(part,contract) for ref,part in p_parts.items()}
        collision_screen=cross_board_screen(b_core,b_parts,p_core,p_parts,contract)
        (output/'populated-collision-check.json').write_text(json.dumps(collision_screen,indent=2)+'\n')
        require(collision_screen['status']=='PASS','Populated cross-board collision: '+str(collision_screen['failures']))
        header_spacing=[]
        for spacing in (11.0,11.08,11.1):
            check=cross_board_screen(b_core,{'J5':b_parts['J5']},p_core,
                                     {'JOUT1':p_parts['JOUT1'].translate((0,0,spacing-11.1))},contract)
            header_spacing.append({'nominal_plane_spacing_mm':spacing,'status':check['status'],
                                   'unintended_intersection_mm3':check['maximum_unintended_intersection_mm3'],
                                   'mating_contact_intersections':check['allowed_mating_contact_intersections']})
        terminal_screens=[]
        for item in contract['terminal_blocks']['placements']:
            ref=item['reference'];fx,fy=item['center_mm'];shape=b_parts[ref]
            # Manufacturer maximum 10.36 x 10.4 x 14.2 mm body plus 0.6 mm
            # side interlock at both ends. Local CAD +Y faces the wire entry.
            housing=cq.Workplane('XY').box(11.56,10.4,14.2).translate((0,.5,7.1)).val()
            housing=housing.rotate((0,0,0),(0,0,1),90).translate((fx,-fy,0))
            # A 1 x 1 mm box around each pin exceeds the drawing's maximum
            # 0.95 x 0.85 mm pin section.
            tails=[]
            for lx,ly in contract['terminal_blocks']['pad_centers_local_mm'].values():
                px,py=fx+ly,fy-lx
                tails.append(cq.Workplane('XY').box(1,1,4.7).translate((px,-py,-2.35)).val())
            compared=0;worst=0
            for candidate in [shape,housing,*tails]:
                for part in [p_core,*p_parts.values()]:
                    if not overlaps(candidate,part):continue
                    volume=candidate.intersect(part).Volume();compared+=1;worst=max(worst,volume)
                    require(volume<=.005,f'{ref}: terminal or conservative tail envelope intersects Board P')
            terminal_screens.append({'reference':ref,'status':'PASS','maximum_tail_projection_mm':4.7,'tail_cross_section_envelope_mm':[1,1],
                                     'overlapping_bbox_pairs_checked':compared,'maximum_intersection_mm3':worst,'terminal_world_bounds_mm':bounds(shape),
                                     'conservative_housing_world_bounds_mm':bounds(housing)})
        c5=contract['pd_stack']['c5_envelope']
        require(c5['size_mm']==[11.2,11.2,11.0] and c5['origin_z_mm']==0,'Unreviewed C5 envelope')
        c5fp=next(f for f in find_all(b_tree,'footprint') if properties(f).get('Reference')=='C5')
        cx,cy=[float(atom(v)) for v in find_all(c5fp,'at')[0][1:3]]
        require([cx,cy]==c5['center_mm'],'C5 position differs from the clearance envelope contract')
        envelope=cq.Workplane('XY').box(*c5['size_mm']).translate((cx,-cy,5.5)).val();c5_pairs=[]
        for ref,part in {'substrate':p_core,**p_parts}.items():
            if not overlaps(envelope,part):continue
            volume=envelope.intersect(part).Volume();c5_pairs.append({'board_p':ref,'intersection_mm3':volume})
            require(volume<=.005,'C5 conservative envelope intersects Board P '+ref)
        c5_screen={'status':'PASS','envelope_world_bounds_mm':bounds(envelope),'source_fact_id':c5['source_fact_id'],
                   'maximum_height_mm':11.0,'overlapping_bbox_pairs_checked':c5_pairs}
        support_screen=support_collar_screen(b_parts,p_core,p_parts,contract)
        stacked=cq.Assembly(name='zudo_pd_board_p_stacked')
        stacked.add(p_core,name='substrate',color=cq.Color(.15,.47,.25))
        for ref,part in p_parts.items():stacked.add(part,name=ref,color=cq.Color(.63,.65,.67))
        stacked.export(str(output/'board-p-stacked.step'));clean_step(output/'board-p-stacked.step')
        assembly=cq.Assembly(name='zudo_pd_terminal_stack_review')
        assembly.add(b_core,name='board_b_substrate',color=cq.Color(.10,.38,.20));assembly.add(p_core,name='board_p_substrate',color=cq.Color(.15,.47,.25))
        for tag,parts in [('b',b_parts),('p',p_parts)]:
            for ref,part in parts.items():assembly.add(part,name=f'board_{tag}_{ref}',color=cq.Color(.63,.65,.67))
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
    # Native rendering writes disposable UI preferences; these are not review
    # artifacts and must not bind a release to a user's later viewer settings.
    (output/'preview.kicad_prl').unlink(missing_ok=True)
    require(not list(output.glob('*.lck')),'Preview is still open/locked; close it before freezing review artifacts')
    sources={**b_sources,**p_sources}
    for name,expected in sources.items():require(sha(ROOT/name)==expected,'Component model changed during preview generation')
    require(sha(b_pcb)==source_hashes['board-b'] and sha(p_pcb)==source_hashes['board-p'],'Source PCB changed during preview generation')
    require(sha(contract_path)==contract_hash and sha(Path(__file__))==generator_hash,'Preview generator or mechanical contract changed during generation')
    for name,expected in verification_sources.items():require(sha(ROOT/name)==expected,'Mechanical verifier changed during generation')
    (output/'README.md').write_text('Review-only assembly. Open preview.kicad_pcb in KiCad and use its 3D viewer. Component models are bundled locally; no global model path is needed. This file adds one BOM/CPL-excluded display footprint for Board P and must not be used for fabrication. The source PCBs are unchanged. Nominal CAD fit does not qualify installed hardware, wire/screwdriver access or powered behavior.\n')
    report={'schema_version':1,'status':'PASS','pcb_sha256':source_hashes,'generator_sha256':generator_hash,
            'mechanical_spec_sha256':contract_hash,'model_sources_sha256':sources,'verification_sources_sha256':verification_sources,
            'original_B_nonmodel_geometry_unchanged':True,'model_only_footprints_added':1,'manufacturing_use':False,
            'pd_transform':'P(x,y) -> B(y-0.5,x+12)','board_p_top_z_mm':contract['pd_stack']['nominal_board_p_top_z_mm'],
            'native_step_datums':{'board-b':b_datum,'board-p':p_datum},'terminal_to_pd_clearance':terminal_screens,
            'populated_cross_board_clearance':collision_screen,'c5_envelope_clearance':c5_screen,
            'header_spacing_comparison':header_spacing,
            'project_support_collar_clearance':support_screen,
            'limits':['Catalog model geometry is illustrative; physical fit, board flex and seating tolerances remain unmeasured.',
                      'The 4.7 mm tail and maximum housing/C5 envelopes supplement catalog geometry; they do not establish connector retention or wire access.',
                      'Every fitted P/B component and opposite substrate was screened. Only the identified J5/JOUT1 contact columns allow mating intersection; own-board solder interfaces are outside this cross-board test.',
                      'Support collar columns are project assumptions; actual adhesive foot/head geometry is unavailable. The documented11mm HC11 flat-floor height conflict remains open.',
                      'No electrical or thermal qualification is implied.'],
            'artifact_sha256':{str(path.relative_to(output)):sha(path) for path in sorted(output.rglob('*')) if path.is_file()}}
    (output/'verification.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'status':'PASS','output':str(output),'pcb_sha256':source_hashes}))


if __name__=='__main__':main()
